"""
Test configuration and fixtures
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_testing_only")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

from app.auth import get_password_hash
from app.database import Base, User, create_default_endpoints, get_db
from app.main import app

# ===== E2E Test Fixtures (Shared SQLite Database) =====


@pytest.fixture(scope="session")
def e2e_db():
    """Create a shared SQLite database for E2E tests (session-scoped)"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Create test database
    engine = create_engine(f"sqlite:///{db_path}")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create default endpoints
    db = TestingSessionLocal()
    create_default_endpoints(db)
    db.close()

    yield db_path, TestingSessionLocal

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def temp_db(e2e_db):
    """Legacy fixture for E2E tests - points to shared database"""
    return e2e_db


# ===== Unit Test Fixtures (In-Memory Database) =====


@pytest.fixture
def unit_db():
    """Create an in-memory database for unit tests"""
    # Use in-memory SQLite database with thread-safe configuration
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create default endpoints
    db = TestingSessionLocal()
    create_default_endpoints(db)
    db.close()

    yield TestingSessionLocal


@pytest.fixture
def unit_db_session(unit_db):
    """Get a unit test database session (in-memory)"""
    TestingSessionLocal = unit_db
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def unit_client(unit_db):
    """Create a test client with in-memory database for unit tests"""
    TestingSessionLocal = unit_db

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ===== Legacy E2E Fixtures =====


@pytest.fixture
def test_db_session(temp_db):
    """Get a test database session"""
    db_path, TestingSessionLocal = temp_db
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(temp_db):
    """Create a test client with temporary database"""
    db_path, TestingSessionLocal = temp_db

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ===== Database Cleanup Fixtures =====


@pytest.fixture(autouse=True)
def clean_e2e_database(request):
    """Clean the E2E database before each test if using E2E fixtures"""
    # Only clean if this test is using E2E fixtures
    if any(
        fixture in request.fixturenames
        for fixture in ["client", "test_db_session", "admin_user", "regular_user"]
    ):
        # Get the shared database path
        db_path = os.environ.get("DATABASE_URL", "sqlite:///test.db").replace(
            "sqlite:///", ""
        )
        if os.path.exists(db_path):
            engine = create_engine(f"sqlite:///{db_path}")
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            try:
                # Use SQLAlchemy models for safer deletion
                from app.database import (
                    ApiKey,
                    AuditLog,
                    DataEntry,
                    DataPrivacyRule,
                    User,
                    UserPrivacySettings,
                )

                # Delete in correct order (respecting foreign keys)
                session.query(UserPrivacySettings).delete()
                session.query(DataPrivacyRule).delete()
                session.query(AuditLog).delete()
                session.query(DataEntry).delete()
                session.query(ApiKey).delete()
                session.query(User).delete()
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()


@pytest.fixture(autouse=True)
def clean_unit_database(request, unit_db):
    """Clean the unit test database before each test if using unit fixtures"""
    # Only clean if this test is using unit fixtures
    if any(
        fixture in request.fixturenames
        for fixture in [
            "unit_client",
            "unit_db_session",
            "unit_admin_user",
            "unit_regular_user",
        ]
    ):
        TestingSessionLocal = unit_db
        session = TestingSessionLocal()
        try:
            # Use SQLAlchemy models for safer deletion
            from app.database import (
                ApiKey,
                AuditLog,
                DataEntry,
                DataPrivacyRule,
                User,
                UserPrivacySettings,
            )

            # Delete in correct order (respecting foreign keys)
            session.query(UserPrivacySettings).delete()
            session.query(DataPrivacyRule).delete()
            session.query(AuditLog).delete()
            session.query(DataEntry).delete()
            session.query(ApiKey).delete()
            session.query(User).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


# ===== User Fixtures (Work with both E2E and Unit tests) =====


@pytest.fixture
def admin_user(test_db_session):
    """Create an admin user for testing (E2E)"""
    # Check if admin user already exists
    existing_user = test_db_session.query(User).filter_by(username="admin").first()
    if existing_user:
        return existing_user

    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_admin=True,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(test_db_session):
    """Create a regular user for testing (E2E)"""
    # Check if regular user already exists
    existing_user = test_db_session.query(User).filter_by(username="user").first()
    if existing_user:
        return existing_user

    user = User(
        username="user",
        email="user@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_admin=False,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def unit_admin_user(unit_db_session):
    """Create an admin user for unit testing"""
    # Check if admin user already exists
    existing_user = unit_db_session.query(User).filter_by(username="admin").first()
    if existing_user:
        return existing_user

    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_admin=True,
    )
    unit_db_session.add(user)
    unit_db_session.commit()
    unit_db_session.refresh(user)
    return user


@pytest.fixture
def unit_regular_user(unit_db_session):
    """Create a regular user for unit testing"""
    # Check if regular user already exists
    existing_user = unit_db_session.query(User).filter_by(username="user").first()
    if existing_user:
        return existing_user

    user = User(
        username="user",
        email="user@test.com",
        hashed_password=get_password_hash("testpassword"),
        is_admin=False,
    )
    unit_db_session.add(user)
    unit_db_session.commit()
    unit_db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, admin_user):
    """Get authentication headers for admin user (E2E)"""
    response = client.post(
        "/auth/login", data={"username": "admin", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_user_headers(client, regular_user):
    """Get authentication headers for regular user (E2E)"""
    response = client.post(
        "/auth/login", data={"username": "user", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unit_auth_headers(unit_client, unit_admin_user):
    """Get authentication headers for admin user (Unit)"""
    response = unit_client.post(
        "/auth/login", data={"username": "admin", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unit_regular_user_headers(unit_client, unit_regular_user):
    """Get authentication headers for regular user (Unit)"""
    response = unit_client.post(
        "/auth/login", data={"username": "user", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_idea_data():
    """Sample data for ideas endpoint"""
    return {
        "title": "Test Idea",
        "description": "This is a test idea",
        "category": "technology",
        "status": "draft",
        "tags": ["test", "api"],
    }


@pytest.fixture
def sample_book_data():
    """Sample data for books endpoint"""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890",
        "rating": 5,
        "review": "Great book!",
        "genres": ["fiction", "mystery"],
    }


@pytest.fixture
def sample_resume_data():
    """Sample data for resume endpoint"""
    return {
        "name": "John Doe",
        "title": "Senior Software Engineer",
        "summary": "Experienced software engineer with expertise in Python and web development.",
        "contact": {
            "email": "john.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "location": "San Francisco, CA",
            "website": "https://johndoe.dev",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
        },
        "experience": [
            {
                "company": "Tech Corp",
                "position": "Senior Software Engineer",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": "Lead development of web applications",
                "achievements": [
                    "Improved system performance by 40%",
                    "Led team of 5 developers",
                ],
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
            }
        ],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "start_date": "2014",
                "end_date": "2018",
                "gpa": 3.8,
                "honors": ["Magna Cum Laude", "Dean's List"],
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "Docker", "AWS"],
            "languages": ["English (Native)", "Spanish (Conversational)"],
            "certifications": ["AWS Solutions Architect"],
            "soft_skills": ["Leadership", "Communication", "Problem Solving"],
        },
        "projects": [
            {
                "name": "Personal API Framework",
                "description": "Built a scalable personal API using FastAPI",
                "technologies": ["Python", "FastAPI", "SQLite"],
                "url": "https://api.johndoe.dev",
                "github": "https://github.com/johndoe/personal-api",
            }
        ],
        "awards": ["Employee of the Year 2022", "Innovation Award 2021"],
        "volunteer": [
            "Coding mentor at local coding bootcamp",
            "Open source contributor",
        ],
        "updated_at": "2024-01-15",
    }
