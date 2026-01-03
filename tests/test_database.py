"""
Tests for database persistence (Phase 6.2).

Tests the CustomizationDatabase for storing and retrieving
customization history.
"""

import os
from pathlib import Path

import pytest

from resume_customizer.storage.database import CustomizationDatabase


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Create a temporary database file path."""
    return tmp_path / "test_customizations.db"


@pytest.fixture
def database(test_db_path: Path) -> CustomizationDatabase:
    """Create a test database instance."""
    db = CustomizationDatabase(test_db_path)
    yield db
    db.close()
    # Clean up
    if test_db_path.exists():
        os.remove(test_db_path)


@pytest.fixture
def sample_customization() -> dict:
    """Sample customization data for testing."""
    return {
        "customization_id": "custom-123",
        "profile_id": "profile-456",
        "job_id": "job-789",
        "profile_name": "John Doe",
        "job_title": "Senior Software Engineer",
        "company": "TechCorp",
        "overall_score": 85,
        "template": "modern",
        "created_at": "2024-01-15T10:30:00",
        "metadata": {
            "changes_count": 5,
            "achievements_reordered": 3,
            "skills_reordered": 2,
        },
    }


class TestDatabaseInitialization:
    """Test database initialization."""

    def test_creates_database_file(self, test_db_path: Path) -> None:
        """Test that database file is created."""
        assert not test_db_path.exists()
        db = CustomizationDatabase(test_db_path)
        assert test_db_path.exists()
        db.close()

    def test_creates_tables_and_indexes(self, database: CustomizationDatabase) -> None:
        """Test that tables and indexes are created."""
        cursor = database.conn.cursor()  # type: ignore

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='customizations'"
        )
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_company" in indexes
        assert "idx_created_at" in indexes
        assert "idx_profile_id" in indexes
        assert "idx_job_id" in indexes


class TestInsertCustomization:
    """Test inserting customization records."""

    def test_insert_customization(
        self, database: CustomizationDatabase, sample_customization: dict
    ) -> None:
        """Test inserting a customization."""
        database.insert_customization(**sample_customization)

        # Verify it was inserted
        result = database.get_customization_by_id("custom-123")
        assert result is not None
        assert result["customization_id"] == "custom-123"
        assert result["profile_name"] == "John Doe"
        assert result["company"] == "TechCorp"
        assert result["overall_score"] == 85

    def test_insert_without_metadata(self, database: CustomizationDatabase) -> None:
        """Test inserting without metadata."""
        database.insert_customization(
            customization_id="custom-no-meta",
            profile_id="profile-1",
            job_id="job-1",
            profile_name="Jane Smith",
            job_title="Developer",
            company="StartupXYZ",
            overall_score=70,
            template="classic",
            created_at="2024-01-16T12:00:00",
        )

        result = database.get_customization_by_id("custom-no-meta")
        assert result is not None
        assert result["metadata"] is None


class TestGetCustomizations:
    """Test querying customizations."""

    @pytest.fixture(autouse=True)
    def setup_test_data(
        self, database: CustomizationDatabase, sample_customization: dict
    ) -> None:
        """Insert test data before each test."""
        # Insert multiple customizations with variations
        for i in range(5):
            custom = sample_customization.copy()
            custom["customization_id"] = f"custom-{i}"
            custom["company"] = f"Company{i % 2}"  # Alternate between Company0 and Company1
            custom["created_at"] = f"2024-01-{15 + i:02d}T10:00:00"
            custom["overall_score"] = 70 + i * 5
            database.insert_customization(**custom)

    def test_get_all_customizations(self, database: CustomizationDatabase) -> None:
        """Test getting all customizations."""
        results = database.get_customizations(limit=10)
        assert len(results) == 5

    def test_filter_by_company(self, database: CustomizationDatabase) -> None:
        """Test filtering by company name."""
        results = database.get_customizations(company="Company0")
        assert len(results) == 3  # Companies 0, 2, 4
        for result in results:
            assert "Company0" in result["company"]

    def test_filter_by_company_case_insensitive(
        self, database: CustomizationDatabase
    ) -> None:
        """Test company filter is case-insensitive."""
        results = database.get_customizations(company="company0")
        assert len(results) == 3

    def test_filter_by_date_range(self, database: CustomizationDatabase) -> None:
        """Test filtering by date range."""
        results = database.get_customizations(
            start_date="2024-01-16T00:00:00", end_date="2024-01-18T23:59:59"
        )
        # Should return customizations from Jan 16, 17, 18 (indices 1, 2, 3)
        assert len(results) == 3

    def test_limit_results(self, database: CustomizationDatabase) -> None:
        """Test limiting number of results."""
        results = database.get_customizations(limit=3)
        assert len(results) == 3

    def test_order_by_created_at(self, database: CustomizationDatabase) -> None:
        """Test ordering by created_at."""
        results = database.get_customizations(order_by="created_at", order_direction="ASC")
        dates = [r["created_at"] for r in results]
        assert dates == sorted(dates)

    def test_order_by_score(self, database: CustomizationDatabase) -> None:
        """Test ordering by overall_score."""
        results = database.get_customizations(
            order_by="overall_score", order_direction="DESC"
        )
        scores = [r["overall_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestGetCustomizationById:
    """Test getting a single customization."""

    def test_get_existing_customization(
        self, database: CustomizationDatabase, sample_customization: dict
    ) -> None:
        """Test getting an existing customization."""
        database.insert_customization(**sample_customization)
        result = database.get_customization_by_id("custom-123")

        assert result is not None
        assert result["customization_id"] == "custom-123"
        assert result["metadata"]["changes_count"] == 5

    def test_get_nonexistent_customization(self, database: CustomizationDatabase) -> None:
        """Test getting a non-existent customization."""
        result = database.get_customization_by_id("nonexistent")
        assert result is None


class TestDeleteCustomization:
    """Test deleting customizations."""

    def test_delete_existing_customization(
        self, database: CustomizationDatabase, sample_customization: dict
    ) -> None:
        """Test deleting an existing customization."""
        database.insert_customization(**sample_customization)
        assert database.get_customization_by_id("custom-123") is not None

        deleted = database.delete_customization("custom-123")
        assert deleted is True
        assert database.get_customization_by_id("custom-123") is None

    def test_delete_nonexistent_customization(
        self, database: CustomizationDatabase
    ) -> None:
        """Test deleting a non-existent customization."""
        deleted = database.delete_customization("nonexistent")
        assert deleted is False


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager(self, test_db_path: Path) -> None:
        """Test using database as context manager."""
        with CustomizationDatabase(test_db_path) as db:
            db.insert_customization(
                customization_id="ctx-test",
                profile_id="profile-1",
                job_id="job-1",
                profile_name="Test User",
                job_title="Engineer",
                company="TestCorp",
                overall_score=80,
                template="modern",
                created_at="2024-01-15T10:00:00",
            )

        # Verify database was closed
        with CustomizationDatabase(test_db_path) as db:
            result = db.get_customization_by_id("ctx-test")
            assert result is not None
