"""
Input validation utilities for MCP handlers.

This module provides validation functions for tool inputs to ensure
data integrity and provide helpful error messages.
"""

from pathlib import Path
from typing import Any

from resume_customizer.core.exceptions import ValidationError


def validate_file_path(file_path: str | None, param_name: str = "file_path") -> str:
    """
    Validate that a file path is provided and exists.

    Args:
        file_path: The file path to validate
        param_name: Name of the parameter (for error messages)

    Returns:
        The validated file path

    Raises:
        ValidationError: If file path is missing or invalid
    """
    if not file_path:
        raise ValidationError(
            field=param_name,
            message="File path is required",
            suggestion=f"Please provide a valid file path for '{param_name}'.",
        )

    if not isinstance(file_path, str):
        raise ValidationError(
            field=param_name,
            message=f"File path must be a string, got {type(file_path).__name__}",
        )

    # Check if path exists
    path = Path(file_path)
    if not path.exists():
        raise ValidationError(
            field=param_name,
            message=f"File does not exist: {file_path}",
            suggestion="Please check that the file path is correct and the file exists.",
        )

    if not path.is_file():
        raise ValidationError(
            field=param_name,
            message=f"Path is not a file: {file_path}",
            suggestion="Please provide a path to a file, not a directory.",
        )

    return file_path


def validate_id(
    id_value: str | None, param_name: str, resource_type: str | None = None
) -> str:
    """
    Validate that an ID is provided and non-empty.

    Args:
        id_value: The ID to validate
        param_name: Name of the parameter (for error messages)
        resource_type: Optional type of resource (for better error messages)

    Returns:
        The validated ID

    Raises:
        ValidationError: If ID is missing or invalid
    """
    if not id_value:
        suggestion = f"Please provide a valid {param_name}."
        if resource_type:
            suggestion = (
                f"Please load the {resource_type} first using the appropriate tool."
            )

        raise ValidationError(
            field=param_name,
            message=f"{param_name} is required",
            suggestion=suggestion,
        )

    if not isinstance(id_value, str):
        raise ValidationError(
            field=param_name,
            message=f"{param_name} must be a string, got {type(id_value).__name__}",
        )

    if not id_value.strip():
        raise ValidationError(
            field=param_name, message=f"{param_name} cannot be empty or whitespace"
        )

    return id_value


def validate_positive_integer(
    value: Any, param_name: str, min_value: int = 1, max_value: int | None = None
) -> int:
    """
    Validate that a value is a positive integer within range.

    Args:
        value: The value to validate
        param_name: Name of the parameter (for error messages)
        min_value: Minimum allowed value (default: 1)
        max_value: Optional maximum allowed value

    Returns:
        The validated integer

    Raises:
        ValidationError: If value is not a valid positive integer
    """
    if not isinstance(value, int):
        raise ValidationError(
            field=param_name,
            message=f"Must be an integer, got {type(value).__name__}",
        )

    if value < min_value:
        raise ValidationError(
            field=param_name,
            message=f"Must be at least {min_value}, got {value}",
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            field=param_name,
            message=f"Must be at most {max_value}, got {value}",
        )

    return value


def validate_enum(
    value: Any, param_name: str, allowed_values: list[str], case_sensitive: bool = False
) -> str:
    """
    Validate that a value is one of the allowed enum values.

    Args:
        value: The value to validate
        param_name: Name of the parameter (for error messages)
        allowed_values: List of allowed values
        case_sensitive: Whether comparison should be case-sensitive

    Returns:
        The validated value

    Raises:
        ValidationError: If value is not in allowed values
    """
    if not isinstance(value, str):
        raise ValidationError(
            field=param_name,
            message=f"Must be a string, got {type(value).__name__}",
        )

    compare_value = value if case_sensitive else value.lower()
    compare_allowed = (
        allowed_values
        if case_sensitive
        else [v.lower() for v in allowed_values]
    )

    if compare_value not in compare_allowed:
        raise ValidationError(
            field=param_name,
            message=f"Invalid value: '{value}'",
            suggestion=f"Allowed values are: {', '.join(allowed_values)}",
        )

    return value


def validate_output_formats(formats: Any) -> list[str]:
    """
    Validate output formats for document generation.

    Args:
        formats: The formats to validate

    Returns:
        The validated list of formats

    Raises:
        ValidationError: If formats are invalid
    """
    if not isinstance(formats, list):
        raise ValidationError(
            field="output_formats",
            message=f"Must be a list, got {type(formats).__name__}",
            suggestion="Please provide a list of formats, e.g., ['pdf', 'docx']",
        )

    if not formats:
        raise ValidationError(
            field="output_formats",
            message="At least one output format must be specified",
            suggestion="Allowed formats are: pdf, docx",
        )

    allowed_formats = ["pdf", "docx"]
    validated_formats = []

    for fmt in formats:
        if not isinstance(fmt, str):
            raise ValidationError(
                field="output_formats",
                message=f"Format must be a string, got {type(fmt).__name__}",
            )

        fmt_lower = fmt.lower()
        if fmt_lower not in allowed_formats:
            raise ValidationError(
                field="output_formats",
                message=f"Invalid format: '{fmt}'",
                suggestion=f"Allowed formats are: {', '.join(allowed_formats)}",
            )

        validated_formats.append(fmt_lower)

    return validated_formats


def validate_preferences(preferences: Any) -> dict[str, Any]:
    """
    Validate customization preferences.

    Args:
        preferences: The preferences dictionary to validate

    Returns:
        The validated preferences dictionary

    Raises:
        ValidationError: If preferences are invalid
    """
    if not isinstance(preferences, dict):
        raise ValidationError(
            field="preferences",
            message=f"Must be a dictionary, got {type(preferences).__name__}",
        )

    validated: dict[str, Any] = {}

    # Validate achievements_per_role
    if "achievements_per_role" in preferences:
        validated["achievements_per_role"] = validate_positive_integer(
            preferences["achievements_per_role"],
            "achievements_per_role",
            min_value=1,
            max_value=10,
        )

    # Validate max_skills
    if "max_skills" in preferences:
        validated["max_skills"] = validate_positive_integer(
            preferences["max_skills"], "max_skills", min_value=1, max_value=100
        )

    # Validate template
    if "template" in preferences:
        validated["template"] = validate_enum(
            preferences["template"],
            "template",
            ["modern", "classic", "minimal", "elegant", "ats_optimized"],
        )

    # Validate include_summary
    if "include_summary" in preferences:
        if not isinstance(preferences["include_summary"], bool):
            raise ValidationError(
                field="include_summary",
                message="Must be a boolean (true or false)",
            )
        validated["include_summary"] = preferences["include_summary"]

    return validated
