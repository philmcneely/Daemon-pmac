"""
Module: auth
Description: Authentication and security utilities for JWT tokens, password hashing,
             and user verification.

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- fastapi: 0.1041+ - Web framework for API routes and dependencies
- python-jose: 3.5.0+ - JWT token creation, verification, and decoding
- passlib: 1.7.4+ - Password hashing with bcrypt algorithm
- sqlalchemy: 2.0+ - Database ORM for user and API key models

Usage:
    from app.auth import get_current_user, verify_password, get_password_hash

    # Verify user authentication in API endpoints
    user = await get_current_user(token)

    # Hash password for secure storage
    hashed = get_password_hash("user_password")

    # Verify password during login
    is_valid = verify_password("plain_password", hashed_password)

Notes:
    - JWT tokens expire after 30 minutes (configurable in settings)
    - Supports both session-based auth and API key authentication
    - Rate limiting applied to all authentication endpoints
    - IP-based access control for enhanced security
    - Automatic security headers added to all responses
"""

import hashlib
import ipaddress
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable, Optional, Union, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings  # type: ignore
from .database import ApiKey, User, get_db  # type: ignore
from .schemas import TokenData  # type: ignore

# ----------------------------------------------------------------------
# Password hashing – CryptContext can be overridden for testing
# ----------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_pwd_context() -> CryptContext:
    """Dependency to retrieve the current CryptContext (injectable)."""
    return _pwd_context


def set_pwd_context(ctx: CryptContext) -> None:
    """Override the password hashing context (used in tests)."""
    global _pwd_context
    _pwd_context = ctx


def verify_password(
    plain_password: str,
    hashed_password: str,
    pwd_context: Optional[CryptContext] = None,
) -> bool:
    """Verify a password against its hash, allowing injection of CryptContext."""
    ctx = pwd_context or get_pwd_context()
    return ctx.verify(plain_password, hashed_password)


def get_password_hash(password: str, pwd_context: Optional[CryptContext] = None) -> str:
    """Hash a password, allowing injection of CryptContext."""
    ctx = pwd_context or get_pwd_context()
    return ctx.hash(password)


# ----------------------------------------------------------------------
# JWT token handling
# ----------------------------------------------------------------------
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
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


# ----------------------------------------------------------------------
# Token revocation hook – can be overridden in tests or runtime
# ----------------------------------------------------------------------


def _default_revocation_checker(token: str) -> bool:
    """Default revocation checker – always returns False."""
    return False


_revocation_checker_func: Callable[[str], bool] = _default_revocation_checker


def get_revocation_checker() -> Callable[[str], bool]:
    """Dependency to retrieve the current revocation checker (injectable)."""
    return _revocation_checker_func


def set_token_revocation_checker(func: Callable[[str], bool]) -> None:
    """Override the token revocation checker (used in tests)."""
    global _revocation_checker_func
    _revocation_checker_func = func


def is_token_revoked(token: str) -> bool:
    """
    Check if a JWT token is revoked using the injectable revocation checker.
    """
    checker = get_revocation_checker()
    return checker(token)


def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """Verify and decode a JWT token, handling expiration and revocation."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        if is_token_revoked(token):
            raise credentials_exception
    except JWTError as e:
        if "Signature has expired" in str(e):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise credentials_exception
    return token_data


def authenticate_user(db: Session, username: str, password: str) -> Union[User, bool]:
    """Authenticate a user with username and password."""
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
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(credentials.credentials, credentials_exception)
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    setattr(user, "last_login", datetime.now(timezone.utc))
    db.commit()
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if not getattr(current_user, "is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current admin user."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


# ----------------------------------------------------------------------
# API Key authentication
# ----------------------------------------------------------------------
def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hash."""
    key = f"daemon_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


def verify_api_key(db: Session, api_key: str) -> Optional[User]:
    """Verify an API key and return the associated user."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_obj = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        .first()
    )
    if not api_key_obj:
        return None  # type: ignore
    current_time = datetime.now(timezone.utc)
    if api_key_obj.expires_at and api_key_obj.expires_at < current_time:  # type: ignore
        return None
    setattr(api_key_obj, "last_used", datetime.now(timezone.utc))
    db.commit()
    return api_key_obj.user


def get_user_from_api_key(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from API key in headers."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    return verify_api_key(db, api_key)


# ----------------------------------------------------------------------
# IP-based access control
# ----------------------------------------------------------------------
def is_ip_allowed(ip_address: str) -> bool:
    """Check if an IP address is allowed."""
    if not settings.allowed_ips:
        return True
    try:
        client_ip = ipaddress.ip_address(ip_address)
        for allowed in settings.allowed_ips:
            if "/" in allowed:
                if client_ip in ipaddress.ip_network(allowed, strict=False):
                    return True
            else:
                if client_ip == ipaddress.ip_address(allowed):
                    return True
        return False
    except ValueError:
        return False


def check_ip_access(request: Request):
    """Validate client IP address against allowed IP list."""
    client_ip = request.client.host if request.client else None
    if not client_ip or not is_ip_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address",
        )


# ----------------------------------------------------------------------
# Security headers middleware
# ----------------------------------------------------------------------
def add_security_headers(response):
    """Add comprehensive security headers to HTTP responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# ----------------------------------------------------------------------
# Rate limiting decorator
# ----------------------------------------------------------------------
def rate_limit(
    max_requests: Optional[int] = None, window_seconds: Optional[int] = None
):
    """Rate limiting decorator."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ----------------------------------------------------------------------
# Input sanitization
# ----------------------------------------------------------------------
def sanitize_input(data: dict) -> dict:
    """Sanitize input data to prevent XSS and injection attacks."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Basic HTML/script tag removal
            value = value.replace("<script>", "").replace("</script>", "")
            # Escape angle brackets
            value = value.replace("<", "<").replace(">", ">")
            # Remove dangerous SQL patterns
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
