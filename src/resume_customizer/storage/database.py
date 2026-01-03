"""
Database persistence for customization history.

This module provides SQLite-based storage for resume customizations,
allowing users to track their customization history with filtering and sorting.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)


class CustomizationDatabase:
    """SQLite database for storing resume customizations."""

    def __init__(self, db_path: str | Path = "customizations.db") -> None:
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn: sqlite3.Connection | None = None
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")

        cursor = self.conn.cursor()

        # Create profiles table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                profile_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                location TEXT,
                linkedin TEXT,
                github TEXT,
                website TEXT,
                summary TEXT,
                skills_count INTEGER,
                experiences_count INTEGER,
                education_count INTEGER,
                certifications_count INTEGER,
                full_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )

        # Create jobs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                job_type TEXT,
                experience_level TEXT,
                salary_range TEXT,
                required_skills_count INTEGER,
                preferred_skills_count INTEGER,
                full_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """
        )

        # Create match_results table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS match_results (
                match_id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                overall_score INTEGER NOT NULL,
                technical_score INTEGER NOT NULL,
                experience_score INTEGER NOT NULL,
                domain_score INTEGER NOT NULL,
                keyword_coverage INTEGER NOT NULL,
                matched_skills_count INTEGER NOT NULL,
                missing_skills_count INTEGER NOT NULL,
                full_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (profile_id) REFERENCES profiles(profile_id),
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """
        )

        # Create customizations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customizations (
                customization_id TEXT PRIMARY KEY,
                profile_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                profile_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                overall_score INTEGER NOT NULL,
                template TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (profile_id) REFERENCES profiles(profile_id),
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """
        )

        # Create indexes for profiles
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_profiles_email
            ON profiles(email)
        """
        )

        # Create indexes for jobs
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_jobs_company
            ON jobs(company)
        """
        )

        # Create indexes for match_results
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_matches_score
            ON match_results(overall_score)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_matches_profile
            ON match_results(profile_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_matches_job
            ON match_results(job_id)
        """
        )

        # Create indexes for customizations (keep existing)
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_company
            ON customizations(company)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON customizations(created_at)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_profile_id
            ON customizations(profile_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_job_id
            ON customizations(job_id)
        """
        )

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def insert_customization(
        self,
        customization_id: str,
        profile_id: str,
        job_id: str,
        profile_name: str,
        job_title: str,
        company: str,
        overall_score: int,
        template: str,
        created_at: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Insert a new customization record.

        Args:
            customization_id: Unique ID for the customization
            profile_id: ID of the user profile
            job_id: ID of the job description
            profile_name: Name of the user
            job_title: Job title
            company: Company name
            overall_score: Match score (0-100)
            template: Template name used
            created_at: ISO format timestamp
            metadata: Additional metadata as dict
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO customizations (
                customization_id, profile_id, job_id, profile_name,
                job_title, company, overall_score, template,
                created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                customization_id,
                profile_id,
                job_id,
                profile_name,
                job_title,
                company,
                overall_score,
                template,
                created_at,
                json.dumps(metadata) if metadata else None,
            ),
        )
        self.conn.commit()
        logger.info(f"Inserted customization: {customization_id}")

    def get_customizations(
        self,
        profile_id: str | None = None,
        job_id: str | None = None,
        company: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 10,
        order_by: str = "created_at",
        order_direction: str = "DESC",
    ) -> list[dict[str, Any]]:
        """
        Query customizations with optional filters.

        Args:
            profile_id: Filter by profile ID
            job_id: Filter by job ID
            company: Filter by company name (case-insensitive)
            start_date: Filter by created_at >= start_date (ISO format)
            end_date: Filter by created_at <= end_date (ISO format)
            limit: Maximum number of results
            order_by: Column to order by (default: created_at)
            order_direction: ASC or DESC (default: DESC)

        Returns:
            List of customization records as dictionaries
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        # Build query with filters
        query = "SELECT * FROM customizations WHERE 1=1"
        params: list[Any] = []

        if profile_id:
            query += " AND profile_id = ?"
            params.append(profile_id)

        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)

        if company:
            query += " AND LOWER(company) LIKE LOWER(?)"
            params.append(f"%{company}%")

        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)

        # Add ordering
        allowed_order_by = [
            "created_at",
            "overall_score",
            "company",
            "job_title",
        ]
        if order_by not in allowed_order_by:
            order_by = "created_at"

        if order_direction.upper() not in ["ASC", "DESC"]:
            order_direction = "DESC"

        query += f" ORDER BY {order_by} {order_direction}"

        # Add limit
        query += " LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        results = []
        for row in rows:
            record = dict(row)
            # Parse metadata JSON
            if record.get("metadata"):
                record["metadata"] = json.loads(record["metadata"])
            results.append(record)

        logger.info(f"Retrieved {len(results)} customizations")
        return results

    def get_customization_by_id(self, customization_id: str) -> dict[str, Any] | None:
        """
        Get a single customization by ID.

        Args:
            customization_id: The customization ID

        Returns:
            Customization record or None if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM customizations WHERE customization_id = ?
        """,
            (customization_id,),
        )
        row = cursor.fetchone()

        if row:
            record = dict(row)
            if record.get("metadata"):
                record["metadata"] = json.loads(record["metadata"])
            return record
        return None

    def delete_customization(self, customization_id: str) -> bool:
        """
        Delete a customization by ID.

        Args:
            customization_id: The customization ID

        Returns:
            True if deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM customizations WHERE customization_id = ?
        """,
            (customization_id,),
        )
        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted customization: {customization_id}")
        return deleted

    # Profile operations
    def insert_profile(
        self,
        profile_id: str,
        name: str,
        email: str,
        full_data: dict[str, Any],
        phone: str | None = None,
        location: str | None = None,
        linkedin: str | None = None,
        github: str | None = None,
        website: str | None = None,
        summary: str | None = None,
        skills_count: int = 0,
        experiences_count: int = 0,
        education_count: int = 0,
        certifications_count: int = 0,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        """
        Insert a new profile record.

        Args:
            profile_id: Unique ID for the profile
            name: User's name
            email: User's email
            full_data: Complete UserProfile as dict
            phone: Phone number (optional)
            location: Location (optional)
            linkedin: LinkedIn URL (optional)
            github: GitHub URL (optional)
            website: Website URL (optional)
            summary: Professional summary (optional)
            skills_count: Number of skills
            experiences_count: Number of experiences
            education_count: Number of education entries
            certifications_count: Number of certifications
            created_at: ISO format timestamp
            updated_at: ISO format timestamp
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        from datetime import datetime

        now = datetime.now().isoformat()
        created_at = created_at or now
        updated_at = updated_at or now

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO profiles (
                profile_id, name, email, phone, location, linkedin, github, website,
                summary, skills_count, experiences_count, education_count,
                certifications_count, full_data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                profile_id,
                name,
                email,
                phone,
                location,
                linkedin,
                github,
                website,
                summary,
                skills_count,
                experiences_count,
                education_count,
                certifications_count,
                json.dumps(full_data),
                created_at,
                updated_at,
            ),
        )
        self.conn.commit()
        logger.info(f"Inserted profile: {profile_id}")

    def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        """
        Get a profile by ID.

        Args:
            profile_id: The profile ID

        Returns:
            Profile record or None if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM profiles WHERE profile_id = ?
        """,
            (profile_id,),
        )
        row = cursor.fetchone()

        if row:
            record = dict(row)
            if record.get("full_data"):
                record["full_data"] = json.loads(record["full_data"])
            return record
        return None

    def update_profile(
        self,
        profile_id: str,
        full_data: dict[str, Any],
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        location: str | None = None,
        linkedin: str | None = None,
        github: str | None = None,
        website: str | None = None,
        summary: str | None = None,
        skills_count: int | None = None,
        experiences_count: int | None = None,
        education_count: int | None = None,
        certifications_count: int | None = None,
    ) -> bool:
        """
        Update an existing profile.

        Args:
            profile_id: The profile ID
            full_data: Complete UserProfile as dict
            name: User's name (optional)
            email: User's email (optional)
            phone: Phone number (optional)
            location: Location (optional)
            linkedin: LinkedIn URL (optional)
            github: GitHub URL (optional)
            website: Website URL (optional)
            summary: Professional summary (optional)
            skills_count: Number of skills (optional)
            experiences_count: Number of experiences (optional)
            education_count: Number of education entries (optional)
            certifications_count: Number of certifications (optional)

        Returns:
            True if updated, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        from datetime import datetime

        # First get existing record
        existing = self.get_profile(profile_id)
        if not existing:
            return False

        # Update fields (use existing values if not provided)
        updated_at = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE profiles
            SET name = ?, email = ?, phone = ?, location = ?, linkedin = ?,
                github = ?, website = ?, summary = ?, skills_count = ?,
                experiences_count = ?, education_count = ?, certifications_count = ?,
                full_data = ?, updated_at = ?
            WHERE profile_id = ?
        """,
            (
                name if name is not None else existing["name"],
                email if email is not None else existing["email"],
                phone if phone is not None else existing["phone"],
                location if location is not None else existing["location"],
                linkedin if linkedin is not None else existing["linkedin"],
                github if github is not None else existing["github"],
                website if website is not None else existing["website"],
                summary if summary is not None else existing["summary"],
                skills_count if skills_count is not None else existing["skills_count"],
                experiences_count
                if experiences_count is not None
                else existing["experiences_count"],
                education_count
                if education_count is not None
                else existing["education_count"],
                certifications_count
                if certifications_count is not None
                else existing["certifications_count"],
                json.dumps(full_data),
                updated_at,
                profile_id,
            ),
        )
        self.conn.commit()
        logger.info(f"Updated profile: {profile_id}")
        return True

    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a profile by ID.

        Args:
            profile_id: The profile ID

        Returns:
            True if deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM profiles WHERE profile_id = ?
        """,
            (profile_id,),
        )
        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted profile: {profile_id}")
        return deleted

    # Job operations
    def insert_job(
        self,
        job_id: str,
        title: str,
        company: str,
        full_data: dict[str, Any],
        location: str | None = None,
        job_type: str | None = None,
        experience_level: str | None = None,
        salary_range: str | None = None,
        required_skills_count: int = 0,
        preferred_skills_count: int = 0,
        created_at: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        """
        Insert a new job record.

        Args:
            job_id: Unique ID for the job
            title: Job title
            company: Company name
            full_data: Complete JobDescription as dict
            location: Job location (optional)
            job_type: Job type (optional)
            experience_level: Experience level (optional)
            salary_range: Salary range (optional)
            required_skills_count: Number of required skills
            preferred_skills_count: Number of preferred skills
            created_at: ISO format timestamp
            updated_at: ISO format timestamp
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        from datetime import datetime

        now = datetime.now().isoformat()
        created_at = created_at or now
        updated_at = updated_at or now

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (
                job_id, title, company, location, job_type, experience_level,
                salary_range, required_skills_count, preferred_skills_count,
                full_data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_id,
                title,
                company,
                location,
                job_type,
                experience_level,
                salary_range,
                required_skills_count,
                preferred_skills_count,
                json.dumps(full_data),
                created_at,
                updated_at,
            ),
        )
        self.conn.commit()
        logger.info(f"Inserted job: {job_id}")

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """
        Get a job by ID.

        Args:
            job_id: The job ID

        Returns:
            Job record or None if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM jobs WHERE job_id = ?
        """,
            (job_id,),
        )
        row = cursor.fetchone()

        if row:
            record = dict(row)
            if record.get("full_data"):
                record["full_data"] = json.loads(record["full_data"])
            return record
        return None

    def update_job(
        self,
        job_id: str,
        full_data: dict[str, Any],
        title: str | None = None,
        company: str | None = None,
        location: str | None = None,
        job_type: str | None = None,
        experience_level: str | None = None,
        salary_range: str | None = None,
        required_skills_count: int | None = None,
        preferred_skills_count: int | None = None,
    ) -> bool:
        """
        Update an existing job.

        Args:
            job_id: The job ID
            full_data: Complete JobDescription as dict
            title: Job title (optional)
            company: Company name (optional)
            location: Job location (optional)
            job_type: Job type (optional)
            experience_level: Experience level (optional)
            salary_range: Salary range (optional)
            required_skills_count: Number of required skills (optional)
            preferred_skills_count: Number of preferred skills (optional)

        Returns:
            True if updated, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        from datetime import datetime

        # First get existing record
        existing = self.get_job(job_id)
        if not existing:
            return False

        # Update fields
        updated_at = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE jobs
            SET title = ?, company = ?, location = ?, job_type = ?,
                experience_level = ?, salary_range = ?, required_skills_count = ?,
                preferred_skills_count = ?, full_data = ?, updated_at = ?
            WHERE job_id = ?
        """,
            (
                title if title is not None else existing["title"],
                company if company is not None else existing["company"],
                location if location is not None else existing["location"],
                job_type if job_type is not None else existing["job_type"],
                experience_level
                if experience_level is not None
                else existing["experience_level"],
                salary_range if salary_range is not None else existing["salary_range"],
                required_skills_count
                if required_skills_count is not None
                else existing["required_skills_count"],
                preferred_skills_count
                if preferred_skills_count is not None
                else existing["preferred_skills_count"],
                json.dumps(full_data),
                updated_at,
                job_id,
            ),
        )
        self.conn.commit()
        logger.info(f"Updated job: {job_id}")
        return True

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job by ID.

        Args:
            job_id: The job ID

        Returns:
            True if deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM jobs WHERE job_id = ?
        """,
            (job_id,),
        )
        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted job: {job_id}")
        return deleted

    # Match result operations
    def insert_match(
        self,
        match_id: str,
        profile_id: str,
        job_id: str,
        overall_score: int,
        technical_score: int,
        experience_score: int,
        domain_score: int,
        keyword_coverage: int,
        matched_skills_count: int,
        missing_skills_count: int,
        full_data: dict[str, Any],
        created_at: str | None = None,
    ) -> None:
        """
        Insert a new match result record.

        Args:
            match_id: Unique ID for the match
            profile_id: ID of the profile
            job_id: ID of the job
            overall_score: Overall match score (0-100)
            technical_score: Technical skills score
            experience_score: Experience score
            domain_score: Domain knowledge score
            keyword_coverage: Keyword coverage score
            matched_skills_count: Number of matched skills
            missing_skills_count: Number of missing skills
            full_data: Complete MatchResult as dict
            created_at: ISO format timestamp
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        from datetime import datetime

        created_at = created_at or datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO match_results (
                match_id, profile_id, job_id, overall_score, technical_score,
                experience_score, domain_score, keyword_coverage,
                matched_skills_count, missing_skills_count, full_data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                match_id,
                profile_id,
                job_id,
                overall_score,
                technical_score,
                experience_score,
                domain_score,
                keyword_coverage,
                matched_skills_count,
                missing_skills_count,
                json.dumps(full_data),
                created_at,
            ),
        )
        self.conn.commit()
        logger.info(f"Inserted match result: {match_id}")

    def get_match(self, match_id: str) -> dict[str, Any] | None:
        """
        Get a match result by ID.

        Args:
            match_id: The match ID

        Returns:
            Match record or None if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM match_results WHERE match_id = ?
        """,
            (match_id,),
        )
        row = cursor.fetchone()

        if row:
            record = dict(row)
            if record.get("full_data"):
                record["full_data"] = json.loads(record["full_data"])
            return record
        return None

    def delete_match(self, match_id: str) -> bool:
        """
        Delete a match result by ID.

        Args:
            match_id: The match ID

        Returns:
            True if deleted, False if not found
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM match_results WHERE match_id = ?
        """,
            (match_id,),
        )
        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted match result: {match_id}")
        return deleted

    # History & Retrieval methods
    def query_customizations_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """
        Query customizations within a date range.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD or ISO 8601)
            end_date: End date in ISO format (YYYY-MM-DD or ISO 8601)

        Returns:
            List of customization records
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM customizations
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at DESC
        """,
            (start_date, end_date),
        )

        results = []
        for row in cursor.fetchall():
            record = dict(row)
            if record.get("metadata"):
                record["metadata"] = json.loads(record["metadata"])
            results.append(record)

        logger.info(
            f"Found {len(results)} customizations between {start_date} and {end_date}"
        )
        return results

    def query_customizations_by_score(
        self, min_score: int, max_score: int = 100
    ) -> list[dict[str, Any]]:
        """
        Query customizations by match score range.

        Args:
            min_score: Minimum overall score (0-100)
            max_score: Maximum overall score (0-100)

        Returns:
            List of customization records
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM customizations
            WHERE overall_score >= ? AND overall_score <= ?
            ORDER BY overall_score DESC, created_at DESC
        """,
            (min_score, max_score),
        )

        results = []
        for row in cursor.fetchall():
            record = dict(row)
            if record.get("metadata"):
                record["metadata"] = json.loads(record["metadata"])
            results.append(record)

        logger.info(
            f"Found {len(results)} customizations with score {min_score}-{max_score}"
        )
        return results

    def search_customizations(self, search_term: str) -> list[dict[str, Any]]:
        """
        Full-text search across customizations.

        Searches in: profile_name, job_title, company

        Args:
            search_term: Search term (case-insensitive)

        Returns:
            List of matching customization records
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        search_pattern = f"%{search_term}%"
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM customizations
            WHERE profile_name LIKE ? OR job_title LIKE ? OR company LIKE ?
            ORDER BY created_at DESC
        """,
            (search_pattern, search_pattern, search_pattern),
        )

        results = []
        for row in cursor.fetchall():
            record = dict(row)
            if record.get("metadata"):
                record["metadata"] = json.loads(record["metadata"])
            results.append(record)

        logger.info(f"Found {len(results)} customizations matching '{search_term}'")
        return results

    # Analytics methods
    def get_analytics_summary(self) -> dict[str, Any]:
        """
        Get comprehensive analytics summary.

        Returns:
            Dictionary with analytics data including:
            - total_customizations: Total count
            - avg_match_score: Average overall score
            - top_companies: Top companies by customization count
            - score_distribution: Distribution by score ranges
            - customizations_by_month: Monthly breakdown
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()

        # Total customizations
        cursor.execute("SELECT COUNT(*) FROM customizations")
        total_customizations = cursor.fetchone()[0]

        # Average match score
        cursor.execute("SELECT AVG(overall_score) FROM customizations")
        avg_score_result = cursor.fetchone()[0]
        avg_match_score = round(avg_score_result, 2) if avg_score_result else 0.0

        # Top companies (top 10)
        cursor.execute(
            """
            SELECT company, COUNT(*) as count
            FROM customizations
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        """
        )
        top_companies = [
            {"company": row[0], "count": row[1]} for row in cursor.fetchall()
        ]

        # Score distribution
        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN overall_score >= 90 THEN 1 ELSE 0 END) as excellent,
                SUM(CASE WHEN overall_score >= 80 AND overall_score < 90 THEN 1 ELSE 0 END) as good,
                SUM(CASE WHEN overall_score >= 70 AND overall_score < 80 THEN 1 ELSE 0 END) as fair,
                SUM(CASE WHEN overall_score < 70 THEN 1 ELSE 0 END) as poor
            FROM customizations
        """
        )
        dist_row = cursor.fetchone()
        score_distribution = {
            "excellent_90_plus": dist_row[0] or 0,
            "good_80_89": dist_row[1] or 0,
            "fair_70_79": dist_row[2] or 0,
            "poor_below_70": dist_row[3] or 0,
        }

        # Customizations by month (last 12 months)
        cursor.execute(
            """
            SELECT
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as count
            FROM customizations
            WHERE created_at >= date('now', '-12 months')
            GROUP BY month
            ORDER BY month DESC
        """
        )
        customizations_by_month = [
            {"month": row[0], "count": row[1]} for row in cursor.fetchall()
        ]

        analytics = {
            "total_customizations": total_customizations,
            "avg_match_score": avg_match_score,
            "top_companies": top_companies,
            "score_distribution": score_distribution,
            "customizations_by_month": customizations_by_month,
        }

        logger.info("Generated analytics summary")
        return analytics

    def get_skill_gap_trends(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Analyze skill gap trends across match results.

        Args:
            limit: Maximum number of trending skills to return

        Returns:
            List of skills with gap frequency
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM match_results
            ORDER BY created_at DESC
        """
        )

        # Aggregate missing skills from match results
        skill_gaps: dict[str, int] = {}
        for row in cursor.fetchall():
            record = dict(row)
            if record.get("full_data"):
                full_data = json.loads(record["full_data"])
                missing_skills = full_data.get("missing_required_skills", [])
                for skill in missing_skills:
                    skill_name = skill if isinstance(skill, str) else skill.get("name", "")
                    if skill_name:
                        skill_gaps[skill_name] = skill_gaps.get(skill_name, 0) + 1

        # Sort by frequency and take top N
        sorted_gaps = sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]
        trends = [{"skill": skill, "gap_count": count} for skill, count in sorted_gaps]

        logger.info(f"Analyzed skill gaps: {len(trends)} trending skills")
        return trends

    # Export methods
    def export_to_json(
        self,
        output_path: str,
        company: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Export customizations to JSON file.

        Args:
            output_path: Path to output JSON file
            company: Optional company filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Export statistics
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        # Query with filters
        if company and start_date and end_date:
            records = [
                r
                for r in self.query_customizations_by_date_range(start_date, end_date)
                if r["company"] == company
            ]
        elif company:
            records = self.get_customizations(company=company)
        elif start_date and end_date:
            records = self.query_customizations_by_date_range(start_date, end_date)
        else:
            records = self.get_customizations()

        # Get analytics
        analytics = self.get_analytics_summary()

        export_data = {
            "export_date": datetime.now().isoformat(),
            "filters": {
                "company": company,
                "start_date": start_date,
                "end_date": end_date,
            },
            "analytics": analytics,
            "customizations": records,
        }

        # Write to file
        from pathlib import Path

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

        stats = {
            "records_exported": len(records),
            "output_path": str(output_file),
            "file_size_bytes": output_file.stat().st_size,
        }

        logger.info(
            f"Exported {stats['records_exported']} customizations to {output_path}"
        )
        return stats

    def export_to_csv(
        self,
        output_path: str,
        company: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Export customizations to CSV file.

        Args:
            output_path: Path to output CSV file
            company: Optional company filter
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Export statistics
        """
        if not self.conn:
            raise RuntimeError("Database connection not initialized")

        import csv
        from pathlib import Path

        # Query with filters
        if company and start_date and end_date:
            records = [
                r
                for r in self.query_customizations_by_date_range(start_date, end_date)
                if r["company"] == company
            ]
        elif company:
            records = self.get_customizations(company=company)
        elif start_date and end_date:
            records = self.query_customizations_by_date_range(start_date, end_date)
        else:
            records = self.get_customizations()

        if not records:
            # Create empty file with headers
            records = []

        # Write to CSV
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="") as f:
            # Define CSV columns (exclude metadata for readability)
            fieldnames = [
                "customization_id",
                "profile_id",
                "job_id",
                "profile_name",
                "job_title",
                "company",
                "overall_score",
                "template",
                "created_at",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for record in records:
                # Remove metadata field for CSV export
                csv_record = {k: v for k, v in record.items() if k != "metadata"}
                writer.writerow(csv_record)

        stats = {
            "records_exported": len(records),
            "output_path": str(output_file),
            "file_size_bytes": output_file.stat().st_size if records else 0,
        }

        logger.info(
            f"Exported {stats['records_exported']} customizations to {output_path}"
        )
        return stats

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def __enter__(self) -> "CustomizationDatabase":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
