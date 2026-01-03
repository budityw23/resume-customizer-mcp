"""
Tests for history & retrieval functionality (Phase 7.3).

Tests the database history queries, analytics, and export functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from resume_customizer.storage.database import CustomizationDatabase


@pytest.fixture
def database() -> CustomizationDatabase:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = CustomizationDatabase(db_path)
    yield db
    db.close()
    db_path.unlink()


@pytest.fixture
def populated_database(database: CustomizationDatabase) -> CustomizationDatabase:
    """Create a database with test data."""
    # Insert profiles
    for i in range(3):
        database.insert_profile(
            profile_id=f"profile-{i}",
            name=f"User {i}",
            email=f"user{i}@example.com",
            full_data={"name": f"User {i}"},
        )

    # Insert jobs
    companies = ["TechCorp", "StartupXYZ", "BigCompany"]
    for i in range(3):
        database.insert_job(
            job_id=f"job-{i}",
            title=f"Engineer {i}",
            company=companies[i],
            full_data={"title": f"Engineer {i}"},
        )

    # Insert match results
    for i in range(3):
        database.insert_match(
            match_id=f"match-{i}",
            profile_id=f"profile-{i}",
            job_id=f"job-{i}",
            overall_score=70 + i * 10,
            technical_score=75 + i * 5,
            experience_score=80 + i * 5,
            domain_score=70 + i * 10,
            keyword_coverage=65 + i * 10,
            matched_skills_count=10 + i * 2,
            missing_skills_count=5 - i,
            full_data={
                "overall_score": 70 + i * 10,
                "missing_required_skills": ["Docker", "Kubernetes"][:5 - i],
            },
            created_at=f"2024-01-{15 + i:02d}T10:00:00Z",
        )

    # Insert customizations
    for i in range(5):
        database.insert_customization(
            customization_id=f"custom-{i}",
            profile_id=f"profile-{i % 3}",
            job_id=f"job-{i % 3}",
            profile_name=f"User {i % 3}",
            job_title=f"Engineer {i % 3}",
            company=companies[i % 3],
            overall_score=70 + i * 5,
            template="modern",
            created_at=f"2024-01-{15 + i:02d}T10:00:00Z",
            metadata=json.dumps({"test": f"data-{i}"}),
        )

    return database


class TestHistoryQueries:
    """Test history query methods."""

    def test_query_by_date_range(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test querying customizations by date range."""
        results = populated_database.query_customizations_by_date_range(
            start_date="2024-01-16T00:00:00Z", end_date="2024-01-18T23:59:59Z"
        )

        assert len(results) == 3  # Should get custom-1, custom-2, custom-3
        # Check that all results are within the date range
        for r in results:
            assert "2024-01-16" <= r["created_at"] <= "2024-01-19"

    def test_query_by_date_range_empty(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test query with date range that has no results."""
        results = populated_database.query_customizations_by_date_range(
            start_date="2024-02-01T00:00:00Z", end_date="2024-02-28T23:59:59Z"
        )

        assert len(results) == 0

    def test_query_by_score_range(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test querying customizations by score range."""
        results = populated_database.query_customizations_by_score(
            min_score=75, max_score=85
        )

        assert len(results) == 3  # Should get 75, 80, 85
        assert all(75 <= r["overall_score"] <= 85 for r in results)
        # Should be ordered by score descending
        scores = [r["overall_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_query_by_score_all(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test querying all customizations by score."""
        results = populated_database.query_customizations_by_score(
            min_score=0, max_score=100
        )

        assert len(results) == 5  # Should get all

    def test_search_customizations_by_company(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test searching customizations by company name."""
        results = populated_database.search_customizations("TechCorp")

        assert len(results) == 2  # Should find company "TechCorp" occurrences
        assert all("TechCorp" in r["company"] for r in results)

    def test_search_customizations_by_job_title(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test searching customizations by job title."""
        results = populated_database.search_customizations("Engineer 1")

        assert len(results) >= 1
        assert any("Engineer 1" in r["job_title"] for r in results)

    def test_search_customizations_case_insensitive(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test that search is case-insensitive."""
        results_upper = populated_database.search_customizations("TECHCORP")
        results_lower = populated_database.search_customizations("techcorp")

        assert len(results_upper) == len(results_lower)

    def test_search_customizations_no_results(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test search with no matching results."""
        results = populated_database.search_customizations("NonExistent")

        assert len(results) == 0


class TestAnalytics:
    """Test analytics methods."""

    def test_get_analytics_summary(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test getting analytics summary."""
        analytics = populated_database.get_analytics_summary()

        assert analytics["total_customizations"] == 5
        assert isinstance(analytics["avg_match_score"], float)
        assert analytics["avg_match_score"] == 80.0  # (70+75+80+85+90)/5
        assert len(analytics["top_companies"]) <= 10
        assert "score_distribution" in analytics
        assert "customizations_by_month" in analytics

    def test_analytics_score_distribution(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test score distribution in analytics."""
        analytics = populated_database.get_analytics_summary()
        dist = analytics["score_distribution"]

        assert "excellent_90_plus" in dist
        assert "good_80_89" in dist
        assert "fair_70_79" in dist
        assert "poor_below_70" in dist

        # Based on test data: 70, 75, 80, 85, 90
        assert dist["excellent_90_plus"] == 1  # 90
        assert dist["good_80_89"] == 2  # 80, 85
        assert dist["fair_70_79"] == 2  # 70, 75
        assert dist["poor_below_70"] == 0

    def test_analytics_top_companies(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test top companies in analytics."""
        analytics = populated_database.get_analytics_summary()
        top_companies = analytics["top_companies"]

        assert len(top_companies) > 0
        assert all("company" in c and "count" in c for c in top_companies)
        # Should be ordered by count descending
        counts = [c["count"] for c in top_companies]
        assert counts == sorted(counts, reverse=True)

    def test_analytics_empty_database(self, database: CustomizationDatabase) -> None:
        """Test analytics with empty database."""
        analytics = database.get_analytics_summary()

        assert analytics["total_customizations"] == 0
        assert analytics["avg_match_score"] == 0.0
        assert len(analytics["top_companies"]) == 0

    def test_get_skill_gap_trends(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test skill gap analysis."""
        trends = populated_database.get_skill_gap_trends(limit=10)

        assert isinstance(trends, list)
        assert len(trends) <= 10
        # Should have Docker and Kubernetes from test data
        assert any(t["skill"] == "Docker" for t in trends)
        assert any(t["skill"] == "Kubernetes" for t in trends)
        # Should be ordered by gap_count descending
        if len(trends) > 1:
            counts = [t["gap_count"] for t in trends]
            assert counts == sorted(counts, reverse=True)

    def test_skill_gap_trends_with_limit(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test skill gap trends with custom limit."""
        trends = populated_database.get_skill_gap_trends(limit=1)

        assert len(trends) <= 1

    def test_skill_gap_trends_empty(self, database: CustomizationDatabase) -> None:
        """Test skill gap trends with no match results."""
        trends = database.get_skill_gap_trends()

        assert len(trends) == 0


class TestExport:
    """Test export functionality."""

    def test_export_to_json(self, populated_database: CustomizationDatabase) -> None:
        """Test exporting to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.json"
            stats = populated_database.export_to_json(str(output_path))

            assert stats["records_exported"] == 5
            assert Path(stats["output_path"]).exists()
            assert stats["file_size_bytes"] > 0

            # Verify JSON content
            with open(output_path) as f:
                data = json.load(f)

            assert "export_date" in data
            assert "filters" in data
            assert "analytics" in data
            assert "customizations" in data
            assert len(data["customizations"]) == 5

    def test_export_to_json_with_company_filter(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test exporting with company filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.json"
            stats = populated_database.export_to_json(
                str(output_path), company="TechCorp"
            )

            assert stats["records_exported"] == 2

            with open(output_path) as f:
                data = json.load(f)

            assert data["filters"]["company"] == "TechCorp"
            assert all(c["company"] == "TechCorp" for c in data["customizations"])

    def test_export_to_json_with_date_filter(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test exporting with date range filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.json"
            stats = populated_database.export_to_json(
                str(output_path),
                start_date="2024-01-16T00:00:00Z",
                end_date="2024-01-18T23:59:59Z",
            )

            assert stats["records_exported"] == 3

            with open(output_path) as f:
                data = json.load(f)

            assert data["filters"]["start_date"] == "2024-01-16T00:00:00Z"
            assert data["filters"]["end_date"] == "2024-01-18T23:59:59Z"

    def test_export_to_csv(self, populated_database: CustomizationDatabase) -> None:
        """Test exporting to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.csv"
            stats = populated_database.export_to_csv(str(output_path))

            assert stats["records_exported"] == 5
            assert Path(stats["output_path"]).exists()
            assert stats["file_size_bytes"] > 0

            # Verify CSV content
            import csv

            with open(output_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 5
            assert "customization_id" in rows[0]
            assert "company" in rows[0]
            assert "overall_score" in rows[0]

    def test_export_to_csv_with_filters(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test CSV export with filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.csv"
            stats = populated_database.export_to_csv(
                str(output_path), company="StartupXYZ"
            )

            assert stats["records_exported"] == 2

            import csv

            with open(output_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert all(r["company"] == "StartupXYZ" for r in rows)

    def test_export_to_csv_empty(self, database: CustomizationDatabase) -> None:
        """Test CSV export with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "export.csv"
            stats = database.export_to_csv(str(output_path))

            assert stats["records_exported"] == 0
            assert Path(stats["output_path"]).exists()
            assert stats["file_size_bytes"] == 0

    def test_export_creates_directory(
        self, populated_database: CustomizationDatabase
    ) -> None:
        """Test that export creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "export.json"
            stats = populated_database.export_to_json(str(output_path))

            assert Path(stats["output_path"]).exists()
            assert Path(stats["output_path"]).parent.exists()


class TestIntegration:
    """Test integration scenarios."""

    def test_complete_workflow(self, populated_database: CustomizationDatabase) -> None:
        """Test complete history & analytics workflow."""
        # 1. Query by date range
        date_results = populated_database.query_customizations_by_date_range(
            "2024-01-15T00:00:00Z", "2024-01-20T23:59:59Z"
        )
        assert len(date_results) > 0

        # 2. Query by score
        score_results = populated_database.query_customizations_by_score(80, 100)
        assert len(score_results) > 0

        # 3. Search
        search_results = populated_database.search_customizations("TechCorp")
        assert len(search_results) > 0

        # 4. Get analytics
        analytics = populated_database.get_analytics_summary()
        assert analytics["total_customizations"] > 0

        # 5. Get skill gaps
        trends = populated_database.get_skill_gap_trends()
        assert len(trends) > 0

        # 6. Export to JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "export.json"
            json_stats = populated_database.export_to_json(str(json_path))
            assert json_stats["records_exported"] > 0

            # 7. Export to CSV
            csv_path = Path(tmpdir) / "export.csv"
            csv_stats = populated_database.export_to_csv(str(csv_path))
            assert csv_stats["records_exported"] > 0
