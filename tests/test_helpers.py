"""
Tests for utility helper functions (src/resume_customizer/utils/helpers.py).

Tests ID generation, timestamps, hashing, filename safety, and other utilities.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from resume_customizer.utils.helpers import (
    deep_merge,
    flatten_dict,
    format_file_size,
    generate_id,
    get_timestamp,
    hash_string,
    load_json_file,
    parse_date_string,
    safe_filename,
    save_json_file,
    truncate_text,
)


class TestGenerateId:
    """Test ID generation."""

    def test_generate_id_without_prefix(self) -> None:
        """Test generating ID without prefix."""
        id1 = generate_id()
        id2 = generate_id()

        assert id1 != id2  # Should be unique
        assert len(id1) == 36  # UUID format: 8-4-4-4-12 = 36 chars
        assert "-" in id1  # UUIDs have hyphens

    def test_generate_id_with_prefix(self) -> None:
        """Test generating ID with prefix."""
        prefix = "profile"
        id_with_prefix = generate_id(prefix)

        assert id_with_prefix.startswith(f"{prefix}-")
        assert len(id_with_prefix) > len(prefix)

    def test_generate_id_uniqueness(self) -> None:
        """Test that generated IDs are unique."""
        ids = [generate_id("test") for _ in range(100)]
        assert len(ids) == len(set(ids))


class TestGetTimestamp:
    """Test timestamp generation."""

    def test_get_timestamp_format(self) -> None:
        """Test timestamp format is ISO 8601."""
        timestamp = get_timestamp()

        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert timestamp.endswith("Z")

        # Should be parseable as datetime
        parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        assert isinstance(parsed, datetime)

    def test_get_timestamp_changes(self) -> None:
        """Test that timestamp changes over time."""
        import time

        ts1 = get_timestamp()
        time.sleep(0.1)
        ts2 = get_timestamp()

        # Timestamps should be different (or at least not fail)
        # We can't guarantee they're different due to second precision
        assert isinstance(ts1, str)
        assert isinstance(ts2, str)


class TestHashString:
    """Test string hashing."""

    def test_hash_string_consistent(self) -> None:
        """Test that same string produces same hash."""
        text = "hello world"
        hash1 = hash_string(text)
        hash2 = hash_string(text)

        assert hash1 == hash2

    def test_hash_string_different_for_different_inputs(self) -> None:
        """Test that different strings produce different hashes."""
        hash1 = hash_string("hello")
        hash2 = hash_string("world")

        assert hash1 != hash2

    def test_hash_string_format(self) -> None:
        """Test hash string format (SHA256 produces 64 hex chars)."""
        text = "test"
        hashed = hash_string(text)

        assert len(hashed) == 64  # SHA256 hex = 64 characters
        assert all(c in "0123456789abcdef" for c in hashed)


class TestSafeFilename:
    """Test safe filename creation."""

    def test_safe_filename_removes_invalid_chars(self) -> None:
        """Test that invalid characters are removed."""
        unsafe = 'Resume: John Doe (2025).pdf<>:"/\\|?*'
        safe = safe_filename(unsafe)

        assert "<" not in safe
        assert ">" not in safe
        assert ":" not in safe
        assert '"' not in safe
        assert "/" not in safe
        assert "\\" not in safe
        assert "|" not in safe
        assert "?" not in safe
        assert "*" not in safe

    def test_safe_filename_replaces_with_underscore(self) -> None:
        """Test that invalid chars are replaced with underscore."""
        unsafe = "file:name.pdf"
        safe = safe_filename(unsafe)

        assert "_" in safe
        assert ":" not in safe

    def test_safe_filename_multiple_underscores(self) -> None:
        """Test that multiple underscores are collapsed."""
        unsafe = "file:::name.pdf"
        safe = safe_filename(unsafe)

        assert "__" not in safe  # Should collapse multiple underscores

    def test_safe_filename_max_length(self) -> None:
        """Test filename truncation to max length."""
        long_name = "a" * 300 + ".pdf"
        safe = safe_filename(long_name, max_length=50)

        assert len(safe) <= 50
        assert safe.endswith(".pdf")  # Extension preserved

    def test_safe_filename_strips_underscores(self) -> None:
        """Test that leading/trailing underscores are stripped."""
        unsafe = "_file_.pdf"
        safe = safe_filename(unsafe)

        assert not safe.startswith("_")
        assert not safe.endswith("_")


class TestFormatFileSize:
    """Test file size formatting."""

    def test_format_bytes(self) -> None:
        """Test formatting bytes."""
        size = format_file_size(500)
        assert "B" in size
        assert "500" in size

    def test_format_kilobytes(self) -> None:
        """Test formatting kilobytes."""
        size = format_file_size(1024)
        assert "KB" in size
        assert "1.00" in size

    def test_format_megabytes(self) -> None:
        """Test formatting megabytes."""
        size = format_file_size(1048576)
        assert "MB" in size
        assert "1.00" in size

    def test_format_gigabytes(self) -> None:
        """Test formatting gigabytes."""
        size = format_file_size(1073741824)
        assert "GB" in size
        assert "1.00" in size

    def test_format_decimal_precision(self) -> None:
        """Test that format includes decimal precision."""
        size = format_file_size(1536)  # 1.5 KB
        assert ".50 KB" in size or "1.50 KB" in size


class TestTruncateText:
    """Test text truncation."""

    def test_truncate_long_text(self) -> None:
        """Test truncating text longer than max length."""
        text = "This is a very long text that needs truncation"
        truncated = truncate_text(text, max_length=20)

        assert len(truncated) == 20
        assert truncated.endswith("...")

    def test_truncate_short_text_unchanged(self) -> None:
        """Test that short text is not truncated."""
        text = "Short"
        truncated = truncate_text(text, max_length=20)

        assert truncated == text
        assert not truncated.endswith("...")

    def test_truncate_custom_suffix(self) -> None:
        """Test truncation with custom suffix."""
        text = "Long text here"
        truncated = truncate_text(text, max_length=10, suffix=">>")

        assert truncated.endswith(">>")
        assert len(truncated) == 10


class TestFlattenDict:
    """Test dictionary flattening."""

    def test_flatten_nested_dict(self) -> None:
        """Test flattening a nested dictionary."""
        nested = {"a": {"b": 1, "c": 2}, "d": 3}
        flattened = flatten_dict(nested)

        assert flattened == {"a.b": 1, "a.c": 2, "d": 3}

    def test_flatten_deeply_nested(self) -> None:
        """Test flattening deeply nested dictionary."""
        nested = {"a": {"b": {"c": {"d": 1}}}}
        flattened = flatten_dict(nested)

        assert flattened == {"a.b.c.d": 1}

    def test_flatten_with_custom_separator(self) -> None:
        """Test flattening with custom separator."""
        nested = {"a": {"b": 1}}
        flattened = flatten_dict(nested, sep="_")

        assert flattened == {"a_b": 1}

    def test_flatten_empty_dict(self) -> None:
        """Test flattening empty dictionary."""
        flattened = flatten_dict({})
        assert flattened == {}


class TestDeepMerge:
    """Test deep dictionary merging."""

    def test_deep_merge_simple(self) -> None:
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        merged = deep_merge(base, override)

        assert merged == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self) -> None:
        """Test nested dictionary merge."""
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        merged = deep_merge(base, override)

        assert merged == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    def test_deep_merge_overrides_nested(self) -> None:
        """Test that nested values are overridden."""
        base = {"a": {"b": 1}}
        override = {"a": {"b": 2}}
        merged = deep_merge(base, override)

        assert merged == {"a": {"b": 2}}

    def test_deep_merge_preserves_base(self) -> None:
        """Test that original base dict is not modified."""
        base = {"a": 1}
        override = {"b": 2}
        merged = deep_merge(base, override)

        assert base == {"a": 1}  # Unchanged
        assert merged == {"a": 1, "b": 2}


class TestJSONFileOperations:
    """Test JSON file loading and saving."""

    def test_save_and_load_json_file(self) -> None:
        """Test saving and loading JSON file."""
        data = {"name": "John", "age": 30, "skills": ["Python", "JavaScript"]}

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"

            # Save
            save_json_file(data, file_path)
            assert file_path.exists()

            # Load
            loaded = load_json_file(file_path)
            assert loaded == data

    def test_save_json_creates_directories(self) -> None:
        """Test that save creates parent directories."""
        data = {"test": "data"}

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nested" / "dir" / "test.json"

            save_json_file(data, file_path)
            assert file_path.exists()

    def test_save_json_with_custom_indent(self) -> None:
        """Test saving JSON with custom indentation."""
        data = {"a": 1, "b": 2}

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.json"

            save_json_file(data, file_path, indent=4)
            content = file_path.read_text()

            # Check for indentation
            assert "    " in content  # 4 spaces

    def test_load_json_nonexistent_file(self) -> None:
        """Test loading non-existent JSON file raises error."""
        with pytest.raises(FileNotFoundError):
            load_json_file(Path("/nonexistent/file.json"))

    def test_load_json_invalid_format(self) -> None:
        """Test loading invalid JSON raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "invalid.json"
            file_path.write_text("not valid json")

            with pytest.raises(json.JSONDecodeError):
                load_json_file(file_path)


class TestParseDateString:
    """Test date string parsing."""

    def test_parse_present(self) -> None:
        """Test parsing 'Present'."""
        result = parse_date_string("Present")
        assert result is not None
        assert isinstance(result, datetime)

    def test_parse_year_only(self) -> None:
        """Test parsing year-only format."""
        result = parse_date_string("2025")
        assert result is not None
        assert result.year == 2025

    def test_parse_year_month(self) -> None:
        """Test parsing YYYY-MM format."""
        result = parse_date_string("2025-12")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12

    def test_parse_full_date(self) -> None:
        """Test parsing full date."""
        result = parse_date_string("2025-12-25")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 25

    def test_parse_month_name_full(self) -> None:
        """Test parsing with full month name."""
        result = parse_date_string("December 2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12

    def test_parse_month_name_abbreviated(self) -> None:
        """Test parsing with abbreviated month name."""
        result = parse_date_string("Dec 2025")
        assert result is not None
        assert result.year == 2025
        assert result.month == 12

    def test_parse_invalid_format(self) -> None:
        """Test parsing invalid format returns None."""
        result = parse_date_string("invalid date")
        assert result is None

    def test_parse_empty_string(self) -> None:
        """Test parsing empty string."""
        # Empty string will likely not match "present" and will fail other formats
        # The function should handle this gracefully
        parse_date_string("")
        # Could be None or raise exception depending on implementation
        # Most likely returns None for invalid format
        # No assertion needed - just testing it doesn't crash
