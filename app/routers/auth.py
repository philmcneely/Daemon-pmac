"""
Module: routers.auth
Description: Authentication routes for user login, registration, token management,
             and session handling

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- fastapi: 0.104.1+ - OAuth2 authentication routing
- python-jose: 3.5.0+ - JWT token operations
- sqlalchemy: 2.0+ - User database operations

Usage:
    # Routes automatically included in main FastAPI app

    # Authentication endpoints:
    # POST /auth/login - User login with credentials
    # POST /auth/register - New user registration
    # POST /auth/refresh - Token refresh
    # GET /auth/me - Current user information

Notes:
    - OAuth2 password flow with JWT tokens
    - Secure password hashing with bcrypt
    - Rate limiting on authentication endpoints
    - Automatic first user becomes admin
    - Session management with token expiration
"""

from datetime import datetime, timedelta
from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import (
    authenticate_user,
    create_access_token,
    get_current_admin_user,
    get_current_user,
    get_password_hash,
)
from ..config import settings
from ..database import User, get_db
from ..schemas import Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["🔐 Authentication & Content Management"])


@router.post("/login", response_model=Token, summary="Login for Content Management")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Login and get JWT access token for content management operations.

    **Content Management Workflow:**
    1. **Login** (this endpoint) → Get JWT token
    2. **List Content**: GET `/api/v1/{endpoint}` (authenticated) → See item IDs
    3. **Create Content**: POST `/api/v1/{endpoint}` → Add new content
    4. **Update Content**: PUT `/api/v1/{endpoint}/{item_id}` → Modify content
    5. **Delete Content**: DELETE `/api/v1/{endpoint}/{item_id}` → Remove content

    **Endpoint Types:**
    - **Public**: `/api/v1/{endpoint}/users/{username}` - Clean view without IDs
    - **Authenticated**: `/api/v1/{endpoint}` - Management view with item IDs

    **Security:**
    - Tokens expire automatically for security
    - Users can only modify their own content (unless admin)
    - All operations are logged in audit trail

    **Example Usage:**
    ```bash
    # Login
    curl -X POST "/auth/login" \
         -d "username=your_username&password=your_password"

    # Use token for content management
    curl -H "Authorization: Bearer <token>" "/api/v1/about"
    ```
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user or not isinstance(user, User):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Update last login timestamp
    from datetime import datetime, timezone

    setattr(user, "last_login", datetime.now(timezone.utc))
    db.commit()

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": cast(str, user.username)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (public registration or admin-only based on config)"""
    from ..database import UserPrivacySettings
    from ..utils import is_single_user_mode

    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter((User.username == user_data.username) | (User.email == user_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)

    # First user is automatically admin in single-user mode
    is_first_user = db.query(User).count() == 0
    is_admin = is_first_user or getattr(user_data, "is_admin", False)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=is_admin,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default privacy settings
    privacy_settings = UserPrivacySettings(
        user_id=new_user.id,
        show_contact_info=True,
        show_location=True,
        show_current_company=True,
        show_salary_range=False,
        show_education_details=True,
        show_personal_projects=True,
        business_card_mode=False,
        ai_assistant_access=True,
        custom_privacy_rules={},
    )
    db.add(privacy_settings)
    db.commit()

    return UserResponse(
        id=cast(int, new_user.id),
        username=cast(str, new_user.username),
        email=cast(str, new_user.email),
        is_active=cast(bool, new_user.is_active),
        is_admin=cast(bool, new_user.is_admin),
        created_at=cast(datetime, new_user.created_at),
    )


@router.post("/users", response_model=UserResponse)
async def create_user_admin(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)"""
    from ..database import UserPrivacySettings

    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter((User.username == user_data.username) | (User.email == user_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=getattr(user_data, "is_admin", False),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default privacy settings
    privacy_settings = UserPrivacySettings(
        user_id=new_user.id,
        show_contact_info=True,
        show_location=True,
        show_current_company=True,
        show_salary_range=False,
        show_education_details=True,
        show_personal_projects=True,
        business_card_mode=False,
        ai_assistant_access=True,
        custom_privacy_rules={},
    )
    db.add(privacy_settings)
    db.commit()

    return UserResponse(
        id=cast(int, new_user.id),
        username=cast(str, new_user.username),
        email=cast(str, new_user.email),
        is_active=cast(bool, new_user.is_active),
        is_admin=cast(bool, new_user.is_admin),
        created_at=cast(datetime, new_user.created_at),
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=cast(int, user.id),
            username=cast(str, user.username),
            email=cast(str, user.email),
            is_active=cast(bool, user.is_active),
            is_admin=cast(bool, user.is_admin),
            created_at=cast(datetime, user.created_at),
        )
        for user in users
    ]


@router.get("/users/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get user by username (admin only)"""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(
        id=cast(int, user.id),
        username=cast(str, user.username),
        email=cast(str, user.email),
        is_active=cast(bool, user.is_active),
        is_admin=cast(bool, user.is_admin),
        created_at=cast(datetime, user.created_at),
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    if not authenticate_user(db, cast(str, current_user.username), old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password"
        )

    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Update password
    setattr(current_user, "hashed_password", get_password_hash(new_password))
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user information"""
    return current_user
