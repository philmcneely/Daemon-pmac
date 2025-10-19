"""
Unit tests for the refactored ``app.multi_user_import`` module.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, DataEntry, Endpoint, User
from app.multi_user_import import (
    _load_json_file,
    _validate_against_schema,
    create_user_data_directory,
    import_all_users_data,
    import_user_data_from_directory,
    import_user_file,
)


@pytest.fixture(scope="function")
def db_session():
    """Create an isolated in‑memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_load_json_file_success(tmp_path):
    # Create a temporary JSON file
    data = {"key": "value", "num": 123}
    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    loaded = _load_json_file(str(file_path))
    assert loaded == data


def test_load_json_file_failure(tmp_path):
    # Point to a non‑existent file
    missing_path = tmp_path / "missing.json"
    with pytest.raises(ValueError) as exc:
        _load_json_file(str(missing_path))
    assert "Failed to load JSON file" in str(exc.value)


def test_validate_against_schema_success():
    # Simple schema that requires a string field "name"
    schema = {"name": {"type": "string", "required": True}}
    data = {"name": "Alice"}
    errors = _validate_against_schema(data, schema)
    assert errors == []


def test_validate_against_schema_failure():
    schema = {"age": {"type": "integer", "required": True}}
    data = {"age": "not-an-int"}
    errors = _validate_against_schema(data, schema)
    assert any("must be an integer" in e for e in errors)


def test_import_user_file_creates_entry(db_session):
    # Set up a user and endpoint in the DB
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    endpoint = Endpoint(
        name="test_endpoint",
        description="Test endpoint",
        schema={},  # No schema constraints for this test
        is_active=True,
        is_public=True,
        created_by_id=user.id,
    )
    db_session.add(endpoint)
    db_session.commit()

    # Create a temporary JSON file with a simple object
    temp_dir = tempfile.mkdtemp()
    json_path = Path(temp_dir) / "data.json"
    json_path.write_text(json.dumps({"field": "value"}), encoding="utf-8")

    result = import_user_file(
        username="testuser",
        file_path=str(json_path),
        endpoint_name="test_endpoint",
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True
    assert result["entries_created"] == 1

    # Verify that a DataEntry was persisted
    entry = (
        db_session.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id).first()
    )
    assert entry is not None
    assert entry.data == {"field": "value"}
    assert entry.created_by_id == user.id


def test_import_user_file_user_not_found(db_session):
    """Test import_user_file when user doesn't exist."""
    result = import_user_file(
        username="nonexistent",
        file_path="/tmp/test.json",
        endpoint_name="test_endpoint",
        db=db_session,
        replace_existing=False,
    )
    assert result["success"] is False
    assert "not found" in result["error"]


def test_import_user_file_json_load_error(db_session):
    """Test import_user_file with invalid JSON file."""
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    # Create a file with invalid JSON
    temp_dir = tempfile.mkdtemp()
    json_path = Path(temp_dir) / "invalid.json"
    json_path.write_text("{invalid json}", encoding="utf-8")

    result = import_user_file(
        username="testuser",
        file_path=str(json_path),
        endpoint_name="test_endpoint",
        db=db_session,
        replace_existing=False,
    )
    assert result["success"] is False
    assert "Failed to load JSON file" in result["error"]


def test_import_user_file_creates_endpoint(db_session):
    """Test import_user_file creates endpoint if it doesn't exist."""
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    # Create a temporary JSON file
    temp_dir = tempfile.mkdtemp()
    json_path = Path(temp_dir) / "data.json"
    json_path.write_text(json.dumps({"field": "value"}), encoding="utf-8")

    result = import_user_file(
        username="testuser",
        file_path=str(json_path),
        endpoint_name="new_endpoint",
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True
    assert result["entries_created"] == 1

    # Verify endpoint was created
    endpoint = (
        db_session.query(Endpoint).filter(Endpoint.name == "new_endpoint").first()
    )
    assert endpoint is not None
    assert endpoint.created_by_id == user.id


def test_import_user_file_with_array_data(db_session):
    """Test import_user_file with array of objects."""
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    endpoint = Endpoint(
        name="test_endpoint",
        description="Test endpoint",
        schema={},
        is_active=True,
        is_public=True,
        created_by_id=user.id,
    )
    db_session.add(endpoint)
    db_session.commit()

    # Create a temporary JSON file with array data
    temp_dir = tempfile.mkdtemp()
    json_path = Path(temp_dir) / "data.json"
    data_array = [{"field": "value1"}, {"field": "value2"}, {"field": "value3"}]
    json_path.write_text(json.dumps(data_array), encoding="utf-8")

    result = import_user_file(
        username="testuser",
        file_path=str(json_path),
        endpoint_name="test_endpoint",
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True
    assert result["entries_created"] == 3

    # Verify all entries were created
    entries = (
        db_session.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id).all()
    )
    assert len(entries) == 3


def test_import_user_file_replace_existing(db_session):
    """Test import_user_file with replace_existing=True."""
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    endpoint = Endpoint(
        name="test_endpoint",
        description="Test endpoint",
        schema={},
        is_active=True,
        is_public=True,
        created_by_id=user.id,
    )
    db_session.add(endpoint)
    db_session.commit()

    # Create initial data entry
    initial_entry = DataEntry(
        endpoint_id=endpoint.id,
        data={"old": "data"},
        created_by_id=user.id,
        is_active=True,
    )
    db_session.add(initial_entry)
    db_session.commit()

    # Create a temporary JSON file
    temp_dir = tempfile.mkdtemp()
    json_path = Path(temp_dir) / "data.json"
    json_path.write_text(json.dumps({"new": "data"}), encoding="utf-8")

    result = import_user_file(
        username="testuser",
        file_path=str(json_path),
        endpoint_name="test_endpoint",
        db=db_session,
        replace_existing=True,
    )

    assert result["success"] is True
    assert result["entries_created"] == 1

    # Verify old entry was replaced
    entries = (
        db_session.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id).all()
    )
    assert len(entries) == 1
    assert entries[0].data == {"new": "data"}


def test_import_user_data_from_directory_nested_structure(db_session, tmp_path):
    """Test import_user_data_from_directory with nested directory structure."""
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    # Create nested directory structure
    user_dir = tmp_path / "testuser"
    user_dir.mkdir()

    # Create endpoint directories
    resume_dir = user_dir / "resume"
    resume_dir.mkdir()
    skills_dir = user_dir / "skills"
    skills_dir.mkdir()

    # Create JSON files in endpoint directories
    (resume_dir / "resume.json").write_text(
        json.dumps({"name": "Test Resume"}), encoding="utf-8"
    )
    (skills_dir / "skills.json").write_text(
        json.dumps({"skills": ["Python", "SQL"]}), encoding="utf-8"
    )

    result = import_user_data_from_directory(
        username="testuser",
        data_directory=str(user_dir),
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True
    assert result["total_entries"] == 2
    assert len(result["imported_files"]) == 2
    assert len(result["errors"]) == 0


def test_import_user_data_from_directory_flat_structure(db_session, tmp_path):
    """Test import_user_data_from_directory with flat file structure."""
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    # Create user directory
    user_dir = tmp_path / "testuser"
    user_dir.mkdir()

    # Create flat JSON files
    (user_dir / "resume_testuser.json").write_text(
        json.dumps({"name": "Test Resume"}), encoding="utf-8"
    )
    (user_dir / "skills_testuser.json").write_text(
        json.dumps({"skills": ["Python", "SQL"]}), encoding="utf-8"
    )

    result = import_user_data_from_directory(
        username="testuser",
        data_directory=str(user_dir),
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True
    assert result["total_entries"] == 2
    assert len(result["imported_files"]) == 2
    assert len(result["errors"]) == 0


def test_import_user_data_from_directory_user_not_found(db_session, tmp_path):
    """Test import_user_data_from_directory when user doesn't exist."""
    user_dir = tmp_path / "nonexistent"
    user_dir.mkdir()

    result = import_user_data_from_directory(
        username="nonexistent",
        data_directory=str(user_dir),
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is False
    assert "not found" in result["error"]


def test_import_user_data_from_directory_directory_not_found(db_session):
    """Test import_user_data_from_directory when directory doesn't exist."""
    # First create the user in the database
    user = User(username="testuser", email="test@example.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    result = import_user_data_from_directory(
        username="testuser",
        data_directory="/nonexistent/path",
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is False
    assert "directory not found" in result["error"]


def test_import_all_users_data_success(db_session, tmp_path):
    """Test import_all_users_data with multiple users."""
    # Create users
    user1 = User(username="user1", email="user1@example.com", hashed_password="hash")
    user2 = User(username="user2", email="user2@example.com", hashed_password="hash")
    db_session.add_all([user1, user2])
    db_session.commit()

    # Create base directory structure
    base_dir = tmp_path / "private"
    base_dir.mkdir()

    # Create user directories
    user1_dir = base_dir / "user1"
    user1_dir.mkdir()
    user2_dir = base_dir / "user2"
    user2_dir.mkdir()

    # Create data files
    (user1_dir / "resume.json").write_text(
        json.dumps({"name": "User1 Resume"}), encoding="utf-8"
    )
    (user2_dir / "skills.json").write_text(
        json.dumps({"skills": ["Java", "C++"]}), encoding="utf-8"
    )

    result = import_all_users_data(
        base_directory=str(base_dir),
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True
    assert result["total_users"] == 2
    assert result["total_entries"] == 2
    assert len(result["users_processed"]) == 2
    assert len(result["errors"]) == 0


def test_import_all_users_data_missing_user(db_session, tmp_path):
    """Test import_all_users_data when a user doesn't exist in database."""
    # Create base directory
    base_dir = tmp_path / "private"
    base_dir.mkdir()

    # Create user directory for non-existent user
    missing_user_dir = base_dir / "missinguser"
    missing_user_dir.mkdir()

    result = import_all_users_data(
        base_directory=str(base_dir),
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is True  # Overall success despite individual errors
    assert result["total_users"] == 0
    assert len(result["errors"]) == 1
    assert "not found in database" in result["errors"][0]["error"]


def test_import_all_users_data_base_directory_not_found(db_session):
    """Test import_all_users_data when base directory doesn't exist."""
    result = import_all_users_data(
        base_directory="/nonexistent/path",
        db=db_session,
        replace_existing=False,
    )

    assert result["success"] is False
    assert "directory not found" in result["error"]


def test_create_user_data_directory(tmp_path, monkeypatch):
    """Test create_user_data_directory creates directory structure."""
    # Create examples directory with sample files
    examples_dir = tmp_path / "data" / "examples"
    examples_dir.mkdir(parents=True)

    (examples_dir / "resume_example.json").write_text(
        json.dumps({"name": "Example User", "title": "Developer"}), encoding="utf-8"
    )
    (examples_dir / "skills_example.json").write_text(
        json.dumps({"skills": ["Example Skill"]}), encoding="utf-8"
    )

    # Create base directory
    base_dir = tmp_path / "data" / "private"
    base_dir.mkdir(parents=True)

    # Change to the test directory so the relative path works
    original_cwd = os.getcwd()
    os.chdir(str(tmp_path))

    try:
        user_dir = create_user_data_directory(
            username="newuser",
            base_directory=str(base_dir),
        )

        assert os.path.exists(user_dir)
        assert os.path.isdir(user_dir)

        # Check that user-specific files were created
        expected_files = ["resume_newuser.json", "skills_newuser.json"]

        for filename in expected_files:
            file_path = os.path.join(user_dir, filename)
            assert os.path.exists(file_path)

            # Verify file content was customized
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "name" in data:
                    assert data["name"] == "Newuser"  # Title case
    finally:
        os.chdir(original_cwd)


def test_create_user_data_directory_no_examples(tmp_path):
    """Test create_user_data_directory when examples directory doesn't exist."""
    base_dir = tmp_path / "private"
    base_dir.mkdir()

    user_dir = create_user_data_directory(
        username="newuser",
        base_directory=str(base_dir),
    )

    assert os.path.exists(user_dir)
    assert os.path.isdir(user_dir)
    # Directory should be created even without examples
