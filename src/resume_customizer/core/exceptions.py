"""
Custom exceptions for Resume Customizer.

This module defines a hierarchy of exceptions for better error handling
and more informative error messages.
"""


class ResumeCustomizerError(Exception):
    """Base exception for all Resume Customizer errors."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Error message describing what went wrong
            suggestion: Optional suggestion for how to fix the error
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        """Convert exception to dictionary for API responses."""
        result = {"error": self.message}
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class FileNotFoundError(ResumeCustomizerError):
    """Raised when a required file is not found."""

    def __init__(self, file_path: str) -> None:
        """
        Initialize the exception.

        Args:
            file_path: Path to the missing file
        """
        super().__init__(
            message=f"File not found: {file_path}",
            suggestion="Please check that the file path is correct and the file exists.",
        )
        self.file_path = file_path


class ParseError(ResumeCustomizerError):
    """Raised when parsing a file fails."""

    def __init__(self, file_path: str, details: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            file_path: Path to the file that failed to parse
            details: Optional details about the parse error
        """
        message = f"Failed to parse file: {file_path}"
        if details:
            message += f" - {details}"

        super().__init__(
            message=message,
            suggestion="Please check that the file is in the correct format. "
            "See docs/resume_template.md or docs/job_template.md for examples.",
        )
        self.file_path = file_path


class ValidationError(ResumeCustomizerError):
    """Raised when validation fails."""

    def __init__(self, field: str, message: str, suggestion: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            field: Name of the field that failed validation
            message: Description of the validation failure
            suggestion: Optional suggestion for fixing the issue
        """
        super().__init__(
            message=f"Validation error for '{field}': {message}",
            suggestion=suggestion
            or f"Please provide a valid value for '{field}' and try again.",
        )
        self.field = field


class ResourceNotFoundError(ResumeCustomizerError):
    """Raised when a required resource (profile, job, match) is not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        """
        Initialize the exception.

        Args:
            resource_type: Type of resource (e.g., 'profile', 'job', 'match')
            resource_id: ID of the missing resource
        """
        super().__init__(
            message=f"{resource_type.capitalize()} not found: {resource_id}",
            suggestion=f"Please load the {resource_type} first using the "
            f"appropriate tool (e.g., load_user_profile or load_job_description).",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class AIServiceError(ResumeCustomizerError):
    """Raised when AI service operations fail."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            message: Description of the AI service error
            details: Optional additional details
        """
        full_message = f"AI service error: {message}"
        if details:
            full_message += f" - {details}"

        super().__init__(
            message=full_message,
            suggestion="The AI service may be temporarily unavailable. "
            "Please try again in a moment. If the problem persists, "
            "check your API key and network connection.",
        )


class GenerationError(ResumeCustomizerError):
    """Raised when document generation fails."""

    def __init__(self, format_type: str, details: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            format_type: Type of document being generated (e.g., 'PDF', 'DOCX')
            details: Optional details about the error
        """
        message = f"Failed to generate {format_type} document"
        if details:
            message += f": {details}"

        super().__init__(
            message=message,
            suggestion=f"Please check that the template is valid and all required "
            f"dependencies for {format_type} generation are installed.",
        )
        self.format_type = format_type


class DatabaseError(ResumeCustomizerError):
    """Raised when database operations fail."""

    def __init__(self, operation: str, details: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            operation: The database operation that failed
            details: Optional details about the error
        """
        message = f"Database {operation} failed"
        if details:
            message += f": {details}"

        super().__init__(
            message=message,
            suggestion="The database may be corrupted or locked. "
            "Try closing other applications that might be using the database.",
        )
        self.operation = operation
