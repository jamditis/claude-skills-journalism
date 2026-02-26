"""
Example: Bug reproduction test in Python (pytest)

Bug reported: "User login fails silently when email contains leading/trailing spaces"

Expected: Login should work after trimming whitespace, or return clear error
Actual: Login returns success=False with no error message
"""

import pytest
from unittest.mock import Mock, patch

# Assume this is the buggy code location
# from myapp.auth import AuthService


class TestLoginWhitespaceBug:
    """
    Bug reproduction tests for email whitespace handling.

    Issue: https://github.com/org/repo/issues/123
    Reported: 2026-02-01

    These tests should FAIL before the fix and PASS after.
    """

    def test_login_with_leading_space_in_email(self):
        """Bug: leading space causes silent failure"""
        auth = AuthService()

        # Email with leading space - user copy/pasted from somewhere
        result = auth.login(" user@example.com", "correct_password")

        # Should either succeed (after trimming) or give clear error
        assert result.success is True or result.error is not None
        if not result.success:
            assert "whitespace" in result.error.lower() or "trim" in result.error.lower()

    def test_login_with_trailing_space_in_email(self):
        """Bug: trailing space causes silent failure"""
        auth = AuthService()

        result = auth.login("user@example.com ", "correct_password")

        assert result.success is True or result.error is not None

    def test_login_with_spaces_around_email(self):
        """Bug: spaces on both sides cause silent failure"""
        auth = AuthService()

        result = auth.login("  user@example.com  ", "correct_password")

        # Most permissive fix: trim and succeed
        assert result.success is True

    def test_login_error_message_is_helpful(self):
        """Even if we reject spaced emails, error should be clear"""
        auth = AuthService()

        result = auth.login(" bad@email.com", "password")

        if not result.success:
            # Error message should explain the problem
            assert result.error is not None
            assert len(result.error) > 10  # Not just "error" or "failed"


class TestLoginNormalCases:
    """
    Regression tests - ensure fix doesn't break normal login.
    """

    def test_login_with_valid_credentials(self):
        """Normal login should still work"""
        auth = AuthService()

        result = auth.login("user@example.com", "correct_password")

        assert result.success is True
        assert result.user is not None

    def test_login_with_wrong_password(self):
        """Wrong password should fail with clear error"""
        auth = AuthService()

        result = auth.login("user@example.com", "wrong_password")

        assert result.success is False
        assert "password" in result.error.lower() or "credentials" in result.error.lower()


# Minimal mock for demonstration - replace with actual import
class AuthService:
    """Mock - replace with actual import"""

    def login(self, email: str, password: str):
        # This simulates the BUGGY behavior
        # The fix would add: email = email.strip()
        if email != "user@example.com":  # Bug: doesn't strip spaces
            return Mock(success=False, error=None, user=None)  # Silent failure!
        if password != "correct_password":
            return Mock(success=False, error="Invalid credentials", user=None)
        return Mock(success=True, error=None, user={"email": email})


# Run with: pytest examples/python-bug-test.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
