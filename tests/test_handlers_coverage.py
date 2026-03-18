"""
Additional handler tests to improve coverage on mcp/handlers.py.

Covers:
- _format_error_response with generic (non-ResumeCustomizerError) exception
- handle_list_customizations with various filter combinations
- handle_generate_resume_files error paths (missing customization_id, missing profile)
"""

import pytest

from resume_customizer.mcp.handlers import (
    _format_error_response,
    _session_state,
    handle_generate_resume_files,
    handle_list_customizations,
)
from resume_customizer.core.exceptions import ResumeCustomizerError, ValidationError


@pytest.fixture(autouse=True)
def clear_session():
    """Clear session state before each test."""
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()
    yield
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()


class TestFormatErrorResponse:
    """Tests for _format_error_response helper."""

    def test_resume_customizer_error_without_suggestion(self):
        err = ResumeCustomizerError("something failed")
        result = _format_error_response(err)
        assert result["status"] == "error"
        assert result["message"] == "something failed"
        assert "suggestion" not in result

    def test_resume_customizer_error_with_suggestion(self):
        err = ResumeCustomizerError("bad input", suggestion="try this instead")
        result = _format_error_response(err)
        assert result["status"] == "error"
        assert result["message"] == "bad input"
        assert result["suggestion"] == "try this instead"

    def test_validation_error_includes_suggestion(self):
        err = ValidationError("file_path", "must not be empty")
        result = _format_error_response(err)
        assert result["status"] == "error"
        assert "suggestion" in result

    def test_generic_exception_returns_error(self):
        """Non-ResumeCustomizerError exceptions should return generic error response."""
        err = RuntimeError("unexpected crash")
        result = _format_error_response(err)
        assert result["status"] == "error"
        assert "unexpected" in result["message"].lower() or "unexpected crash" in result["message"]
        assert "suggestion" in result

    def test_generic_valueerror(self):
        err = ValueError("bad value")
        result = _format_error_response(err)
        assert result["status"] == "error"
        assert "bad value" in result["message"]

    def test_generic_keyerror(self):
        err = KeyError("missing_key")
        result = _format_error_response(err)
        assert result["status"] == "error"


class TestListCustomizations:
    """Tests for handle_list_customizations with various filter combinations."""

    def test_no_filters_returns_list(self):
        result = handle_list_customizations({})
        assert result["status"] == "success"
        assert isinstance(result["customizations"], list)
        assert isinstance(result["count"], int)
        assert result["count"] == len(result["customizations"])

    def test_with_company_filter_returns_list(self):
        result = handle_list_customizations({"filter_by_company": "ZZZ_Nonexistent_Corp_XYZ"})
        assert result["status"] == "success"
        assert isinstance(result["customizations"], list)

    def test_with_limit(self):
        result = handle_list_customizations({"limit": 5})
        assert result["status"] == "success"
        assert isinstance(result["customizations"], list)

    def test_with_date_range_filter(self):
        result = handle_list_customizations({
            "filter_by_date_range": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            }
        })
        assert result["status"] == "success"

    def test_with_all_filters(self):
        result = handle_list_customizations({
            "filter_by_company": "ZZZ_Nonexistent_Corp_XYZ",
            "filter_by_date_range": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
            "limit": 3,
        })
        assert result["status"] == "success"
        assert isinstance(result["customizations"], list)

    def test_message_includes_count(self):
        result = handle_list_customizations({})
        assert "0" in result["message"]

    def test_empty_date_range_dict(self):
        """Empty date range dict should be handled gracefully."""
        result = handle_list_customizations({"filter_by_date_range": {}})
        assert result["status"] == "success"


class TestGenerateResumeFilesErrorPaths:
    """Tests for handle_generate_resume_files error handling paths."""

    def test_missing_customization_id(self):
        result = handle_generate_resume_files({})
        assert result["status"] == "error"
        assert "customization_id" in result["message"].lower()

    def test_nonexistent_customization_id(self):
        result = handle_generate_resume_files({
            "customization_id": "nonexistent-id-xyz",
        })
        assert result["status"] == "error"
        assert "not found" in result["message"].lower()

    def test_default_output_formats(self):
        """Missing customization returns error, not format error."""
        result = handle_generate_resume_files({
            "customization_id": "fake-id",
            "output_formats": ["pdf", "docx"],
        })
        assert result["status"] == "error"
