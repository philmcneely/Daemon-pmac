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

from app import multi_user_import as mu
from app.database import Base, DataEntry, Endpoint, User


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

    loaded = mu._load_json_file(str(file_path))
    assert loaded == data


def test_load_json_file_failure(tmp_path):
    # Point to a non‑existent file
    missing_path = tmp_path / "missing.json"
    with pytest.raises(ValueError) as exc:
        mu._load_json_file(str(missing_path))
    assert "Failed to load JSON file" in str(exc.value)


def test_validate_against_schema_success():
    # Simple schema that requires a string field "name"
    schema = {"name": {"type": "string", "required": True}}
    data = {"name": "Alice"}
    errors = mu._validate_against_schema(data, schema)
    assert errors == []


def test_validate_against_schema_failure():
    schema = {"age": {"type": "integer", "required": True}}
    data = {"age": "not-an-int"}
    errors = mu._validate_against_schema(data, schema)
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

    result = mu.import_user_file(
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
