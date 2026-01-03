"""
Database persistence for customization history.

This module provides SQLite-based storage for resume customizations,
allowing users to track their customization history with filtering and sorting.
"""

import json
import sqlite3
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

        cursor = self.conn.cursor()
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
                metadata TEXT
            )
        """
        )

        # Create indexes for common queries
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
