import pytest

from app.auth import (
    get_password_hash,
    get_revocation_checker,
    is_token_revoked,
    set_token_revocation_checker,
    verify_password,
)


def test_password_hash_and_verify():
    """Ensure that password hashing and verification work correctly."""
    password = "super_secret"
    hashed = get_password_hash(password)
    assert isinstance(hashed, str)
    assert verify_password(password, hashed)
    # Wrong password should fail
    assert not verify_password("wrong_password", hashed)


def test_default_revocation_checker_returns_false():
    """The default revocation checker should always return False."""
    assert not is_token_revoked("any-token")


def test_custom_revocation_checker():
    """Override the revocation checker and verify it is used."""
    # Set a custom checker that always returns True
    set_token_revocation_checker(lambda token: True)
    try:
        assert is_token_revoked("any-token")
        # Ensure the getter returns the same callable
        checker = get_revocation_checker()
        assert callable(checker)
        assert checker("test") is True
    finally:
        # Reset to the default (always False) to avoid side effects on other tests
        set_token_revocation_checker(lambda token: False)
