"""
Authentication routes
"""

from datetime import timedelta
from typing import List

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

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
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

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
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
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        is_admin=new_user.is_admin,
        created_at=new_user.created_at,
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
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        is_admin=new_user.is_admin,
        created_at=new_user.created_at,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
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
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    if not authenticate_user(db, current_user.username, old_password):
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
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user information"""
    return current_user
