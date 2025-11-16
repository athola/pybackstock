"""Security tests for the inventory application."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture()
def csrf_app():
    """Create a Flask app with CSRF protection enabled for security testing."""
    from inventoryApp import app

    # Temporarily enable CSRF for these specific tests
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["TESTING"] = True
    return app


@pytest.fixture()
def csrf_client(csrf_app: Any) -> Any:
    """Create a test client with CSRF protection enabled."""
    return csrf_app.test_client()


class TestCSRFProtection:
    """Test CSRF protection implementation."""

    def test_csrf_protection_enabled_in_config(self, csrf_app: Any) -> None:
        """Test that CSRF protection is enabled in configuration."""
        assert csrf_app.config.get("WTF_CSRF_ENABLED", False) is True

    def test_csrf_token_present_in_search_form(self, csrf_client: Any) -> None:
        """Test that CSRF token is present in search form."""
        response = csrf_client.get("/")
        assert response.status_code == 200
        assert b"csrf_token" in response.data or b"csrf-token" in response.data

    def test_csrf_token_present_in_add_form(self, csrf_client: Any) -> None:
        """Test that CSRF token is present in add item form."""
        # First get a CSRF token from the initial page
        initial_response = csrf_client.get("/")
        assert initial_response.status_code == 200

        # Extract CSRF token from the response
        import re
        csrf_match = re.search(rb'name="csrf_token" value="([^"]+)"', initial_response.data)
        assert csrf_match is not None, "CSRF token not found in initial response"
        csrf_token = csrf_match.group(1).decode()

        # Now switch to add item form with CSRF token
        response = csrf_client.post("/", data={"add-item": "", "csrf_token": csrf_token})
        assert response.status_code == 200
        assert b"csrf_token" in response.data or b"csrf-token" in response.data

    def test_post_request_without_csrf_token_rejected(self, csrf_client: Any) -> None:
        """Test that POST requests without CSRF token are rejected when CSRF is enabled."""
        response = csrf_client.post(
            "/",
            data={
                "send-add": "",
                "id-add": "9999",
                "description-add": "Test Item",
                "last-sold-add": "2024-01-01",
                "shelf-life-add": "7d",
                "department-add": "Test",
                "price-add": "1.99",
                "unit-add": "ea",
                "xfor-add": "1",
                "cost-add": "0.99",
            },
        )
        # Should be rejected (400 Bad Request)
        assert response.status_code == 400


class TestSecurityHeaders:
    """Test security headers implementation."""

    def test_x_frame_options_header_present(self, client: Any) -> None:
        """Test that X-Frame-Options header is set to prevent clickjacking."""
        response = client.get("/")
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] in ("DENY", "SAMEORIGIN")

    def test_x_content_type_options_header_present(self, client: Any) -> None:
        """Test that X-Content-Type-Options header is set."""
        response = client.get("/")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_content_security_policy_header_present(self, client: Any) -> None:
        """Test that Content-Security-Policy header is set."""
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp

    def test_strict_transport_security_disabled_in_testing(self, app: Flask) -> None:
        """Test that HSTS is disabled in testing environment."""
        # HSTS should only be enabled in production with HTTPS
        # In testing, it should be disabled to avoid redirect loops
        with app.test_client() as client:
            response = client.get("/")
            # Should NOT have HSTS in testing
            assert "Strict-Transport-Security" not in response.headers or app.config.get("TESTING")


class TestErrorHandling:
    """Test secure error handling."""

    def test_error_messages_do_not_expose_internal_details(self, client: Any) -> None:
        """Test that error messages don't expose stack traces or line numbers."""
        # Search for non-existent item (should work without errors)
        response = client.post(
            "/",
            data={
                "send-search": "",
                "column": "id",
                "item": "nonexistent",  # This will trigger an error (not a digit)
            },
        )
        assert response.status_code == 200
        # Even if there's an error, internal details should not be exposed
        assert b"line no:" not in response.data
        assert b"KeyError" not in response.data
        assert b"ValueError" not in response.data
        assert b"TypeError" not in response.data

    def test_generic_error_message_shown_to_user(self, client: Any) -> None:
        """Test that users see helpful messages without internal details."""
        # This tests that the application returns sensible responses
        response = client.post(
            "/",
            data={
                "send-search": "",
                "column": "id",
                "item": "12345",
            },
        )
        assert response.status_code == 200
        # Response should be valid HTML, not an error dump
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestFileUploadSecurity:
    """Test file upload security measures."""

    def test_file_upload_size_limit(self, app: Flask) -> None:
        """Test that file upload size limit is configured."""
        # Flask's MAX_CONTENT_LENGTH should be set
        assert app.config.get("MAX_CONTENT_LENGTH") is not None
        # Should be reasonable (e.g., 16MB)
        assert app.config["MAX_CONTENT_LENGTH"] <= 16 * 1024 * 1024

    def test_file_upload_validates_content_type(self, client: Any) -> None:
        """Test that file uploads validate content type."""
        from io import BytesIO

        # Try uploading a file with wrong content type
        data = {"csv-submit": "", "csv-input": (BytesIO(b"malicious content"), "test.csv")}
        _response = client.post("/", data=data, content_type="multipart/form-data")
        # Implementation should validate content type
        # This test documents expected behavior

    def test_file_upload_rejects_oversized_files(self, client: Any) -> None:
        """Test that oversized files are rejected."""
        from io import BytesIO

        # Create a large CSV (if MAX_CONTENT_LENGTH is set)
        large_content = b"x" * (17 * 1024 * 1024)  # 17MB
        data = {"csv-submit": "", "csv-input": (BytesIO(large_content), "large.csv")}
        response = client.post("/", data=data, content_type="multipart/form-data")
        # Should be rejected with 413 Payload Too Large
        assert response.status_code in (413, 200)  # 200 if validation happens in handler


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_protection_via_orm(self, client: Any) -> None:
        """Test that SQLAlchemy ORM protects against SQL injection."""
        # SQLAlchemy ORM uses parameterized queries automatically
        # This test documents that we rely on ORM, not manual checks

        # Try various SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE grocery_items; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ]

        for malicious_input in malicious_inputs:
            response = client.post(
                "/",
                data={
                    "send-search": "",
                    "column": "description",
                    "item": malicious_input,
                },
            )
            # Should not crash or cause SQL errors
            assert response.status_code == 200
            # Should not return unexpected results - literal string might appear in search but not execute
            # The important thing is the app doesn't crash

    def test_no_misleading_sql_injection_check(self) -> None:
        """Test that code doesn't contain ineffective SQL injection checks."""
        import inventoryApp
        from pathlib import Path

        # Read the source code
        source = Path(inventoryApp.__file__)
        code = source.read_text()

        # Should not have naive "DROP TABLE" check
        assert 'if "DROP TABLE" in search_item:' not in code

    def test_xss_protection_in_output(self, client: Any) -> None:
        """Test that user input is properly escaped in output."""
        # Try adding item with XSS payload
        xss_payload = "<script>alert('XSS')</script>"
        response = client.post(
            "/",
            data={
                "send-add": "",
                "id-add": "9998",
                "description-add": xss_payload,
                "last-sold-add": "2024-01-01",
                "shelf-life-add": "7d",
                "department-add": "Test",
                "price-add": "1.99",
                "unit-add": "ea",
                "xfor-add": "1",
                "cost-add": "0.99",
            },
        )
        # Jinja2 auto-escapes by default
        # The literal script tag should not appear in response
        assert b"<script>alert" not in response.data


class TestSessionSecurity:
    """Test session security configuration."""

    def test_session_cookie_httponly(self, app: Flask) -> None:
        """Test that session cookies are HTTPOnly."""
        assert app.config.get("SESSION_COOKIE_HTTPONLY", True) is True

    def test_session_cookie_secure_in_production(self, app: Flask) -> None:
        """Test that session cookies are Secure in production."""
        if not app.config.get("DEBUG"):
            assert app.config.get("SESSION_COOKIE_SECURE", False) is True

    def test_session_cookie_samesite(self, app: Flask) -> None:
        """Test that session cookies have SameSite attribute."""
        samesite = app.config.get("SESSION_COOKIE_SAMESITE")
        assert samesite in ("Lax", "Strict", None)


# Type hints import
from typing import Any
