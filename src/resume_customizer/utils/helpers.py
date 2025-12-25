"""
Utility helper functions for Resume Customizer MCP Server.

This module provides common utility functions used throughout the application.
"""

import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID (e.g., 'profile', 'job', 'match')

    Returns:
        Unique ID string

    Example:
        >>> generate_id('profile')
        'profile-a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}-{unique_id}" if prefix else unique_id


def get_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format.

    Returns:
        ISO formatted timestamp string

    Example:
        >>> get_timestamp()
        '2025-12-25T10:30:00Z'
    """
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_string(text: str) -> str:
    """
    Generate SHA256 hash of a string.

    Args:
        text: String to hash

    Returns:
        Hexadecimal hash string

    Example:
        >>> hash_string("hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    return hashlib.sha256(text.encode()).hexdigest()


def safe_filename(filename: str, max_length: int = 200) -> str:
    """
    Create a safe filename by removing/replacing invalid characters.

    Args:
        filename: Original filename
        max_length: Maximum length for the filename

    Returns:
        Safe filename string

    Example:
        >>> safe_filename("Resume: John Doe (2025).pdf")
        'Resume_John_Doe_2025.pdf'
    """
    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, "_")

    # Replace multiple underscores with single
    while "__" in safe_name:
        safe_name = safe_name.replace("__", "_")

    # Trim to max length
    if len(safe_name) > max_length:
        name, ext = Path(safe_name).stem, Path(safe_name).suffix
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext

    return safe_name.strip("_")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted size string

    Example:
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated

    Returns:
        Truncated text

    Example:
        >>> truncate_text("This is a very long text", max_length=15)
        'This is a ve...'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def flatten_dict(
    nested_dict: dict[str, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        nested_dict: Dictionary to flatten
        parent_key: Parent key for nested items
        sep: Separator between keys

    Returns:
        Flattened dictionary

    Example:
        >>> flatten_dict({'a': {'b': 1, 'c': 2}, 'd': 3})
        {'a.b': 1, 'a.c': 2, 'd': 3}
    """
    items: list[tuple] = []
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary

    Example:
        >>> deep_merge({'a': 1, 'b': {'c': 2}}, {'b': {'d': 3}, 'e': 4})
        {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_json_file(file_path: Path) -> dict[str, Any]:
    """
    Load JSON file safely.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(file_path, encoding="utf-8") as f:
        result: dict[str, Any] = json.load(f)
        return result


def save_json_file(data: dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """
    Save dictionary to JSON file.

    Args:
        data: Dictionary to save
        file_path: Path to save file
        indent: JSON indentation level
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def parse_date_string(date_str: str) -> datetime | None:
    """
    Parse date string in various formats.

    Args:
        date_str: Date string (e.g., "2025-12", "December 2025", "Present")

    Returns:
        Parsed datetime object or None if parsing fails

    Example:
        >>> parse_date_string("2025-12")
        datetime.datetime(2025, 12, 1, 0, 0)
    """
    if date_str.lower() == "present":
        return datetime.now()

    # Try various formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%B %Y",  # December 2025
        "%b %Y",  # Dec 2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None
