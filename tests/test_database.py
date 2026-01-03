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

    @pytest.fixture(autouse=True)
    def setup_foreign_keys(self, database: CustomizationDatabase) -> None:
        """Set up profile and job for foreign key constraints."""
        database.insert_profile(
            profile_id="profile-456",
            name="John Doe",
            email="john@example.com",
            full_data={"name": "John Doe"},
        )
        database.insert_job(
            job_id="job-789",
            title="Senior Software Engineer",
            company="TechCorp",
            full_data={"title": "Engineer"},
        )
        # For test_insert_without_metadata
        database.insert_profile(
            profile_id="profile-1",
            name="Jane Smith",
            email="jane@example.com",
            full_data={"name": "Jane Smith"},
        )
        database.insert_job(
            job_id="job-1",
            title="Developer",
            company="StartupXYZ",
            full_data={"title": "Developer"},
        )

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
        # Set up required profiles and jobs
        database.insert_profile(
            profile_id="profile-456",
            name="John Doe",
            email="john@example.com",
            full_data={"name": "John Doe"},
        )
        database.insert_job(
            job_id="job-789",
            title="Senior Software Engineer",
            company="TechCorp",
            full_data={"title": "Engineer"},
        )

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

    @pytest.fixture(autouse=True)
    def setup_foreign_keys(self, database: CustomizationDatabase) -> None:
        """Set up profile and job for foreign key constraints."""
        database.insert_profile(
            profile_id="profile-456",
            name="John Doe",
            email="john@example.com",
            full_data={"name": "John Doe"},
        )
        database.insert_job(
            job_id="job-789",
            title="Senior Software Engineer",
            company="TechCorp",
            full_data={"title": "Engineer"},
        )

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

    @pytest.fixture(autouse=True)
    def setup_foreign_keys(self, database: CustomizationDatabase) -> None:
        """Set up profile and job for foreign key constraints."""
        database.insert_profile(
            profile_id="profile-456",
            name="John Doe",
            email="john@example.com",
            full_data={"name": "John Doe"},
        )
        database.insert_job(
            job_id="job-789",
            title="Senior Software Engineer",
            company="TechCorp",
            full_data={"title": "Engineer"},
        )

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
            # Set up profile and job first
            db.insert_profile(
                profile_id="profile-1",
                name="Test User",
                email="test@example.com",
                full_data={"name": "Test User"},
            )
            db.insert_job(
                job_id="job-1",
                title="Engineer",
                company="TestCorp",
                full_data={"title": "Engineer"},
            )
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


class TestProfileOperations:
    """Test profile CRUD operations."""

    @pytest.fixture
    def sample_profile_data(self) -> dict:
        """Sample profile data for testing."""
        return {
            "profile_id": "profile-abc123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0100",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
            "website": "https://johndoe.dev",
            "summary": "Experienced software engineer",
            "skills_count": 25,
            "experiences_count": 3,
            "education_count": 1,
            "certifications_count": 2,
            "full_data": {"name": "John Doe", "skills": []},
        }

    def test_insert_profile(
        self, database: CustomizationDatabase, sample_profile_data: dict
    ) -> None:
        """Test inserting a profile."""
        database.insert_profile(**sample_profile_data)

        result = database.get_profile("profile-abc123")
        assert result is not None
        assert result["name"] == "John Doe"
        assert result["email"] == "john.doe@example.com"
        assert result["skills_count"] == 25
        assert result["full_data"]["name"] == "John Doe"

    def test_insert_profile_with_minimal_data(
        self, database: CustomizationDatabase
    ) -> None:
        """Test inserting profile with only required fields."""
        database.insert_profile(
            profile_id="profile-min",
            name="Jane Smith",
            email="jane@example.com",
            full_data={"name": "Jane Smith"},
        )

        result = database.get_profile("profile-min")
        assert result is not None
        assert result["phone"] is None
        assert result["linkedin"] is None

    def test_get_nonexistent_profile(self, database: CustomizationDatabase) -> None:
        """Test getting a non-existent profile."""
        result = database.get_profile("nonexistent")
        assert result is None

    def test_update_profile(
        self, database: CustomizationDatabase, sample_profile_data: dict
    ) -> None:
        """Test updating a profile."""
        database.insert_profile(**sample_profile_data)

        # Update profile
        updated = database.update_profile(
            profile_id="profile-abc123",
            full_data={"name": "John Doe Updated", "skills": ["Python"]},
            name="John Doe Updated",
            skills_count=30,
        )

        assert updated is True

        result = database.get_profile("profile-abc123")
        assert result is not None
        assert result["name"] == "John Doe Updated"
        assert result["skills_count"] == 30
        assert result["email"] == "john.doe@example.com"  # Unchanged
        assert result["created_at"] != result["updated_at"]  # updated_at changed

    def test_update_nonexistent_profile(self, database: CustomizationDatabase) -> None:
        """Test updating a non-existent profile."""
        updated = database.update_profile(
            profile_id="nonexistent",
            full_data={"name": "Nobody"},
        )
        assert updated is False

    def test_delete_profile(
        self, database: CustomizationDatabase, sample_profile_data: dict
    ) -> None:
        """Test deleting a profile."""
        database.insert_profile(**sample_profile_data)
        assert database.get_profile("profile-abc123") is not None

        deleted = database.delete_profile("profile-abc123")
        assert deleted is True
        assert database.get_profile("profile-abc123") is None

    def test_delete_nonexistent_profile(self, database: CustomizationDatabase) -> None:
        """Test deleting a non-existent profile."""
        deleted = database.delete_profile("nonexistent")
        assert deleted is False


class TestJobOperations:
    """Test job CRUD operations."""

    @pytest.fixture
    def sample_job_data(self) -> dict:
        """Sample job data for testing."""
        return {
            "job_id": "job-xyz789",
            "title": "Senior Software Engineer",
            "company": "TechCorp Inc.",
            "location": "Remote",
            "job_type": "Full-time",
            "experience_level": "Senior",
            "salary_range": "$150k-$200k",
            "required_skills_count": 8,
            "preferred_skills_count": 5,
            "full_data": {"title": "Senior Software Engineer", "requirements": {}},
        }

    def test_insert_job(
        self, database: CustomizationDatabase, sample_job_data: dict
    ) -> None:
        """Test inserting a job."""
        database.insert_job(**sample_job_data)

        result = database.get_job("job-xyz789")
        assert result is not None
        assert result["title"] == "Senior Software Engineer"
        assert result["company"] == "TechCorp Inc."
        assert result["required_skills_count"] == 8
        assert result["full_data"]["title"] == "Senior Software Engineer"

    def test_insert_job_with_minimal_data(
        self, database: CustomizationDatabase
    ) -> None:
        """Test inserting job with only required fields."""
        database.insert_job(
            job_id="job-min",
            title="Developer",
            company="StartupXYZ",
            full_data={"title": "Developer", "company": "StartupXYZ"},
        )

        result = database.get_job("job-min")
        assert result is not None
        assert result["location"] is None
        assert result["salary_range"] is None

    def test_get_nonexistent_job(self, database: CustomizationDatabase) -> None:
        """Test getting a non-existent job."""
        result = database.get_job("nonexistent")
        assert result is None

    def test_update_job(
        self, database: CustomizationDatabase, sample_job_data: dict
    ) -> None:
        """Test updating a job."""
        database.insert_job(**sample_job_data)

        # Update job
        updated = database.update_job(
            job_id="job-xyz789",
            full_data={"title": "Staff Engineer", "company": "TechCorp Inc."},
            title="Staff Engineer",
            required_skills_count=10,
        )

        assert updated is True

        result = database.get_job("job-xyz789")
        assert result is not None
        assert result["title"] == "Staff Engineer"
        assert result["required_skills_count"] == 10
        assert result["company"] == "TechCorp Inc."  # Unchanged
        assert result["created_at"] != result["updated_at"]

    def test_update_nonexistent_job(self, database: CustomizationDatabase) -> None:
        """Test updating a non-existent job."""
        updated = database.update_job(
            job_id="nonexistent",
            full_data={"title": "None"},
        )
        assert updated is False

    def test_delete_job(
        self, database: CustomizationDatabase, sample_job_data: dict
    ) -> None:
        """Test deleting a job."""
        database.insert_job(**sample_job_data)
        assert database.get_job("job-xyz789") is not None

        deleted = database.delete_job("job-xyz789")
        assert deleted is True
        assert database.get_job("job-xyz789") is None

    def test_delete_nonexistent_job(self, database: CustomizationDatabase) -> None:
        """Test deleting a non-existent job."""
        deleted = database.delete_job("nonexistent")
        assert deleted is False


class TestMatchOperations:
    """Test match result CRUD operations."""

    @pytest.fixture
    def sample_match_data(self) -> dict:
        """Sample match result data for testing."""
        return {
            "match_id": "match-def456",
            "profile_id": "profile-abc123",
            "job_id": "job-xyz789",
            "overall_score": 85,
            "technical_score": 90,
            "experience_score": 80,
            "domain_score": 85,
            "keyword_coverage": 75,
            "matched_skills_count": 12,
            "missing_skills_count": 3,
            "full_data": {
                "overall_score": 85,
                "breakdown": {},
                "matched_skills": [],
            },
        }

    @pytest.fixture(autouse=True)
    def setup_foreign_keys(
        self, database: CustomizationDatabase
    ) -> None:
        """Set up profile and job for foreign key constraints."""
        database.insert_profile(
            profile_id="profile-abc123",
            name="John Doe",
            email="john@example.com",
            full_data={"name": "John Doe"},
        )
        database.insert_job(
            job_id="job-xyz789",
            title="Engineer",
            company="TechCorp",
            full_data={"title": "Engineer"},
        )

    def test_insert_match(
        self, database: CustomizationDatabase, sample_match_data: dict
    ) -> None:
        """Test inserting a match result."""
        database.insert_match(**sample_match_data)

        result = database.get_match("match-def456")
        assert result is not None
        assert result["overall_score"] == 85
        assert result["technical_score"] == 90
        assert result["matched_skills_count"] == 12
        assert result["full_data"]["overall_score"] == 85

    def test_get_nonexistent_match(self, database: CustomizationDatabase) -> None:
        """Test getting a non-existent match."""
        result = database.get_match("nonexistent")
        assert result is None

    def test_delete_match(
        self, database: CustomizationDatabase, sample_match_data: dict
    ) -> None:
        """Test deleting a match result."""
        database.insert_match(**sample_match_data)
        assert database.get_match("match-def456") is not None

        deleted = database.delete_match("match-def456")
        assert deleted is True
        assert database.get_match("match-def456") is None

    def test_delete_nonexistent_match(self, database: CustomizationDatabase) -> None:
        """Test deleting a non-existent match."""
        deleted = database.delete_match("nonexistent")
        assert deleted is False


class TestForeignKeyConstraints:
    """Test foreign key constraints."""

    def test_foreign_keys_enabled(self, database: CustomizationDatabase) -> None:
        """Test that foreign keys are enabled."""
        cursor = database.conn.cursor()  # type: ignore
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1  # Foreign keys should be ON

    def test_cannot_delete_profile_with_customization(
        self, database: CustomizationDatabase
    ) -> None:
        """Test that profile with customizations cannot be deleted due to FK constraint."""
        import sqlite3

        # Insert profile, job, customization
        database.insert_profile(
            profile_id="profile-fk",
            name="Test User",
            email="test@example.com",
            full_data={"name": "Test"},
        )
        database.insert_job(
            job_id="job-fk",
            title="Engineer",
            company="Corp",
            full_data={"title": "Eng"},
        )
        database.insert_customization(
            customization_id="custom-fk",
            profile_id="profile-fk",
            job_id="job-fk",
            profile_name="Test User",
            job_title="Engineer",
            company="Corp",
            overall_score=80,
            template="modern",
            created_at="2024-01-15T10:00:00",
        )

        # Try to delete profile with customization - should fail with FK constraint
        with pytest.raises(sqlite3.IntegrityError):
            database.delete_profile("profile-fk")

        # Customization should still exist (FK prevented the delete)
        custom = database.get_customization_by_id("custom-fk")
        assert custom is not None
