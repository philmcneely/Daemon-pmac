"""
Module: database
Description: SQLAlchemy database models, configuration, and session management
             for the Daemon personal API framework

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- sqlalchemy: 2.0+ - Database ORM and query builder
- aiosqlite: 0.19.0+ - Async SQLite database driver

Usage:
    from app.database import get_db, User, DynamicEndpoint

    # Use dependency injection in FastAPI routes
    @router.get("/users")
    async def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()

    # Create new database entries
    new_user = User(username="pmac", email="pmac@example.com")
    db.add(new_user)
    db.commit()

Notes:
    - Uses SQLite by default with async support via aiosqlite
    - All models inherit from DeclarativeBase for SQLAlchemy 2.0 compatibility
    - Automatic database initialization on first startup
    - Comprehensive audit logging for all data changes
    - Privacy settings and dynamic endpoint support built-in
"""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy.sql import func

from .config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


# Create engine with SQLite optimizations
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False, "timeout": 20, "isolation_level": None},
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)  # Display name for portfolio
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationship to data entries
    data_entries = relationship("DataEntry", back_populates="created_by")
    privacy_settings = relationship(
        "UserPrivacySettings", back_populates="user", uselist=False
    )
    privacy_settings = relationship(
        "UserPrivacySettings", back_populates="user", uselist=False
    )


class Endpoint(Base):
    """Dynamic endpoint configuration"""

    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    schema = Column(JSON, nullable=False)  # JSON schema for validation
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    data_entries = relationship("DataEntry", back_populates="endpoint")
    created_by = relationship("User")


class DataEntry(Base):
    """Generic data storage for all endpoints"""

    __tablename__ = "data_entries"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False)
    data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    endpoint = relationship("Endpoint", back_populates="data_entries")
    created_by = relationship("User", back_populates="data_entries")

    # Indexes for performance
    __table_args__ = (
        Index("ix_data_entries_endpoint_active", "endpoint_id", "is_active"),
        Index("ix_data_entries_created_at", "created_at"),
    )


class ApiKey(Base):
    """API key management for external access"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(128), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User")


class AuditLog(Base):
    """Audit log for tracking changes"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user = relationship("User")

    # Index for performance
    __table_args__ = (
        Index("ix_audit_logs_table_record", "table_name", "record_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )


class DataPrivacyRule(Base):
    """Privacy rules for data filtering"""

    __tablename__ = "data_privacy_rules"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_name = Column(String(100), nullable=False)
    field_path = Column(String(200), nullable=False)  # e.g., "contact.phone"
    # public, private, sensitive
    privacy_level = Column(String(20), default="private")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPrivacySettings(Base):
    """User-controlled privacy settings"""

    __tablename__ = "user_privacy_settings"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    show_contact_info = Column(Boolean, default=True)
    show_location = Column(Boolean, default=True)
    show_current_company = Column(Boolean, default=True)
    show_salary_range = Column(Boolean, default=False)
    show_education_details = Column(Boolean, default=True)
    show_personal_projects = Column(Boolean, default=True)
    # Ultra-minimal public view
    business_card_mode = Column(Boolean, default=False)
    # Allow AI assistants to access
    ai_assistant_access = Column(Boolean, default=True)
    custom_privacy_rules = Column(JSON, default={})  # User-defined field rules
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="privacy_settings")


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and schema.

    Creates all database tables defined in SQLAlchemy models using the
    configured database engine. This should be called once during
    application startup to ensure database schema exists.

    Note:
        - Uses Base.metadata.create_all() to create tables
        - Safe to call multiple times (won't recreate existing tables)
        - Should be called before any database operations
    """
    Base.metadata.create_all(bind=engine)


def create_default_endpoints(db: Session):
    """Create standard endpoint definitions in database.

    Initializes the database with default endpoint configurations including
    resume, about, ideas, skills, and other core endpoints. Each endpoint
    includes name, description, and JSON schema for data validation.

    Args:
        db (Session): SQLAlchemy database session for endpoint creation.

    Note:
        - Only creates endpoints that don't already exist
        - Each endpoint includes comprehensive JSON schema definitions
        - Covers all standard personal API endpoints
        - Safe to call multiple times (checks for existing endpoints)
    """
    default_endpoints = [
        {
            "name": "resume",
            "description": "Professional resume and work history",
            "schema": {
                "name": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "summary": {"type": "string"},
                "contact": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "location": {"type": "string"},
                        "website": {"type": "string"},
                        "linkedin": {"type": "string"},
                        "github": {"type": "string"},
                    },
                },
                "experience": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string", "required": True},
                            "position": {"type": "string", "required": True},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "description": {"type": "string"},
                            "achievements": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "education": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "institution": {"type": "string", "required": True},
                            "degree": {"type": "string"},
                            "field": {"type": "string"},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "gpa": {"type": "number"},
                            "honors": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "skills": {
                    "type": "object",
                    "properties": {
                        "technical": {"type": "array", "items": {"type": "string"}},
                        "languages": {"type": "array", "items": {"type": "string"}},
                        "certifications": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "soft_skills": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "required": True},
                            "description": {"type": "string"},
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "url": {"type": "string"},
                            "github": {"type": "string"},
                        },
                    },
                },
                "awards": {"type": "array", "items": {"type": "string"}},
                "volunteer": {"type": "array", "items": {"type": "string"}},
                "updated_at": {"type": "string", "format": "date"},
            },
        },
        {
            "name": "about",
            "description": "Basic information about the person or entity",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "ideas",
            "description": "Ideas, thoughts, and concepts",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "skills",
            "description": "Skills and areas of expertise",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "favorite_books",
            "description": "Favorite books and reading recommendations",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "problems",
            "description": "Problems being worked on or solved",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "hobbies",
            "description": "Hobbies and personal interests",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "projects",
            "description": "Personal and professional projects with markdown support",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "looking_for",
            "description": "Things currently looking for or seeking",
            "schema": {
                "content": {"type": "string", "required": True},  # Markdown content
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        # New flexible markdown endpoints
        {
            "name": "skills_matrix",
            "description": "Skills matrix with endorsements and skill-grid commentary",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "personal_story",
            "description": "Personal narrative, biography, or personal story",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "goals",
            "description": "Personal or professional goals with status and notes",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "values",
            "description": "Core values and guiding principles",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "recommendations",
            "description": "Recommendations for tools, books, people, or processes",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "learning",
            "description": "Current learning topics, courses, notes, and study plans",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "quotes",
            "description": "Favorite quotes or mottos with context/explanations",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "contact_info",
            "description": "Public-safe contact information",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "unlisted",
                        },
                    },
                },
            },
        },
        {
            "name": "events",
            "description": "Public events, appearances, or past events",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "achievements",
            "description": "Notable accomplishments",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "contacts",
            "description": "Directory of people with public-safe bios",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "private",
                        },
                    },
                },
            },
        },
        {
            "name": "arguments",
            "description": "Argument maps, structured debate notes, or position pieces",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "claims",
            "description": "Individual claims or beliefs with supporting evidence",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "data_sources",
            "description": "Notes and links to trusted data sources",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "experiments",
            "description": "Experiments with hypothesis, method, and results",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "frames",
            "description": "Cognitive frames or context pieces for viewing topics",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "funding_sources",
            "description": "Notes about funding sources and revenue streams",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "private",
                        },
                    },
                },
            },
        },
        {
            "name": "organizations",
            "description": "Organizations affiliated with, past employers, etc.",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "outcomes",
            "description": "Measured outcomes and observed impacts",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "people",
            "description": "Profiles of people with public-friendly bios",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "private",
                        },
                    },
                },
            },
        },
        {
            "name": "results",
            "description": "Raw or summarized results from experiments or projects",
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "risks",
            "description": (
                "Personal and professional risks with analysis and "
                "mitigation strategies"
            ),
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "private",
                        },
                    },
                },
            },
        },
        {
            "name": "solutions",
            "description": (
                "Solutions and approaches to problems, both personal and "
                "broader challenges"
            ),
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "public",
                        },
                    },
                },
            },
        },
        {
            "name": "threats",
            "description": (
                "External threats and security concerns with impact assessment"
            ),
            "schema": {
                "content": {"type": "string", "required": True},
                "meta": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "date": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "unlisted", "private"],
                            "default": "private",
                        },
                    },
                },
            },
        },
    ]

    for endpoint_data in default_endpoints:
        # Check if endpoint already exists
        existing = (
            db.query(Endpoint).filter(Endpoint.name == endpoint_data["name"]).first()
        )
        if not existing:
            endpoint = Endpoint(**endpoint_data)
            db.add(endpoint)

    db.commit()
