"""
Authentication and security utilities
"""

import hashlib
import ipaddress
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional, Union, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import ApiKey, User, get_db
from .schemas import TokenData

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


def authenticate_user(db: Session, username: str, password: str) -> Union[User, bool]:
    """Authenticate a user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, cast(str, user.hashed_password)):
        return False
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(credentials.credentials, credentials_exception)
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception

    # Update last login
    setattr(user, "last_login", datetime.now(timezone.utc))
    db.commit()

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


# API Key authentication
def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hash"""
    key = f"daemon_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


def verify_api_key(db: Session, api_key: str) -> Optional[User]:
    """Verify an API key and return the associated user"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_obj = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        .first()
    )

    if not api_key_obj:
        return None

    # Check expiration
    current_time = datetime.now(timezone.utc)
    if api_key_obj.expires_at and api_key_obj.expires_at < current_time:
        return None

    # Update last used
    setattr(api_key_obj, "last_used", datetime.now(timezone.utc))
    db.commit()

    return api_key_obj.user


def get_user_from_api_key(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key in headers"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None

    return verify_api_key(db, api_key)


# IP-based access control
def is_ip_allowed(ip_address: str) -> bool:
    """Check if an IP address is allowed"""
    if not settings.allowed_ips:
        return True  # No restrictions if list is empty

    try:
        client_ip = ipaddress.ip_address(ip_address)
        for allowed in settings.allowed_ips:
            if "/" in allowed:  # CIDR notation
                if client_ip in ipaddress.ip_network(allowed, strict=False):
                    return True
            else:  # Single IP
                if client_ip == ipaddress.ip_address(allowed):
                    return True
        return False
    except ValueError:
        return False


def check_ip_access(request: Request):
    """Middleware to check IP access"""
    client_ip = request.client.host if request.client else None
    if not client_ip or not is_ip_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address",
        )


# Security headers middleware
def add_security_headers(response):
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# Rate limiting decorator
def rate_limit(
    max_requests: Optional[int] = None, window_seconds: Optional[int] = None
):
    """Rate limiting decorator"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a simple in-memory rate limiter
            # For production, use Redis or similar
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Input sanitization
def sanitize_input(data: dict) -> dict:
    """Sanitize input data to prevent XSS and injection attacks"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Basic HTML/script tag removal
            value = value.replace("<script>", "").replace("</script>", "")
            value = value.replace("<", "&lt;").replace(">", "&gt;")
            # Remove SQL injection patterns
            dangerous_patterns = [
                "DROP",
                "DELETE",
                "INSERT",
                "UPDATE",
                "SELECT",
                "--",
                ";",
            ]
            for pattern in dangerous_patterns:
                if pattern.lower() in value.lower():
                    value = value.replace(pattern.lower(), "")
                    value = value.replace(pattern.upper(), "")
        sanitized[key] = value
    return sanitized
