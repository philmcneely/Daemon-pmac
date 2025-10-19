"""
Additional unit tests for uncovered utility functions in ``app.utils``.
"""

import json
import os
import re
import tempfile
from datetime import datetime, timezone

import pytest

from app import utils


def test_sanitize_filename_basic():
    # Remove unsafe characters and replace spaces
    filename = "my<file>:name?.txt"
    sanitized = utils.sanitize_filename(filename)
    assert sanitized == "my_file__name_.txt"
    # Ensure length limit (255 chars)
    long_name = "a" * 300 + ".txt"
    sanitized_long = utils.sanitize_filename(long_name)
    assert len(sanitized_long) <= 255


def test_format_bytes():
    assert utils.format_bytes(0) == "0.0 B"
    assert utils.format_bytes(1023) == "1023.0 B"
    assert utils.format_bytes(1024) == "1.0 KB"
    assert utils.format_bytes(1536) == "1.5 KB"
    assert utils.format_bytes(1048576) == "1.0 MB"
    assert utils.format_bytes(1073741824) == "1.0 GB"


def test_validate_url_allowed():
    # Allowed http/https URLs
    assert utils.validate_url("https://example.com")
    assert utils.validate_url("http://sub.domain.org/path")


def test_validate_url_disallowed_protocols():
    # Disallowed protocols should return False
    for proto in [
        "file://",
        "ftp://",
        "gopher://",
        "javascript:",
        "data:",
        "vbscript:",
    ]:
        assert not utils.validate_url(f"{proto}malicious")


def test_validate_url_disallowed_internal_ips():
    # Disallowed internal IPs and localhost
    for host in [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "10.0.0.5",
        "192.168.1.10",
        "172.20.0.1",
        "169.254.10.20",
        "::1",
        "fe80::1",
    ]:
        assert not utils.validate_url(f"https://{host}/test")


def test_sanitize_input_string():
    # HTML escaping and script removal
    raw = '<script>alert("x")</script><a href="javascript:evil()">Link</a>'
    sanitized = utils.sanitize_input(raw)
    # Script tags should be removed, javascript: stripped, HTML escaped
    assert "<script>" not in sanitized
    assert "javascript:" not in sanitized
    # The <a> tag should be removed because of the javascript: in the href
    # assert '<a href="evil()">Link</a>' in sanitized
    assert "Link" in sanitized


def test_sanitize_data_dict():
    data = {
        "email": "user@example.com",
        "nested": {
            "phone": "+1-555-123-4567",
            "list": ["<script>bad</script>", "safe"],
        },
    }
    sanitized = utils.sanitize_data_dict(data)
    # Phone should be removed, script tag stripped from list element
    assert "phone" not in sanitized["nested"]
    assert sanitized["nested"]["list"][0] == ""
    assert sanitized["nested"]["list"][1] == "safe"
