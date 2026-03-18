"""
Tests for custom exceptions in resume_customizer.core.exceptions.
"""

import pytest

from resume_customizer.core.exceptions import (
    AIServiceError,
    DatabaseError,
    FileNotFoundError,
    GenerationError,
    ParseError,
    ResourceNotFoundError,
    ResumeCustomizerError,
    ValidationError,
)


class TestResumeCustomizerError:
    """Tests for the base ResumeCustomizerError class."""

    def test_init_message_only(self):
        err = ResumeCustomizerError("something went wrong")
        assert err.message == "something went wrong"
        assert err.suggestion is None
        assert str(err) == "something went wrong"

    def test_init_with_suggestion(self):
        err = ResumeCustomizerError("bad input", suggestion="try again")
        assert err.message == "bad input"
        assert err.suggestion == "try again"

    def test_is_exception(self):
        with pytest.raises(ResumeCustomizerError):
            raise ResumeCustomizerError("test")

    def test_to_dict_without_suggestion(self):
        err = ResumeCustomizerError("oops")
        d = err.to_dict()
        assert d == {"error": "oops"}
        assert "suggestion" not in d

    def test_to_dict_with_suggestion(self):
        err = ResumeCustomizerError("oops", suggestion="fix it")
        d = err.to_dict()
        assert d["error"] == "oops"
        assert d["suggestion"] == "fix it"


class TestFileNotFoundError:
    """Tests for FileNotFoundError."""

    def test_init(self):
        err = FileNotFoundError("/some/path.md")
        assert "/some/path.md" in err.message
        assert err.file_path == "/some/path.md"
        assert err.suggestion is not None

    def test_is_resume_customizer_error(self):
        err = FileNotFoundError("/path")
        assert isinstance(err, ResumeCustomizerError)

    def test_raises_as_exception(self):
        with pytest.raises(FileNotFoundError):
            raise FileNotFoundError("/missing.md")

    def test_suggestion_present(self):
        err = FileNotFoundError("/some/file.md")
        assert "check" in err.suggestion.lower() or "path" in err.suggestion.lower()


class TestParseError:
    """Tests for ParseError."""

    def test_init_without_details(self):
        err = ParseError("/resume.md")
        assert "/resume.md" in err.message
        assert err.file_path == "/resume.md"
        assert err.suggestion is not None

    def test_init_with_details(self):
        err = ParseError("/resume.md", details="missing header")
        assert "/resume.md" in err.message
        assert "missing header" in err.message

    def test_is_resume_customizer_error(self):
        assert isinstance(ParseError("/f"), ResumeCustomizerError)

    def test_suggestion_references_template(self):
        err = ParseError("/x.md")
        assert "template" in err.suggestion.lower() or "format" in err.suggestion.lower()


class TestValidationError:
    """Tests for ValidationError."""

    def test_init_basic(self):
        err = ValidationError("file_path", "cannot be empty")
        assert "file_path" in err.message
        assert "cannot be empty" in err.message
        assert err.field == "file_path"

    def test_init_with_custom_suggestion(self):
        err = ValidationError("age", "must be positive", suggestion="enter a number > 0")
        assert err.suggestion == "enter a number > 0"

    def test_default_suggestion_references_field(self):
        err = ValidationError("email", "invalid format")
        assert "email" in err.suggestion

    def test_is_resume_customizer_error(self):
        assert isinstance(ValidationError("x", "y"), ResumeCustomizerError)


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError."""

    def test_init(self):
        err = ResourceNotFoundError("profile", "profile-abc123")
        assert "profile" in err.message.lower()
        assert "profile-abc123" in err.message
        assert err.resource_type == "profile"
        assert err.resource_id == "profile-abc123"

    def test_suggestion_references_resource_type(self):
        err = ResourceNotFoundError("job", "job-xyz")
        assert "job" in err.suggestion.lower()

    def test_capitalizes_resource_type_in_message(self):
        err = ResourceNotFoundError("profile", "p-1")
        assert "Profile" in err.message

    def test_is_resume_customizer_error(self):
        assert isinstance(ResourceNotFoundError("match", "m-1"), ResumeCustomizerError)


class TestAIServiceError:
    """Tests for AIServiceError."""

    def test_init_without_details(self):
        err = AIServiceError("rate limit exceeded")
        assert "rate limit exceeded" in err.message
        assert err.suggestion is not None

    def test_init_with_details(self):
        err = AIServiceError("connection failed", details="timeout after 30s")
        assert "connection failed" in err.message
        assert "timeout after 30s" in err.message

    def test_suggestion_mentions_api(self):
        err = AIServiceError("error")
        assert "api" in err.suggestion.lower() or "key" in err.suggestion.lower()

    def test_is_resume_customizer_error(self):
        assert isinstance(AIServiceError("x"), ResumeCustomizerError)


class TestGenerationError:
    """Tests for GenerationError."""

    def test_init_without_details(self):
        err = GenerationError("PDF")
        assert "PDF" in err.message
        assert err.format_type == "PDF"

    def test_init_with_details(self):
        err = GenerationError("DOCX", details="template not found")
        assert "DOCX" in err.message
        assert "template not found" in err.message

    def test_suggestion_references_format(self):
        err = GenerationError("PDF")
        assert "PDF" in err.suggestion

    def test_is_resume_customizer_error(self):
        assert isinstance(GenerationError("PDF"), ResumeCustomizerError)


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_init_without_details(self):
        err = DatabaseError("insert")
        assert "insert" in err.message
        assert err.operation == "insert"

    def test_init_with_details(self):
        err = DatabaseError("query", details="table does not exist")
        assert "query" in err.message
        assert "table does not exist" in err.message

    def test_suggestion_mentions_database(self):
        err = DatabaseError("delete")
        assert "database" in err.suggestion.lower()

    def test_is_resume_customizer_error(self):
        assert isinstance(DatabaseError("op"), ResumeCustomizerError)
