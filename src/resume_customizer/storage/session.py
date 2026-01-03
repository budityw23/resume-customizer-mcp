"""
Session management for resume customizer MCP server.

This module provides in-memory session storage with TTL support,
automatic cleanup, and usage metrics.
"""

import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class SessionEntry(Generic[T]):
    """A single session entry with metadata."""

    value: T
    created_at: float
    last_accessed: float
    access_count: int = 0


@dataclass
class SessionMetrics:
    """Session usage metrics."""

    total_entries: int
    profiles_count: int
    jobs_count: int
    matches_count: int
    customizations_count: int
    total_accesses: int
    hit_count: int
    miss_count: int
    hit_rate: float
    expired_count: int
    memory_entries: int


class SessionManager:
    """Manages in-memory session state with TTL and cleanup."""

    def __init__(self, default_ttl: int = 3600) -> None:
        """
        Initialize session manager.

        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self._profiles: dict[str, SessionEntry[Any]] = {}
        self._jobs: dict[str, SessionEntry[Any]] = {}
        self._matches: dict[str, SessionEntry[Any]] = {}
        self._customizations: dict[str, SessionEntry[Any]] = {}

        # Metrics
        self._hit_count = 0
        self._miss_count = 0
        self._expired_count = 0

        logger.info(f"SessionManager initialized with TTL={default_ttl}s")

    def _is_expired(self, entry: SessionEntry[Any], ttl: int | None = None) -> bool:
        """
        Check if an entry has expired.

        Args:
            entry: The session entry to check
            ttl: Optional TTL override (uses default if not provided)

        Returns:
            True if expired, False otherwise
        """
        effective_ttl = ttl if ttl is not None else self.default_ttl
        age = time.time() - entry.created_at
        return age > effective_ttl

    def set_profile(self, profile_id: str, profile: Any) -> None:
        """
        Store a profile in session.

        Args:
            profile_id: Unique profile ID
            profile: Profile object to store
        """
        now = time.time()
        self._profiles[profile_id] = SessionEntry(
            value=profile,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )
        logger.debug(f"Stored profile in session: {profile_id}")

    def get_profile(self, profile_id: str, ttl: int | None = None) -> Any | None:
        """
        Retrieve a profile from session.

        Args:
            profile_id: Profile ID to retrieve
            ttl: Optional TTL override

        Returns:
            Profile object if found and not expired, None otherwise
        """
        entry = self._profiles.get(profile_id)

        if entry is None:
            self._miss_count += 1
            logger.debug(f"Profile not found in session: {profile_id}")
            return None

        if self._is_expired(entry, ttl):
            self._expired_count += 1
            del self._profiles[profile_id]
            logger.debug(f"Profile expired in session: {profile_id}")
            return None

        # Update access metadata
        entry.last_accessed = time.time()
        entry.access_count += 1
        self._hit_count += 1
        logger.debug(f"Retrieved profile from session: {profile_id}")
        return entry.value

    def set_job(self, job_id: str, job: Any) -> None:
        """
        Store a job in session.

        Args:
            job_id: Unique job ID
            job: Job object to store
        """
        now = time.time()
        self._jobs[job_id] = SessionEntry(
            value=job,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )
        logger.debug(f"Stored job in session: {job_id}")

    def get_job(self, job_id: str, ttl: int | None = None) -> Any | None:
        """
        Retrieve a job from session.

        Args:
            job_id: Job ID to retrieve
            ttl: Optional TTL override

        Returns:
            Job object if found and not expired, None otherwise
        """
        entry = self._jobs.get(job_id)

        if entry is None:
            self._miss_count += 1
            logger.debug(f"Job not found in session: {job_id}")
            return None

        if self._is_expired(entry, ttl):
            self._expired_count += 1
            del self._jobs[job_id]
            logger.debug(f"Job expired in session: {job_id}")
            return None

        entry.last_accessed = time.time()
        entry.access_count += 1
        self._hit_count += 1
        logger.debug(f"Retrieved job from session: {job_id}")
        return entry.value

    def set_match(self, match_id: str, match: Any) -> None:
        """
        Store a match result in session.

        Args:
            match_id: Unique match ID
            match: Match result object to store
        """
        now = time.time()
        self._matches[match_id] = SessionEntry(
            value=match,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )
        logger.debug(f"Stored match in session: {match_id}")

    def get_match(self, match_id: str, ttl: int | None = None) -> Any | None:
        """
        Retrieve a match result from session.

        Args:
            match_id: Match ID to retrieve
            ttl: Optional TTL override

        Returns:
            Match result if found and not expired, None otherwise
        """
        entry = self._matches.get(match_id)

        if entry is None:
            self._miss_count += 1
            logger.debug(f"Match not found in session: {match_id}")
            return None

        if self._is_expired(entry, ttl):
            self._expired_count += 1
            del self._matches[match_id]
            logger.debug(f"Match expired in session: {match_id}")
            return None

        entry.last_accessed = time.time()
        entry.access_count += 1
        self._hit_count += 1
        logger.debug(f"Retrieved match from session: {match_id}")
        return entry.value

    def set_customization(self, customization_id: str, customization: Any) -> None:
        """
        Store a customization in session.

        Args:
            customization_id: Unique customization ID
            customization: Customization object to store
        """
        now = time.time()
        self._customizations[customization_id] = SessionEntry(
            value=customization,
            created_at=now,
            last_accessed=now,
            access_count=0,
        )
        logger.debug(f"Stored customization in session: {customization_id}")

    def get_customization(
        self, customization_id: str, ttl: int | None = None
    ) -> Any | None:
        """
        Retrieve a customization from session.

        Args:
            customization_id: Customization ID to retrieve
            ttl: Optional TTL override

        Returns:
            Customization if found and not expired, None otherwise
        """
        entry = self._customizations.get(customization_id)

        if entry is None:
            self._miss_count += 1
            logger.debug(f"Customization not found in session: {customization_id}")
            return None

        if self._is_expired(entry, ttl):
            self._expired_count += 1
            del self._customizations[customization_id]
            logger.debug(f"Customization expired in session: {customization_id}")
            return None

        entry.last_accessed = time.time()
        entry.access_count += 1
        self._hit_count += 1
        logger.debug(f"Retrieved customization from session: {customization_id}")
        return entry.value

    def cleanup_expired(self, ttl: int | None = None) -> int:
        """
        Remove all expired entries from session.

        Args:
            ttl: Optional TTL override for this cleanup

        Returns:
            Number of entries removed
        """
        removed = 0
        now = time.time()
        effective_ttl = ttl if ttl is not None else self.default_ttl

        # Clean profiles
        expired_profiles = [
            pid
            for pid, entry in self._profiles.items()
            if (now - entry.created_at) > effective_ttl
        ]
        for pid in expired_profiles:
            del self._profiles[pid]
            removed += 1

        # Clean jobs
        expired_jobs = [
            jid
            for jid, entry in self._jobs.items()
            if (now - entry.created_at) > effective_ttl
        ]
        for jid in expired_jobs:
            del self._jobs[jid]
            removed += 1

        # Clean matches
        expired_matches = [
            mid
            for mid, entry in self._matches.items()
            if (now - entry.created_at) > effective_ttl
        ]
        for mid in expired_matches:
            del self._matches[mid]
            removed += 1

        # Clean customizations
        expired_customizations = [
            cid
            for cid, entry in self._customizations.items()
            if (now - entry.created_at) > effective_ttl
        ]
        for cid in expired_customizations:
            del self._customizations[cid]
            removed += 1

        if removed > 0:
            self._expired_count += removed
            logger.info(f"Cleaned up {removed} expired session entries")

        return removed

    def clear(self) -> None:
        """Clear all session data."""
        count = (
            len(self._profiles)
            + len(self._jobs)
            + len(self._matches)
            + len(self._customizations)
        )

        self._profiles.clear()
        self._jobs.clear()
        self._matches.clear()
        self._customizations.clear()

        logger.info(f"Cleared {count} session entries")

    def get_metrics(self) -> SessionMetrics:
        """
        Get session usage metrics.

        Returns:
            SessionMetrics object with current statistics
        """
        total_accesses = sum(
            entry.access_count
            for storage in [
                self._profiles,
                self._jobs,
                self._matches,
                self._customizations,
            ]
            for entry in storage.values()
        )

        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0.0

        return SessionMetrics(
            total_entries=len(self._profiles)
            + len(self._jobs)
            + len(self._matches)
            + len(self._customizations),
            profiles_count=len(self._profiles),
            jobs_count=len(self._jobs),
            matches_count=len(self._matches),
            customizations_count=len(self._customizations),
            total_accesses=total_accesses,
            hit_count=self._hit_count,
            miss_count=self._miss_count,
            hit_rate=hit_rate,
            expired_count=self._expired_count,
            memory_entries=len(self._profiles)
            + len(self._jobs)
            + len(self._matches)
            + len(self._customizations),
        )

    def get_all_profiles(self) -> dict[str, Any]:
        """Get all profiles (for backward compatibility)."""
        return {pid: entry.value for pid, entry in self._profiles.items()}

    def get_all_jobs(self) -> dict[str, Any]:
        """Get all jobs (for backward compatibility)."""
        return {jid: entry.value for jid, entry in self._jobs.items()}

    def get_all_matches(self) -> dict[str, Any]:
        """Get all matches (for backward compatibility)."""
        return {mid: entry.value for mid, entry in self._matches.items()}

    def get_all_customizations(self) -> dict[str, Any]:
        """Get all customizations (for backward compatibility)."""
        return {cid: entry.value for cid, entry in self._customizations.items()}
