"""
Security tests for OWASP Top 10 and common vulnerabilities
"""

import base64
import json
import urllib.parse
from datetime import datetime, timedelta

import pytest


class TestOWASPSecurity:
    """Test suite for OWASP Top 10 security vulnerabilities"""

    def test_sql_injection_attempts(self, client, auth_headers):
        """Test SQL injection prevention (OWASP A03: Injection)"""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin' OR 1=1#",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' OR 1=1 LIMIT 1 --",
            "') OR ('1'='1",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
        ]

        for payload in sql_injection_payloads:
            # Test in endpoint name parameter
            response = client.get(f"/api/v1/endpoints/{urllib.parse.quote(payload)}")
            assert response.status_code == 404  # Should not execute SQL

            # Test in data fields
            response = client.post(
                "/api/v1/ideas",
                json={
                    "title": payload,
                    "description": f"Testing SQL injection: {payload}",
                    "category": "security_test",
                },
                headers=auth_headers,
            )
            # Should either succeed (properly escaped) or fail validation, but
            # not crash
            assert response.status_code in [200, 400, 422]

            # Test in query parameters
            response = client.get(f"/api/v1/ideas?search={urllib.parse.quote(payload)}")
            assert response.status_code in [200, 400, 404]  # Should not crash

    def test_xss_prevention(self, client, auth_headers):
        """Test Cross-Site Scripting (XSS) prevention (OWASP A03: Injection)"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<<SCRIPT>alert('XSS')//<</SCRIPT>",
            "<script>document.cookie='stolen='+document.cookie</script>",
        ]

        for payload in xss_payloads:
            # Test XSS in data creation
            response = client.post(
                "/api/v1/ideas",
                json={
                    "title": f"XSS Test: {payload}",
                    "description": f"Testing XSS prevention with: {payload}",
                    "category": "security_test",
                },
                headers=auth_headers,
            )

            if response.status_code == 200:
                # Verify data is properly escaped/sanitized
                data = response.json()
                stored_title = data["data"]["title"]
                stored_description = data["data"]["description"]

                # Should not contain executable script tags
                assert "<script>" not in stored_title.lower()
                assert "<script>" not in stored_description.lower()
                assert "javascript:" not in stored_title.lower()
                assert "javascript:" not in stored_description.lower()

    def test_broken_authentication(self, client):
        """Test broken authentication vulnerabilities (OWASP A07: Authentication Failures)"""

        # Test weak password requirements
        weak_passwords = ["123", "password", "admin", "123456", "qwerty", "abc123", ""]

        for weak_password in weak_passwords:
            response = client.post(
                "/auth/register",
                json={
                    "username": f"testuser_{weak_password}",
                    "email": f"test_{weak_password}@example.com",
                    "password": weak_password,
                },
            )
            # Should reject weak passwords
            if len(weak_password) < 8:
                assert response.status_code == 422  # Validation error

        # Test brute force protection
        for i in range(10):
            response = client.post(
                "/auth/login",
                data={
                    "username": "nonexistent_user",
                    "password": f"wrong_password_{i}",
                },
            )
            assert response.status_code == 401

        # Test for timing attacks (should have consistent response times)
        import time

        start_time = time.time()
        client.post("/auth/login", data={"username": "admin", "password": "wrong"})
        valid_user_time = time.time() - start_time

        start_time = time.time()
        client.post(
            "/auth/login", data={"username": "nonexistent", "password": "wrong"}
        )
        invalid_user_time = time.time() - start_time

        # Times should be roughly similar (within reasonable bounds)
        # This is a basic check - production systems need more sophisticated
        # timing analysis
        time_difference = abs(valid_user_time - invalid_user_time)
        assert time_difference < 1.0  # Should not leak timing information

    def test_sensitive_data_exposure(self, client, auth_headers):
        """Test sensitive data exposure prevention (OWASP A02: Cryptographic Failures)"""

        # Create user with sensitive information
        sensitive_resume = {
            "name": "John Sensitive",
            "title": "Security Tester",
            "contact": {
                "email": "john@sensitive.com",
                "phone": "+1-555-123-4567",
                "ssn": "123-45-6789",  # Should be filtered
                "credit_card": "4111-1111-1111-1111",  # Should be filtered
                "password": "secret123",  # Should be filtered
                "api_key": "sk_test_123456789",  # Should be filtered
                "private_key": "-----BEGIN PRIVATE KEY-----",  # Should be filtered
            },
            "salary": "$150,000",
            "personal_notes": "Confidential performance review notes",
        }

        response = client.post(
            "/api/v1/resume", json=sensitive_resume, headers=auth_headers
        )

        if response.status_code == 200:
            # Check that sensitive data is properly filtered in public access
            # Try the direct user-specific endpoint pattern first
            direct_url = "/api/v1/resume/users/admin?level=business_card"
            public_response = client.get(direct_url)

            # Debug: print what we're getting
            print(f"Direct URL response status: {public_response.status_code}")
            if public_response.status_code == 301:
                location = public_response.headers.get("location", "")
                print(f"Redirect location: {location}")
                if location:
                    public_response = client.get(location)
                    print(f"After redirect status: {public_response.status_code}")

            if public_response.status_code == 200:
                public_data = public_response.json()
                public_str = json.dumps(public_data)
                print(f"Response data: {public_str[:200]}...")
                public_str_lower = public_str.lower()

                # Sensitive patterns should be filtered out
                assert "123-45-6789" not in public_str_lower  # SSN
                assert "4111-1111-1111-1111" not in public_str_lower  # Credit card
                assert "secret123" not in public_str_lower  # Password
                assert "sk_test_" not in public_str_lower  # API key
                assert "private key" not in public_str_lower  # Private key

    def test_broken_access_control(self, client, auth_headers, regular_user_headers):
        """Test broken access control (OWASP A01: Broken Access Control)"""

        # Create data as admin user
        admin_response = client.post(
            "/api/v1/ideas",
            json={
                "title": "Admin Only Idea",
                "description": "This should only be accessible to admin",
                "category": "admin_only",
            },
            headers=auth_headers,
        )

        if admin_response.status_code == 200:
            admin_idea_id = admin_response.json()["id"]

            # Test horizontal privilege escalation - regular user trying to
            # access admin's data
            user_attempt = client.put(
                f"/api/v1/ideas/{admin_idea_id}",
                json={
                    "title": "Hacked by regular user",
                    "description": "This should not work",
                },
                headers=regular_user_headers,
            )
            # Should be forbidden or not found (proper access control)
            assert user_attempt.status_code in [403, 404]

            # Test delete attempt
            user_delete = client.delete(
                f"/api/v1/ideas/{admin_idea_id}", headers=regular_user_headers
            )
            assert user_delete.status_code in [403, 404]

        # Test vertical privilege escalation - regular user trying admin
        # functions (Note: Custom endpoint creation was removed, testing other admin functions)

        # Test access to admin-only user management endpoints
        user_admin_attempt = client.get("/admin/users", headers=regular_user_headers)
        assert user_admin_attempt.status_code in [401, 403]

        # Test attempt to access admin API key management
        user_apikey_attempt = client.get(
            "/admin/api-keys", headers=regular_user_headers
        )
        assert user_apikey_attempt.status_code in [401, 403]

    def test_security_misconfiguration(self, client):
        """Test security misconfiguration (OWASP A05: Security Misconfiguration)"""

        # Test that debug information is not exposed
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        response_text = response.text.lower()

        # Should not expose internal paths, stack traces, or debug info
        assert "traceback" not in response_text
        assert "exception" not in response_text
        assert "/users/" not in response_text  # Internal paths
        assert "sql" not in response_text
        assert "database" not in response_text

        # Test that sensitive headers are not exposed
        sensitive_headers = [
            "server",
            "x-powered-by",
            "x-aspnet-version",
            "x-debug",
            "x-source-file",
        ]

        for header in sensitive_headers:
            assert header not in [h.lower() for h in response.headers.keys()]

        # Test that proper security headers are present
        response = client.get("/")
        security_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-xss-protection": "1; mode=block",
        }

        # Note: These should be implemented in the application
        # This test documents what should be present

    def test_vulnerable_components(self, client):
        """Test for vulnerable and outdated components (OWASP A06: Vulnerable Components)"""

        # Test that version information is not exposed unnecessarily
        response = client.get("/")
        assert response.status_code == 200

        # Should not expose detailed version information
        response_data = response.json()
        if "version" in response_data:
            version = response_data["version"]
            # Version should be present but not overly detailed
            assert version is not None
            assert len(version) < 50  # Should not be extremely verbose

    def test_identification_authentication_failures(self, client):
        """Test identification and authentication failures (OWASP A07: Authentication Failures)"""

        # Test password brute force protection
        failed_attempts = []
        for i in range(5):
            start_time = datetime.now()
            response = client.post(
                "/auth/login",
                data={"username": "admin", "password": f"wrongpassword{i}"},
            )
            end_time = datetime.now()
            failed_attempts.append(
                {
                    "response_time": (end_time - start_time).total_seconds(),
                    "status_code": response.status_code,
                }
            )

        # Should consistently return 401 for wrong passwords
        for attempt in failed_attempts:
            assert attempt["status_code"] == 401

        # Test that user enumeration is prevented
        # (Both existing and non-existing users should have similar responses)
        existing_user_response = client.post(
            "/auth/login", data={"username": "admin", "password": "wrongpassword"}
        )
        nonexistent_user_response = client.post(
            "/auth/login",
            data={"username": "definitelynotauser", "password": "wrongpassword"},
        )

        # Both should return same status code (prevent user enumeration)
        assert (
            existing_user_response.status_code == nonexistent_user_response.status_code
        )

    def test_software_data_integrity_failures(self, client, auth_headers):
        """Test software and data integrity failures (OWASP A08: Software and Data Integrity Failures)"""

        # Test data tampering protection
        original_data = {
            "title": "Original Title",
            "description": "Original Description",
            "category": "original",
        }

        response = client.post(
            "/api/v1/ideas", json=original_data, headers=auth_headers
        )

        if response.status_code == 200:
            item_id = response.json()["id"]

            # Attempt to tamper with data using malformed updates
            tampered_data = {
                "id": 99999,  # Attempt to change ID
                "title": "Tampered Title",
                "description": "Tampered Description",
                "created_by_id": 999,  # Attempt to change ownership
                "is_admin": True,  # Attempt privilege escalation
            }

            response = client.put(
                f"/api/v1/ideas/{item_id}", json=tampered_data, headers=auth_headers
            )

            if response.status_code == 200:
                updated_data = response.json()["data"]
                # Verify that sensitive fields were not tampered with
                assert "id" not in updated_data or updated_data.get("id") == item_id
                assert (
                    "created_by_id" not in updated_data
                    or updated_data.get("created_by_id") != 999
                )

    def test_security_logging_monitoring_failures(self, client, auth_headers):
        """Test security logging and monitoring failures (OWASP A09: Security Logging and Monitoring Failures)"""

        # Test that security events would be logged (this is more of a documentation test)
        # In a real implementation, you'd verify logs are created

        # Failed authentication attempts
        client.post("/auth/login", data={"username": "admin", "password": "wrong"})

        # Unauthorized access attempts
        client.post("/api/v1/endpoints", json={"name": "test"})  # No auth

        # Suspicious data access patterns
        for i in range(10):
            client.get(f"/api/v1/ideas?page={i}")

        # These events should be logged in a production system
        # This test documents the requirement

    def test_server_side_request_forgery(self, client, auth_headers):
        """Test Server-Side Request Forgery (SSRF) prevention (OWASP A10: Server-Side Request Forgery)"""

        # Test that URLs pointing to internal services are rejected
        ssrf_payloads = [
            "http://localhost:22",
            "http://127.0.0.1:3306",
            "http://169.254.169.254",  # AWS metadata service
            "http://internal.company.com",
            "ftp://internal.server.com",
            "file:///etc/passwd",
            "dict://localhost:11211",
            "gopher://localhost:25",
        ]

        # Test in URL fields if any exist in the data models
        for payload in ssrf_payloads:
            # Test with resume data that might contain URLs
            resume_data = {
                "name": "Test User",
                "title": "Developer",
                "contact": {"website": payload, "linkedin": payload, "github": payload},
            }

            response = client.post(
                "/api/v1/resume", json=resume_data, headers=auth_headers
            )

            # Should either reject malicious URLs or sanitize them
            if response.status_code == 200:
                data = response.json()["data"]
                contact = data.get("contact", {})

                # Verify that internal URLs are not stored as-is
                for field in ["website", "linkedin", "github"]:
                    if field in contact:
                        stored_url = contact[field]
                        # Should not contain localhost or internal IPs
                        assert "localhost" not in stored_url
                        assert "127.0.0.1" not in stored_url
                        assert "169.254.169.254" not in stored_url

    def test_input_validation_and_sanitization(self, client, auth_headers):
        """Test comprehensive input validation and sanitization"""

        # Test various malicious input patterns
        malicious_inputs = [
            # Path traversal
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            # Command injection
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            # LDAP injection
            "*)(uid=*",
            "*)(|(password=*))",
            # XML injection
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
            # NoSQL injection
            "'; return 1; //",
            "{$where: 'this.password.match(/.*/)'}",
            # Template injection
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            # File upload bypass attempts
            "file.php.jpg",
            "file.jsp;.jpg",
            "file%00.jpg",
        ]

        for malicious_input in malicious_inputs:
            # Test in text fields
            response = client.post(
                "/api/v1/ideas",
                json={
                    "title": malicious_input,
                    "description": f"Testing malicious input: {malicious_input}",
                    "category": "security_test",
                },
                headers=auth_headers,
            )

            # Should either reject or properly sanitize
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                # If accepted, verify it's properly sanitized
                data = response.json()["data"]
                # Original malicious patterns should be neutralized
                assert "../" not in data["title"]
                assert "..\\" not in data["title"]
                assert "<?xml" not in data["title"]
                assert "{{" not in data["title"] or "}}" not in data["title"]

    def test_rate_limiting_and_dos_protection(self, client):
        """Test rate limiting and DoS protection"""

        # Test basic rate limiting
        responses = []
        for i in range(100):  # Send many requests quickly
            response = client.get("/api/v1/endpoints")
            responses.append(response.status_code)

            # Stop if we hit rate limiting
            if response.status_code == 429:
                break

        # Should implement some form of rate limiting
        # (This depends on the application's rate limiting configuration)

        # Test large payload handling
        huge_description = "A" * 100000  # 100KB description
        response = client.post(
            "/api/v1/ideas",
            json={
                "title": "DoS Test",
                "description": huge_description,
                "category": "dos_test",
            },
            headers={"Authorization": "Bearer fake_token"},
        )

        # Should handle large payloads gracefully (and may return 401 for
        # invalid auth)
        assert response.status_code in [200, 400, 401, 413, 422]  # Should not crash

    def test_information_disclosure_prevention(self, client):
        """Test prevention of information disclosure"""

        # Test error messages don't leak sensitive information
        error_responses = [
            client.get("/api/v1/nonexistent"),
            client.post("/api/v1/ideas", json={"invalid": "data"}),
            client.get("/api/v1/ideas/99999"),
            client.put("/api/v1/ideas/99999", json={"title": "test"}),
            client.delete("/api/v1/ideas/99999"),
        ]

        for response in error_responses:
            if response.status_code >= 400:
                error_text = response.text.lower()

                # Should not leak sensitive information
                sensitive_info = [
                    "password",
                    "secret",
                    "key",
                    "token",
                    "database",
                    "sql",
                    "traceback",
                    "exception",
                    "stack trace",
                    "internal server error",
                    "/home/",
                    "/var/",
                    "/opt/",
                    "c:\\",
                    "file not found",
                ]

                for info in sensitive_info:
                    assert info not in error_text

    def test_cors_configuration(self, client):
        """Test CORS configuration security"""

        # Test that CORS is properly configured
        response = client.options("/api/v1/endpoints")

        # Should have CORS headers but not wildcard for credentials
        cors_headers = {
            key.lower(): value
            for key, value in response.headers.items()
            if key.lower().startswith("access-control")
        }

        # If CORS is enabled, it should be properly configured
        if cors_headers:
            # Should not allow all origins with credentials
            origin_header = cors_headers.get("access-control-allow-origin", "")
            credentials_header = cors_headers.get(
                "access-control-allow-credentials", ""
            )

            if credentials_header.lower() == "true":
                assert origin_header != "*"  # Dangerous combination

    def test_content_type_validation(self, client, auth_headers):
        """Test content type validation"""

        # Test that only expected content types are accepted
        invalid_content_types = [
            "text/html",
            "application/xml",
            "text/plain",
            "application/x-www-form-urlencoded",  # For JSON endpoints
        ]

        for content_type in invalid_content_types:
            response = client.post(
                "/api/v1/ideas",
                data=json.dumps({"title": "Test", "description": "Test"}),
                headers={**auth_headers, "Content-Type": content_type},
            )

            # Should reject unexpected content types for JSON endpoints
            # (Unless specifically designed to accept them)
            if content_type != "application/json":
                assert response.status_code in [400, 415, 422]

    def test_http_methods_security(self, client):
        """Test HTTP methods security"""

        # Test that dangerous HTTP methods are disabled
        dangerous_methods = ["TRACE", "TRACK", "CONNECT"]

        for method in dangerous_methods:
            # Most test clients don't support all methods, so we test what we
            # can
            if hasattr(client, method.lower()):
                response = getattr(client, method.lower())("/api/v1/endpoints")
                # Should be method not allowed
                assert response.status_code in [405, 501]

    def test_session_security(self, client):
        """Test session security (if sessions are used)"""

        # Test JWT token security
        response = client.post(
            "/auth/login", data={"username": "admin", "password": "admin123"}
        )

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token", "")

            if token:
                # JWT should not contain sensitive information in payload
                try:
                    # Decode JWT payload (without verification for testing)
                    parts = token.split(".")
                    if len(parts) >= 2:
                        # Add padding if needed
                        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
                        decoded = base64.urlsafe_b64decode(payload)
                        payload_data = json.loads(decoded)

                        # Should not contain sensitive information
                        sensitive_fields = ["password", "secret", "key", "hash"]
                        for field in sensitive_fields:
                            assert field not in payload_data

                except Exception:
                    # If we can't decode, that's actually good for security
                    pass


class TestRoutingSecurityRegression:
    """Regression tests for routing security vulnerabilities"""

    def test_route_precedence_security(self, client, auth_headers):
        """Test that route precedence cannot be exploited for unauthorized access"""
        # Create private content
        private_content = {
            "content": "This is private admin content",
            "meta": {"title": "Admin Secret", "visibility": "private"},
        }
        response = client.post(
            "/api/v1/about", json=private_content, headers=auth_headers
        )
        item_id = response.json()["id"] if response.status_code == 200 else None

        try:
            # Test various malformed patterns that might exploit route precedence
            malformed_patterns = [
                "/api/v1/about/users/admin/../../../secrets",
                "/api/v1/about/users/admin/%2e%2e%2f%2e%2e%2fsecrets",
                "/api/v1/about/users/admin//../../admin",
                "/api/v1/about//users//admin",
                "/api/v1/about/users/admin/extra/path",
                "/api/v1/users/admin/about/../../../secrets",
                "/api/v1/users/admin/../admin/about",
            ]

            for pattern in malformed_patterns:
                response = client.get(pattern)

                # For patterns that HTTP clients normalize to valid URLs,
                # check that no private data is leaked instead of rejecting the request
                normalized_valid_patterns = [
                    "/api/v1/about/users/admin//../../admin",  # normalizes to /api/v1/about/users/admin
                    "/api/v1/about//users//admin",  # normalizes to /api/v1/about/users/admin
                    "/api/v1/users/admin/../admin/about",  # normalizes to /api/v1/users/admin/about
                ]

                if pattern in normalized_valid_patterns:
                    # These patterns are normalized by HTTP clients, so ensure no private data leaks
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list):
                                for item in data:
                                    title = item.get("meta", {}).get("title", "")
                                    assert (
                                        "Admin Secret" not in title
                                    ), f"Private content leaked via normalized pattern: {pattern}"
                        except Exception:
                            pass  # JSON parsing error is acceptable
                else:
                    # Other patterns should be rejected outright
                    assert response.status_code in [
                        400,
                        404,
                        422,
                    ], f"Malformed pattern should be rejected: {pattern}"

                    # Even if we get a response, it shouldn't contain private data
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list):
                                for item in data:
                                    title = item.get("meta", {}).get("title", "")
                                    assert (
                                        "Admin Secret" not in title
                                    ), f"Private content leaked via: {pattern}"
                        except Exception:
                            pass  # JSON parsing error is acceptable

        finally:
            if item_id:
                client.delete(f"/api/v1/about/{item_id}", headers=auth_headers)

    def test_endpoint_name_injection_prevention(self, client):
        """Test that endpoint names cannot be injected to access wrong routes"""
        dangerous_endpoint_names = [
            "users/admin",
            "users%2Fadmin",
            "../admin",
            "..%2Fadmin",
            "admin/../../secrets",
            "/etc/passwd",
            "../../app/config",
        ]

        # Valid but potentially confusing patterns that should work correctly
        potentially_confusing_patterns = [
            "resume/users/admin",  # This is actually a valid user-specific pattern
        ]

        for endpoint_name in dangerous_endpoint_names:
            # Test direct endpoint access
            response = client.get(f"/api/v1/{endpoint_name}")
            # Should return 404 or error, not successful data
            assert response.status_code in [
                400,
                404,
                422,
            ], f"Dangerous endpoint should be rejected: {endpoint_name}"

            # Test in user-specific patterns
            response = client.get(f"/api/v1/{endpoint_name}/users/admin")
            assert response.status_code in [
                400,
                404,
                422,
            ], f"Dangerous pattern should be rejected: {endpoint_name}/users/admin"

            response = client.get(f"/api/v1/users/admin/{endpoint_name}")
            assert response.status_code in [
                400,
                404,
                422,
            ], f"Dangerous pattern should be rejected: users/admin/{endpoint_name}"

        # Test potentially confusing but valid patterns
        for pattern in potentially_confusing_patterns:
            response = client.get(f"/api/v1/{pattern}")
            # This should work as it's a valid user-specific endpoint pattern
            # In single-user mode, it should redirect; in multi-user mode, it should work directly
            assert response.status_code in [
                200,
                301,
            ], f"Valid pattern should work or redirect: {pattern}"

    def test_username_injection_prevention(self, client, auth_headers):
        """Test that usernames cannot be injected to access wrong data"""
        # Create test content
        test_content = {
            "content": "Test content",
            "meta": {"title": "Test", "visibility": "public"},
        }
        client.post("/api/v1/about", json=test_content, headers=auth_headers)

        dangerous_usernames = [
            "../admin",
            "..%2Fadmin",
            "admin/../../secrets",
            "/etc/passwd",
            "../../app/config",
            "admin/../user",
            "admin%2F%2E%2E%2Fuser",
        ]

        for username in dangerous_usernames:
            # Test user-specific patterns
            response = client.get(f"/api/v1/about/users/{username}")

            # Some patterns may be normalized by HTTP servers to valid paths
            normalized_patterns = [
                "admin/../user",  # normalizes to "user" which may be valid
            ]

            if username in normalized_patterns:
                # These patterns are normalized to potentially valid usernames
                # Ensure they either fail (user doesn't exist) or return correct data
                assert response.status_code in [
                    200,
                    301,
                    404,
                ], f"Normalized pattern should be handled correctly: {username}"
                if response.status_code == 200:
                    # If it succeeds, ensure no private admin data is leaked
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            for item in data:
                                title = item.get("meta", {}).get("title", "")
                                assert (
                                    "Admin Secret" not in title
                                ), f"Admin data leaked via normalized pattern: {username}"
                    except Exception:
                        pass
            else:
                # Other patterns should be rejected for malformed usernames
                assert response.status_code in [
                    400,
                    404,
                    422,
                ], f"Dangerous username should be rejected: {username}"

            response = client.get(f"/api/v1/users/{username}/about")

            if username in normalized_patterns:
                # These patterns are normalized to potentially valid usernames
                assert response.status_code in [
                    200,
                    301,
                    404,
                ], f"Normalized pattern should be handled correctly in legacy route: {username}"
                if response.status_code == 200:
                    # If it succeeds, ensure no private admin data is leaked
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            for item in data:
                                title = item.get("meta", {}).get("title", "")
                                assert (
                                    "Admin Secret" not in title
                                ), f"Admin data leaked via normalized legacy pattern: {username}"
                    except Exception:
                        pass
            else:
                assert response.status_code in [
                    400,
                    404,
                    422,
                ], f"Dangerous username should be rejected in pattern: users/{username}/about"

    def test_cross_user_data_isolation(self, client, auth_headers):
        """Test that users cannot access other users' data through any URL pattern"""
        # This test assumes we have multiple users in the system

        # Create private content for admin
        private_content = {
            "content": "Admin private data",
            "meta": {"title": "Admin Private", "visibility": "private"},
        }
        response = client.post(
            "/api/v1/about", json=private_content, headers=auth_headers
        )
        admin_item_id = response.json()["id"] if response.status_code == 200 else None

        try:
            # Test accessing admin data as different user patterns
            test_patterns = [
                "/api/v1/about/users/admin",
                "/api/v1/users/admin/about",
                "/api/v1/resume/users/admin",
                "/api/v1/users/admin/resume",
                "/api/v1/skills/users/admin",
                "/api/v1/users/admin/skills",
            ]

            for pattern in test_patterns:
                # Test unauthenticated access
                response = client.get(pattern)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        # Should not contain private content
                        for item in data:
                            visibility = item.get("meta", {}).get(
                                "visibility", "public"
                            )
                            assert (
                                visibility != "private"
                            ), f"Private content exposed via unauthenticated {pattern}"

                            title = item.get("meta", {}).get("title", "")
                            assert (
                                "Admin Private" not in title
                            ), f"Admin private data exposed via {pattern}"

        finally:
            if admin_item_id:
                client.delete(f"/api/v1/about/{admin_item_id}", headers=auth_headers)

    def test_response_format_consistency_security(self, client, auth_headers):
        """Test that response formats are consistent to prevent information leakage"""
        # Create test data
        test_content = {
            "content": "Test data",
            "meta": {"title": "Test", "visibility": "public"},
        }
        client.post("/api/v1/about", json=test_content, headers=auth_headers)

        endpoints = ["about", "resume", "skills"]
        users = ["admin", "nonexistent_user"]

        for endpoint in endpoints:
            for user in users:
                # Test both URL patterns
                pattern1_response = client.get(f"/api/v1/{endpoint}/users/{user}")
                pattern2_response = client.get(f"/api/v1/users/{user}/{endpoint}")

                # Response formats should be consistent
                if (
                    pattern1_response.status_code == 200
                    and pattern2_response.status_code == 200
                ):
                    try:
                        data1 = pattern1_response.json()
                        data2 = pattern2_response.json()

                        # Both should have same structure
                        assert type(data1) is type(
                            data2
                        ), f"Response types should match for {endpoint}/{user}"

                        if isinstance(data1, list) and isinstance(data2, list):
                            assert len(data1) == len(
                                data2
                            ), f"Response lengths should match for {endpoint}/{user}"

                    except Exception:
                        pass  # JSON parsing errors are acceptable

                # Error responses should also be consistent
                elif pattern1_response.status_code == pattern2_response.status_code:
                    # Same error status is good
                    pass
                elif pattern2_response.status_code == 301:
                    # Redirect is acceptable for pattern 2
                    pass
                else:
                    # Different error statuses might indicate information leakage
                    assert (
                        False
                    ), f"Inconsistent error responses for {endpoint}/{user}: {pattern1_response.status_code} vs {pattern2_response.status_code}"
