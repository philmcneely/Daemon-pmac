# Adjust import paths for test environment
import sys  # noqa: E402
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

# Adjust import paths for test environment (removed sys.path manipulation)
from app.auth import (  # type: ignore
    _default_revocation_checker,
    add_security_headers,
    check_ip_access,
    generate_api_key,
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
    is_ip_allowed,
    is_token_revoked,
    rate_limit,
    sanitize_input,
    set_token_revocation_checker,
    verify_api_key,
)
from app.config import settings  # type: ignore
from app.schemas import TokenData  # type: ignore


# ---------- Helper mocks ----------
class DummyUser:
    def __init__(
        self,
        username: str,
        hashed_password: str = "hashed",
        is_active=True,
        is_admin=False,
    ):
        self.username = username
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.is_admin = is_admin
        self.last_login = None


class DummySession:  # type: ignore
    """Very small mock of a SQLAlchemy session used for auth tests."""

    def __init__(self, user: DummyUser | None = None, api_key_obj=None):  # type: ignore
        self._user = user
        self._api_key_obj = api_key_obj

    def query(self, model):
        self._model = model
        return self

    def filter(self, *args, **kwargs):  # type: ignore
        return self

    def first(self):
        if self._model.__name__ == "User":
            return self._user
        if self._model.__name__ == "ApiKey":
            return self._api_key_obj
        return None

    def commit(self):
        pass


# ---------- Tests for user retrieval ----------
def test_get_current_user_success(monkeypatch):
    """get_current_user should return the user and set last_login."""
    dummy_user = DummyUser(username="alice")
    dummy_db = DummySession(user=dummy_user)

    # Create a valid token for alice
    token = "dummy-token"
    # Monkeypatch the token verification to return a TokenData with username alice
    monkeypatch.setattr(
        "app.auth.verify_token",
        lambda token_str, exc: TokenData(username="alice"),
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    result_user = get_current_user(credentials=credentials, db=dummy_db)
    assert result_user is dummy_user
    # last_login should be set to a datetime
    assert isinstance(result_user.last_login, datetime)


def test_get_current_user_not_found(monkeypatch):
    """If the user is not found, get_current_user should raise HTTPException."""
    dummy_db = DummySession(user=None)  # type: ignore
    token = "dummy-token"
    monkeypatch.setattr(
        "app.auth.verify_token",
        lambda token_str, exc: TokenData(username="bob"),
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, db=dummy_db)
    assert exc_info.value.status_code == 401


def test_get_current_active_user(monkeypatch):
    """Active user check should pass for active users and fail otherwise."""
    active_user = DummyUser(username="carol", is_active=True)
    inactive_user = DummyUser(username="dave", is_active=False)

    # Active case
    result = get_current_active_user(current_user=active_user)
    assert result is active_user

    # Inactive case
    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(current_user=inactive_user)
    assert exc_info.value.status_code == 400


def test_get_current_admin_user(monkeypatch):
    """Admin user check should pass for admins and fail otherwise."""
    admin_user = DummyUser(username="eve", is_admin=True)
    normal_user = DummyUser(username="frank", is_admin=False)

    # Admin case
    result = get_current_admin_user(current_user=admin_user)
    assert result is admin_user

    # Non‑admin case
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(current_user=normal_user)
    assert exc_info.value.status_code == 403


# ---------- Security headers ----------
def test_add_security_headers():
    class DummyResponse:
        def __init__(self):
            self.headers = {}

    resp = DummyResponse()
    result = add_security_headers(resp)
    # Ensure all expected headers are present
    expected = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'",
    }
    for k, v in expected.items():
        assert result.headers.get(k) == v


# ---------- Rate limiting decorator ----------
@pytest.mark.asyncio
async def test_rate_limit_decorator():
    @rate_limit(max_requests=10, window_seconds=60)
    async def sample_func(x, y=2):
        return x + y

    result = await sample_func(3, y=4)
    assert result == 7


# ---------- Input sanitization ----------
def test_sanitize_input():
    dirty = {
        "safe": "hello",
        "script": "<script>alert('x')</script>",
        "sql": "SELECT * FROM users; DROP TABLE users;",
    }
    cleaned = sanitize_input(dirty)
    # script tags should be removed
    assert cleaned["script"] == "alert('x')"
    # SQL keywords should be stripped (case‑insensitive)
    assert "SELECT" not in cleaned["sql"]
    assert "DROP" not in cleaned["sql"]
    # safe value unchanged
    assert cleaned["safe"] == "hello"


# ---------- IP allow‑list ----------
def test_is_ip_allowed_no_list():
    # When allowed_ips is empty, any IP is allowed
    settings.allowed_ips = []
    assert is_ip_allowed("192.168.1.1") is True


def test_is_ip_allowed_with_cidr(monkeypatch):
    settings.allowed_ips = ["10.0.0.0/8"]
    assert is_ip_allowed("10.5.6.7") is True
    assert is_ip_allowed("192.168.1.1") is False


def test_check_ip_access_allowed(monkeypatch):
    settings.allowed_ips = []  # allow all
    request = Request({"type": "http", "client": ("127.0.0.1", 12345)})
    # Should not raise
    check_ip_access(request)


def test_check_ip_access_denied(monkeypatch):
    settings.allowed_ips = ["10.0.0.0/8"]
    request = Request({"type": "http", "client": ("192.168.1.1", 12345)})
    with pytest.raises(HTTPException) as exc_info:
        check_ip_access(request)
    assert exc_info.value.status_code == 403


# ---------- API key utilities ----------
def test_generate_and_verify_api_key(monkeypatch):
    # Generate a key and its hash
    key, key_hash = generate_api_key()
    assert isinstance(key, str) and isinstance(key_hash, str)

    # Mock a DB session that returns an ApiKey object with matching hash
    class DummyApiKey:
        def __init__(self, key_hash):
            self.key_hash = key_hash
            self.is_active = True
            self.expires_at = None
            self.user = DummyUser(username="api_user")
            self.last_used = None

    dummy_api_key = DummyApiKey(key_hash=key_hash)
    dummy_db = DummySession(api_key_obj=dummy_api_key)

    # Verify should return the associated user
    result_user = verify_api_key(dummy_db, key)
    assert isinstance(result_user, DummyUser)
    assert result_user.username == "api_user"


def test_verify_api_key_invalid(monkeypatch):
    # Use a key that does not exist in DB
    dummy_db = DummySession(api_key_obj=None)
    result = verify_api_key(dummy_db, "nonexistent")
    assert result is None


# ---------- Revocation checker ----------
def test_default_revocation_checker_behavior():
    # Ensure the default checker returns False
    set_token_revocation_checker(_default_revocation_checker)
    assert is_token_revoked("any-token") is False
    # Reset to default for other tests
    set_token_revocation_checker(_default_revocation_checker)
