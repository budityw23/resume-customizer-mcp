"""
Tests for MCP input validation utilities (src/resume_customizer/utils/validation.py).

Tests validation functions for file paths, IDs, integers, enums, and preferences.
"""

import tempfile
from pathlib import Path

import pytest

from resume_customizer.core.exceptions import ValidationError
from resume_customizer.utils.validation import (
    validate_enum,
    validate_file_path,
    validate_id,
    validate_output_formats,
    validate_positive_integer,
    validate_preferences,
)


class TestValidateFilePath:
    """Test file path validation."""

    def test_valid_file_path(self) -> None:
        """Test validation of valid file path."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name

        try:
            result = validate_file_path(file_path)
            assert result == file_path
        finally:
            Path(file_path).unlink()

    def test_empty_file_path(self) -> None:
        """Test validation of empty file path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("")

        assert "required" in str(exc_info.value).lower()

    def test_none_file_path(self) -> None:
        """Test validation of None file path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path(None)

        assert "required" in str(exc_info.value).lower()

    def test_non_string_file_path(self) -> None:
        """Test validation of non-string file path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path(123)  # type: ignore

        assert "string" in str(exc_info.value).lower()

    def test_nonexistent_file_path(self) -> None:
        """Test validation of non-existent file path."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path("/nonexistent/file.txt")

        assert "exist" in str(exc_info.value).lower()

    def test_directory_path(self) -> None:
        """Test validation of directory path (should fail)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError) as exc_info:
                validate_file_path(tmpdir)

            assert "not a file" in str(exc_info.value).lower()

    def test_custom_param_name(self) -> None:
        """Test validation with custom parameter name."""
        with pytest.raises(ValidationError) as exc_info:
            validate_file_path(None, param_name="custom_file")

        assert "custom_file" in str(exc_info.value).lower()


class TestValidateId:
    """Test ID validation."""

    def test_valid_id(self) -> None:
        """Test validation of valid ID."""
        result = validate_id("profile-123", "profile_id")
        assert result == "profile-123"

    def test_empty_id(self) -> None:
        """Test validation of empty ID."""
        with pytest.raises(ValidationError) as exc_info:
            validate_id("", "profile_id")

        assert "required" in str(exc_info.value).lower()

    def test_none_id(self) -> None:
        """Test validation of None ID."""
        with pytest.raises(ValidationError) as exc_info:
            validate_id(None, "profile_id")

        assert "required" in str(exc_info.value).lower()

    def test_whitespace_id(self) -> None:
        """Test validation of whitespace-only ID."""
        with pytest.raises(ValidationError) as exc_info:
            validate_id("   ", "profile_id")

        assert "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()

    def test_non_string_id(self) -> None:
        """Test validation of non-string ID."""
        with pytest.raises(ValidationError) as exc_info:
            validate_id(123, "profile_id")  # type: ignore

        assert "string" in str(exc_info.value).lower()

    def test_id_with_resource_type(self) -> None:
        """Test validation with resource type for better error messages."""
        with pytest.raises(ValidationError) as exc_info:
            validate_id(None, "profile_id", resource_type="user profile")

        error_msg = str(exc_info.value).lower()
        assert "user profile" in error_msg or "required" in error_msg


class TestValidatePositiveInteger:
    """Test positive integer validation."""

    def test_valid_positive_integer(self) -> None:
        """Test validation of valid positive integer."""
        result = validate_positive_integer(5, "count")
        assert result == 5

    def test_non_integer(self) -> None:
        """Test validation of non-integer value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer("5", "count")  # type: ignore

        assert "integer" in str(exc_info.value).lower()

    def test_below_minimum(self) -> None:
        """Test validation of value below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer(0, "count", min_value=1)

        assert "at least" in str(exc_info.value).lower() or "1" in str(exc_info.value)

    def test_above_maximum(self) -> None:
        """Test validation of value above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_integer(15, "count", max_value=10)

        assert "at most" in str(exc_info.value).lower() or "10" in str(exc_info.value)

    def test_custom_min_value(self) -> None:
        """Test validation with custom minimum value."""
        result = validate_positive_integer(10, "count", min_value=10)
        assert result == 10

    def test_custom_max_value(self) -> None:
        """Test validation with custom maximum value."""
        result = validate_positive_integer(10, "count", max_value=10)
        assert result == 10


class TestValidateEnum:
    """Test enum validation."""

    def test_valid_enum_value(self) -> None:
        """Test validation of valid enum value."""
        result = validate_enum("pdf", "format", ["pdf", "docx"])
        assert result == "pdf"

    def test_invalid_enum_value(self) -> None:
        """Test validation of invalid enum value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_enum("txt", "format", ["pdf", "docx"])

        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "txt" in error_msg

    def test_case_insensitive_match(self) -> None:
        """Test case-insensitive enum validation."""
        result = validate_enum("PDF", "format", ["pdf", "docx"], case_sensitive=False)
        assert result == "PDF"

    def test_case_sensitive_mismatch(self) -> None:
        """Test case-sensitive enum validation fails on case mismatch."""
        with pytest.raises(ValidationError):
            validate_enum("PDF", "format", ["pdf", "docx"], case_sensitive=True)

    def test_non_string_enum_value(self) -> None:
        """Test validation of non-string enum value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_enum(123, "format", ["pdf", "docx"])  # type: ignore

        assert "string" in str(exc_info.value).lower()


class TestValidateOutputFormats:
    """Test output formats validation."""

    def test_valid_output_formats(self) -> None:
        """Test validation of valid output formats."""
        result = validate_output_formats(["pdf", "docx"])
        assert result == ["pdf", "docx"]

    def test_single_format(self) -> None:
        """Test validation of single format."""
        result = validate_output_formats(["pdf"])
        assert result == ["pdf"]

    def test_case_normalization(self) -> None:
        """Test that formats are normalized to lowercase."""
        result = validate_output_formats(["PDF", "DOCX"])
        assert result == ["pdf", "docx"]

    def test_non_list_formats(self) -> None:
        """Test validation of non-list formats."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_formats("pdf")  # type: ignore

        assert "list" in str(exc_info.value).lower()

    def test_empty_formats_list(self) -> None:
        """Test validation of empty formats list."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_formats([])

        assert "at least one" in str(exc_info.value).lower()

    def test_invalid_format_in_list(self) -> None:
        """Test validation with invalid format in list."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_formats(["pdf", "txt"])

        assert "invalid" in str(exc_info.value).lower() or "txt" in str(exc_info.value).lower()

    def test_non_string_format_in_list(self) -> None:
        """Test validation with non-string format in list."""
        with pytest.raises(ValidationError) as exc_info:
            validate_output_formats([123, "pdf"])  # type: ignore

        assert "string" in str(exc_info.value).lower()


class TestValidatePreferences:
    """Test customization preferences validation."""

    def test_valid_preferences(self) -> None:
        """Test validation of valid preferences."""
        prefs = {
            "achievements_per_role": 4,
            "max_skills": 10,
            "template": "modern",
            "include_summary": True,
        }

        result = validate_preferences(prefs)

        assert result["achievements_per_role"] == 4
        assert result["max_skills"] == 10
        assert result["template"] == "modern"
        assert result["include_summary"] is True

    def test_empty_preferences(self) -> None:
        """Test validation of empty preferences dict."""
        result = validate_preferences({})
        assert result == {}

    def test_non_dict_preferences(self) -> None:
        """Test validation of non-dict preferences."""
        with pytest.raises(ValidationError) as exc_info:
            validate_preferences("not a dict")  # type: ignore

        assert "dictionary" in str(exc_info.value).lower()

    def test_invalid_achievements_per_role(self) -> None:
        """Test validation with invalid achievements_per_role."""
        with pytest.raises(ValidationError):
            validate_preferences({"achievements_per_role": 0})

    def test_achievements_per_role_above_max(self) -> None:
        """Test validation with achievements_per_role above maximum."""
        with pytest.raises(ValidationError):
            validate_preferences({"achievements_per_role": 11})

    def test_invalid_max_skills(self) -> None:
        """Test validation with invalid max_skills."""
        with pytest.raises(ValidationError):
            validate_preferences({"max_skills": 0})

    def test_max_skills_above_max(self) -> None:
        """Test validation with max_skills above maximum."""
        with pytest.raises(ValidationError):
            validate_preferences({"max_skills": 101})

    def test_invalid_template(self) -> None:
        """Test validation with invalid template."""
        with pytest.raises(ValidationError):
            validate_preferences({"template": "invalid_template"})

    def test_valid_templates(self) -> None:
        """Test validation with all valid templates."""
        valid_templates = ["modern", "classic", "minimal", "elegant", "ats_optimized"]

        for template in valid_templates:
            result = validate_preferences({"template": template})
            assert result["template"] == template

    def test_non_boolean_include_summary(self) -> None:
        """Test validation with non-boolean include_summary."""
        with pytest.raises(ValidationError) as exc_info:
            validate_preferences({"include_summary": "yes"})  # type: ignore

        assert "boolean" in str(exc_info.value).lower()

    def test_partial_preferences(self) -> None:
        """Test validation with only some preferences set."""
        prefs = {"template": "modern"}
        result = validate_preferences(prefs)

        assert result == {"template": "modern"}
        assert "achievements_per_role" not in result
        assert "max_skills" not in result

    def test_unknown_preferences_ignored(self) -> None:
        """Test that unknown preferences are ignored."""
        prefs = {
            "template": "modern",
            "unknown_field": "value",
        }
        result = validate_preferences(prefs)

        assert result == {"template": "modern"}
        assert "unknown_field" not in result
