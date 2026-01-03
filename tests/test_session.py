"""
Tests for session management (Phase 7.2).

Tests the SessionManager for in-memory caching with TTL support,
automatic cleanup, and usage metrics.
"""

import time

import pytest

from resume_customizer.storage.session import SessionManager


@pytest.fixture
def session() -> SessionManager:
    """Create a SessionManager instance with short TTL for testing."""
    return SessionManager(default_ttl=1)  # 1 second TTL for testing


@pytest.fixture
def sample_profile() -> dict:
    """Sample profile data."""
    return {
        "profile_id": "profile-123",
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "SQL"],
    }


@pytest.fixture
def sample_job() -> dict:
    """Sample job data."""
    return {
        "job_id": "job-456",
        "title": "Software Engineer",
        "company": "TechCorp",
        "requirements": ["Python"],
    }


@pytest.fixture
def sample_match() -> dict:
    """Sample match result data."""
    return {
        "match_id": "match-789",
        "profile_id": "profile-123",
        "job_id": "job-456",
        "overall_score": 85,
    }


@pytest.fixture
def sample_customization() -> dict:
    """Sample customization data."""
    return {
        "customization_id": "custom-abc",
        "profile_id": "profile-123",
        "job_id": "job-456",
        "template": "modern",
    }


class TestSessionManagerInit:
    """Test SessionManager initialization."""

    def test_default_ttl(self) -> None:
        """Test initialization with default TTL."""
        session = SessionManager()
        assert session.default_ttl == 3600  # Default 1 hour

    def test_custom_ttl(self) -> None:
        """Test initialization with custom TTL."""
        session = SessionManager(default_ttl=7200)
        assert session.default_ttl == 7200


class TestProfileStorage:
    """Test profile storage and retrieval."""

    def test_set_and_get_profile(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test storing and retrieving a profile."""
        session.set_profile("profile-123", sample_profile)
        result = session.get_profile("profile-123")

        assert result is not None
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"

    def test_get_nonexistent_profile(self, session: SessionManager) -> None:
        """Test retrieving a non-existent profile."""
        result = session.get_profile("nonexistent")
        assert result is None

    def test_profile_expiration(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test profile expiration after TTL."""
        session.set_profile("profile-123", sample_profile)

        # Should be available immediately
        assert session.get_profile("profile-123") is not None

        # Wait for expiration (TTL is 1 second)
        time.sleep(1.1)

        # Should be expired now
        assert session.get_profile("profile-123") is None

    def test_profile_custom_ttl(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test profile retrieval with custom TTL."""
        session.set_profile("profile-123", sample_profile)

        # Wait for default TTL to pass
        time.sleep(1.1)

        # Should be expired with default TTL
        assert session.get_profile("profile-123") is None

        # Store again
        session.set_profile("profile-123", sample_profile)

        # Should still be available with longer TTL
        assert session.get_profile("profile-123", ttl=10) is not None


class TestJobStorage:
    """Test job storage and retrieval."""

    def test_set_and_get_job(self, session: SessionManager, sample_job: dict) -> None:
        """Test storing and retrieving a job."""
        session.set_job("job-456", sample_job)
        result = session.get_job("job-456")

        assert result is not None
        assert result["title"] == "Software Engineer"
        assert result["company"] == "TechCorp"

    def test_get_nonexistent_job(self, session: SessionManager) -> None:
        """Test retrieving a non-existent job."""
        result = session.get_job("nonexistent")
        assert result is None

    def test_job_expiration(self, session: SessionManager, sample_job: dict) -> None:
        """Test job expiration after TTL."""
        session.set_job("job-456", sample_job)
        assert session.get_job("job-456") is not None

        time.sleep(1.1)
        assert session.get_job("job-456") is None


class TestMatchStorage:
    """Test match result storage and retrieval."""

    def test_set_and_get_match(
        self, session: SessionManager, sample_match: dict
    ) -> None:
        """Test storing and retrieving a match result."""
        session.set_match("match-789", sample_match)
        result = session.get_match("match-789")

        assert result is not None
        assert result["overall_score"] == 85
        assert result["profile_id"] == "profile-123"

    def test_get_nonexistent_match(self, session: SessionManager) -> None:
        """Test retrieving a non-existent match."""
        result = session.get_match("nonexistent")
        assert result is None

    def test_match_expiration(
        self, session: SessionManager, sample_match: dict
    ) -> None:
        """Test match expiration after TTL."""
        session.set_match("match-789", sample_match)
        assert session.get_match("match-789") is not None

        time.sleep(1.1)
        assert session.get_match("match-789") is None


class TestCustomizationStorage:
    """Test customization storage and retrieval."""

    def test_set_and_get_customization(
        self, session: SessionManager, sample_customization: dict
    ) -> None:
        """Test storing and retrieving a customization."""
        session.set_customization("custom-abc", sample_customization)
        result = session.get_customization("custom-abc")

        assert result is not None
        assert result["template"] == "modern"
        assert result["profile_id"] == "profile-123"

    def test_get_nonexistent_customization(self, session: SessionManager) -> None:
        """Test retrieving a non-existent customization."""
        result = session.get_customization("nonexistent")
        assert result is None

    def test_customization_expiration(
        self, session: SessionManager, sample_customization: dict
    ) -> None:
        """Test customization expiration after TTL."""
        session.set_customization("custom-abc", sample_customization)
        assert session.get_customization("custom-abc") is not None

        time.sleep(1.1)
        assert session.get_customization("custom-abc") is None


class TestSessionCleanup:
    """Test session cleanup operations."""

    def test_cleanup_expired_entries(
        self,
        session: SessionManager,
        sample_profile: dict,
        sample_job: dict,
        sample_match: dict,
        sample_customization: dict,
    ) -> None:
        """Test cleanup of expired entries."""
        # Add entries
        session.set_profile("profile-1", sample_profile)
        session.set_job("job-1", sample_job)
        session.set_match("match-1", sample_match)
        session.set_customization("custom-1", sample_customization)

        # Wait for expiration
        time.sleep(1.1)

        # Cleanup should remove all expired
        removed = session.cleanup_expired()
        assert removed == 4

        # Verify all are gone
        assert session.get_profile("profile-1") is None
        assert session.get_job("job-1") is None
        assert session.get_match("match-1") is None
        assert session.get_customization("custom-1") is None

    def test_cleanup_preserves_fresh_entries(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test that cleanup preserves non-expired entries."""
        session.set_profile("profile-1", sample_profile)

        # Cleanup immediately (nothing should be removed)
        removed = session.cleanup_expired()
        assert removed == 0

        # Profile should still exist
        assert session.get_profile("profile-1") is not None

    def test_clear_all_sessions(
        self,
        session: SessionManager,
        sample_profile: dict,
        sample_job: dict,
        sample_match: dict,
        sample_customization: dict,
    ) -> None:
        """Test clearing all session data."""
        # Add entries
        session.set_profile("profile-1", sample_profile)
        session.set_job("job-1", sample_job)
        session.set_match("match-1", sample_match)
        session.set_customization("custom-1", sample_customization)

        # Clear all
        session.clear()

        # All should be gone
        assert session.get_profile("profile-1") is None
        assert session.get_job("job-1") is None
        assert session.get_match("match-1") is None
        assert session.get_customization("custom-1") is None


class TestSessionMetrics:
    """Test session usage metrics."""

    def test_empty_metrics(self, session: SessionManager) -> None:
        """Test metrics for empty session."""
        metrics = session.get_metrics()

        assert metrics.total_entries == 0
        assert metrics.profiles_count == 0
        assert metrics.jobs_count == 0
        assert metrics.matches_count == 0
        assert metrics.customizations_count == 0
        assert metrics.hit_count == 0
        assert metrics.miss_count == 0
        assert metrics.hit_rate == 0.0

    def test_metrics_after_operations(
        self,
        session: SessionManager,
        sample_profile: dict,
        sample_job: dict,
    ) -> None:
        """Test metrics after various operations."""
        # Add some entries
        session.set_profile("profile-1", sample_profile)
        session.set_profile("profile-2", sample_profile)
        session.set_job("job-1", sample_job)

        # Access them (hits)
        session.get_profile("profile-1")
        session.get_profile("profile-1")  # Access twice
        session.get_job("job-1")

        # Try to access non-existent (misses)
        session.get_profile("nonexistent")
        session.get_job("nonexistent")

        metrics = session.get_metrics()

        assert metrics.total_entries == 3
        assert metrics.profiles_count == 2
        assert metrics.jobs_count == 1
        assert metrics.matches_count == 0
        assert metrics.customizations_count == 0
        assert metrics.hit_count == 3
        assert metrics.miss_count == 2
        assert metrics.hit_rate == 3 / 5  # 3 hits out of 5 total requests

    def test_expired_count_metric(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test expired count in metrics."""
        # Add and let expire
        session.set_profile("profile-1", sample_profile)
        time.sleep(1.1)

        # Access expired (triggers removal)
        session.get_profile("profile-1")

        metrics = session.get_metrics()
        assert metrics.expired_count == 1

    def test_access_count_tracking(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test that access counts are tracked."""
        session.set_profile("profile-1", sample_profile)

        # Access multiple times
        for _ in range(5):
            session.get_profile("profile-1")

        metrics = session.get_metrics()
        assert metrics.total_accesses >= 5


class TestBackwardCompatibilityMethods:
    """Test backward compatibility helper methods."""

    def test_get_all_profiles(
        self, session: SessionManager, sample_profile: dict
    ) -> None:
        """Test getting all profiles as dict."""
        session.set_profile("profile-1", sample_profile)
        session.set_profile("profile-2", sample_profile)

        all_profiles = session.get_all_profiles()
        assert len(all_profiles) == 2
        assert "profile-1" in all_profiles
        assert "profile-2" in all_profiles

    def test_get_all_jobs(self, session: SessionManager, sample_job: dict) -> None:
        """Test getting all jobs as dict."""
        session.set_job("job-1", sample_job)
        session.set_job("job-2", sample_job)

        all_jobs = session.get_all_jobs()
        assert len(all_jobs) == 2
        assert "job-1" in all_jobs
        assert "job-2" in all_jobs

    def test_get_all_matches(
        self, session: SessionManager, sample_match: dict
    ) -> None:
        """Test getting all matches as dict."""
        session.set_match("match-1", sample_match)
        session.set_match("match-2", sample_match)

        all_matches = session.get_all_matches()
        assert len(all_matches) == 2
        assert "match-1" in all_matches
        assert "match-2" in all_matches

    def test_get_all_customizations(
        self, session: SessionManager, sample_customization: dict
    ) -> None:
        """Test getting all customizations as dict."""
        session.set_customization("custom-1", sample_customization)
        session.set_customization("custom-2", sample_customization)

        all_customizations = session.get_all_customizations()
        assert len(all_customizations) == 2
        assert "custom-1" in all_customizations
        assert "custom-2" in all_customizations


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    def test_multiple_entry_types_simultaneously(
        self,
        session: SessionManager,
        sample_profile: dict,
        sample_job: dict,
        sample_match: dict,
        sample_customization: dict,
    ) -> None:
        """Test storing different entry types simultaneously."""
        session.set_profile("profile-1", sample_profile)
        session.set_job("job-1", sample_job)
        session.set_match("match-1", sample_match)
        session.set_customization("custom-1", sample_customization)

        # All should be retrievable
        assert session.get_profile("profile-1") is not None
        assert session.get_job("job-1") is not None
        assert session.get_match("match-1") is not None
        assert session.get_customization("custom-1") is not None

        metrics = session.get_metrics()
        assert metrics.total_entries == 4
