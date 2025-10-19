from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.auth import (
    _default_revocation_checker,
    create_access_token,
    get_revocation_checker,
    is_token_revoked,
    set_token_revocation_checker,
    verify_token,
)
from app.config import settings
from app.schemas import TokenData


def test_create_and_verify_token():
    """A token created with create_access_token should be verifiable and return the correct username."""
    data = {"sub": "test_user"}
    token = create_access_token(data)
    # Verify without custom exception (should succeed)
    token_data = verify_token(token, HTTPException(status_code=401, detail="Invalid"))
    assert isinstance(token_data, TokenData)
    assert token_data.username == "test_user"


def test_token_expiration_handling():
    """A token with an expiration in the past should raise an HTTPException."""
    data = {"sub": "expired_user"}
    # Create a token that expired 1 second ago
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, HTTPException(status_code=401, detail="Invalid"))
    # The exception should be a 401 Unauthorized
    assert exc_info.value.status_code == 401


def test_revocation_checker_default_behavior():
    """The default revocation checker should always return False."""
    # Ensure the default checker is in place
    set_token_revocation_checker(_default_revocation_checker)
    assert not is_token_revoked("any-token")
    # The getter should return the same callable
    checker = get_revocation_checker()
    assert callable(checker)
    assert checker("any-token") is False


def test_custom_revocation_checker_blocks_token():
    """When a custom revocation checker returns True, verification should fail."""
    # Override the revocation checker to always revoke tokens
    set_token_revocation_checker(lambda token: True)
    try:
        token = create_access_token({"sub": "revoked_user"})
        # Verification should raise the provided credentials exception
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, HTTPException(status_code=401, detail="Invalid"))
        assert exc_info.value.status_code == 401
    finally:
        # Reset to default to avoid side effects on other tests
        set_token_revocation_checker(_default_revocation_checker)
