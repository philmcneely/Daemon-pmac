"""
Test suite for the privacy filtering utilities in ``app/privacy.py``.
"""

from typing import Any, Dict

import pytest

# Import the factory function and the filter class
from app.privacy import PrivacyFilter, get_privacy_filter


class DummySession:
    """A minimal mock of a SQLAlchemy Session that returns ``None`` for all queries."""

    def query(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None

    def all(self):
        return []


@pytest.fixture
def dummy_db():
    """Provide a dummy DB session that does not hit the real database."""
    return DummySession()


@pytest.fixture
def sample_data():
    """Sample user data containing a variety of fields for filtering."""
    return {
        "name": "John Doe",
        "title": "Senior Engineer",
        "contact": {
            "email": "john.doe@example.com",
            "personal_email": "john.private@example.com",
            "phone": "+1-555-123-4567",
            "website": "https://johndoe.dev",
            "linkedin": "john-doe",
        },
        "experience": [
            {
                "company": "Acme Corp",
                "position": "Lead Engineer",
                "start_date": "2020-01-01",
                "end_date": None,
                "salary": "150000",
            }
        ],
        "skills": {
            "technical": ["Python", "FastAPI", "SQLAlchemy", "Docker", "Kubernetes"]
        },
        "education": [{"institution": "University X", "degree": "B.Sc.", "gpa": "3.9"}],
        "personal": {"ssn": "123-45-6789", "address": "123 Main St"},
    }


def test_business_card_view(dummy_db, sample_data):
    """Business‑card view should contain only a minimal public subset."""
    privacy = get_privacy_filter(dummy_db)
    result = privacy.filter_data(sample_data, privacy_level="business_card")

    # Expected top‑level keys
    assert set(result.keys()) == {
        "name",
        "title",
        "company",
        "position",
        "contact",
        "skills",
    }

    # Contact should only contain allowed fields
    assert set(result["contact"].keys()) == {"email", "website", "linkedin"}

    # Skills should be limited to the first five technical entries
    assert result["skills"]["technical"] == [
        "Python",
        "FastAPI",
        "SQLAlchemy",
        "Docker",
        "Kubernetes",
    ]


def test_ai_safe_filter_removes_sensitive_fields(dummy_db, sample_data):
    """AI‑safe filter must strip any personally identifiable information."""
    privacy = get_privacy_filter(dummy_db)
    result = privacy.filter_data(sample_data, privacy_level="ai_safe")

    # Sensitive top‑level fields should be removed
    for field in ("personal", "contact"):
        assert field not in result

    # Ensure no phone numbers or SSN appear anywhere in the filtered data
    def contains_sensitive(value: Any) -> bool:
        if isinstance(value, dict):
            return any(contains_sensitive(v) for v in value.values())
        if isinstance(value, list):
            return any(contains_sensitive(v) for v in value)
        if isinstance(value, str):
            return any(s in value.lower() for s in ["ssn", "phone", "address"])
        return False

    assert not contains_sensitive(result)


def test_public_filter_without_user_settings(dummy_db, sample_data):
    """Public filter (default) should remove obvious sensitive patterns."""
    privacy = get_privacy_filter(dummy_db)
    result = privacy.filter_data(sample_data, privacy_level="public_full")

    # Email should be kept (non‑personal) but personal_email should be removed
    assert "email" in result["contact"]
    assert "personal_email" not in result["contact"]

    # SSN and address should be stripped from the data
    assert "personal" not in result
    assert "address" not in result.get("education", [{}])[0]

    # Salary information inside experience should be removed
    assert "salary" not in result["experience"][0]


def test_filter_without_privacy_level_returns_public_full(dummy_db, sample_data):
    """When no privacy level is supplied, the filter defaults to public view."""
    privacy = get_privacy_filter(dummy_db)
    result = privacy.filter_data(sample_data)  # default level

    # Should behave like public_full
    assert "personal" not in result
    assert "salary" not in result["experience"][0]
