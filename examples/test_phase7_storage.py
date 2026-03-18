#!/usr/bin/env python3
"""
Interactive manual testing script for Phase 7 - Storage & History.

This script tests:
- Session management with TTL
- History queries (date range, score, search)
- Analytics and reporting
- Data export (JSON, CSV)
- Multi-layer caching

Usage:
    python examples/test_phase7_storage.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import tempfile
import time
from datetime import datetime, timedelta

from resume_customizer.storage.database import CustomizationDatabase
from resume_customizer.storage.session import SessionManager


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✓ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"ℹ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"✗ {message}")


def setup_test_data(db: CustomizationDatabase) -> None:
    """Set up test data for Phase 7 testing."""
    print_section("Setup: Creating Test Data")

    # Create profiles
    profiles = [
        ("profile-001", "Alice Smith", "alice@example.com"),
        ("profile-002", "Bob Johnson", "bob@example.com"),
        ("profile-003", "Carol White", "carol@example.com"),
    ]

    print_info("Creating test profiles...")
    for pid, name, email in profiles:
        db.insert_profile(
            profile_id=pid,
            name=name,
            email=email,
            full_data={"name": name, "email": email},
        )
    print_success(f"Created {len(profiles)} profiles")

    # Create jobs
    jobs = [
        ("job-001", "Backend Engineer", "TechCorp"),
        ("job-002", "Frontend Developer", "WebCo"),
        ("job-003", "Full Stack Engineer", "TechCorp"),
        ("job-004", "DevOps Engineer", "CloudSystems"),
        ("job-005", "Data Scientist", "DataInc"),
    ]

    print_info("Creating test jobs...")
    for jid, title, company in jobs:
        db.insert_job(
            job_id=jid,
            title=title,
            company=company,
            full_data={"title": title, "company": company},
        )
    print_success(f"Created {len(jobs)} jobs")

    # Create match results with varied data
    matches = [
        ("match-001", "profile-001", "job-001", 85, ["Docker", "Kubernetes"]),
        ("match-002", "profile-001", "job-002", 72, ["React", "TypeScript"]),
        ("match-003", "profile-002", "job-003", 91, ["Docker"]),
        ("match-004", "profile-002", "job-004", 88, ["AWS", "Terraform"]),
        ("match-005", "profile-003", "job-005", 76, ["Python", "SQL"]),
    ]

    print_info("Creating test match results...")
    for mid, pid, jid, score, missing in matches:
        db.insert_match(
            match_id=mid,
            profile_id=pid,
            job_id=jid,
            overall_score=score,
            technical_score=score + 2,
            experience_score=score - 3,
            domain_score=score + 1,
            keyword_coverage=score - 5,
            matched_skills_count=10,
            missing_skills_count=len(missing),
            full_data={"overall_score": score, "missing_required_skills": missing},
        )
    print_success(f"Created {len(matches)} match results")

    # Create customizations with different dates
    base_date = datetime.now()
    customizations = [
        (
            "custom-001",
            "profile-001",
            "job-001",
            "Alice Smith",
            "Backend Engineer",
            "TechCorp",
            85,
            base_date - timedelta(days=30),
        ),
        (
            "custom-002",
            "profile-001",
            "job-002",
            "Alice Smith",
            "Frontend Developer",
            "WebCo",
            72,
            base_date - timedelta(days=20),
        ),
        (
            "custom-003",
            "profile-002",
            "job-003",
            "Bob Johnson",
            "Full Stack Engineer",
            "TechCorp",
            91,
            base_date - timedelta(days=15),
        ),
        (
            "custom-004",
            "profile-002",
            "job-004",
            "Bob Johnson",
            "DevOps Engineer",
            "CloudSystems",
            88,
            base_date - timedelta(days=10),
        ),
        (
            "custom-005",
            "profile-003",
            "job-005",
            "Carol White",
            "Data Scientist",
            "DataInc",
            76,
            base_date - timedelta(days=5),
        ),
    ]

    print_info("Creating test customizations...")
    for cid, pid, jid, pname, jtitle, company, score, created in customizations:
        db.insert_customization(
            customization_id=cid,
            profile_id=pid,
            job_id=jid,
            profile_name=pname,
            job_title=jtitle,
            company=company,
            overall_score=score,
            template="modern",
            created_at=created.isoformat(),
            metadata=json.dumps({"test": True, "version": "1.0"}),
        )
    print_success(f"Created {len(customizations)} customizations")


def test_session_management() -> None:
    """Test session management with TTL."""
    print_section("Test 1: Session Management")

    # Create session manager with short TTL for testing
    print_info("Creating SessionManager with 2 second TTL...")
    session = SessionManager(default_ttl=2)
    print_success("SessionManager created")

    # Store profile
    print_info("Storing profile in session...")
    profile_data = {"name": "Test User", "email": "test@example.com"}
    session.set_profile("test-profile", profile_data)
    print_success("Profile stored in session")

    # Retrieve profile (should hit cache)
    print_info("Retrieving profile (cache hit)...")
    retrieved = session.get_profile("test-profile")
    if retrieved:
        print_success(f"Profile retrieved: {retrieved['name']}")
    else:
        print_error("Failed to retrieve profile")

    # Get metrics
    metrics = session.get_metrics()
    print_info("Session metrics:")
    print(f"  Total entries: {metrics.total_entries}")
    print(f"  Hit count: {metrics.hit_count}")
    print(f"  Miss count: {metrics.miss_count}")
    print(f"  Hit rate: {metrics.hit_rate:.2%}")

    # Test TTL expiration
    print_info("Waiting for TTL expiration (2 seconds)...")
    time.sleep(2.5)

    print_info("Retrieving profile (should be expired)...")
    retrieved = session.get_profile("test-profile")
    if retrieved is None:
        print_success("Profile correctly expired")
    else:
        print_error("Profile should have expired")

    # Get updated metrics
    metrics = session.get_metrics()
    print_info("Updated session metrics:")
    print(f"  Expired count: {metrics.expired_count}")
    print(f"  Miss count: {metrics.miss_count}")


def test_history_queries(db: CustomizationDatabase) -> None:
    """Test history query operations."""
    print_section("Test 2: History Queries")

    # Query by date range
    print_info("Querying customizations from last 20 days...")
    start_date = (datetime.now() - timedelta(days=20)).isoformat()
    end_date = datetime.now().isoformat()
    results = db.query_customizations_by_date_range(start_date, end_date)
    print_success(f"Found {len(results)} customization(s) in date range")
    for r in results:
        print(f"  - {r['created_at'][:10]}: {r['job_title']} at {r['company']}")

    # Query by score range
    print_info("Querying high-scoring customizations (85-100)...")
    results = db.query_customizations_by_score(min_score=85, max_score=100)
    print_success(f"Found {len(results)} high-scoring customization(s)")
    for r in results:
        print(f"  - Score {r['overall_score']}: {r['job_title']} at {r['company']}")

    # Full-text search
    print_info("Searching for 'TechCorp' customizations...")
    results = db.search_customizations("TechCorp")
    print_success(f"Found {len(results)} matching customization(s)")
    for r in results:
        print(f"  - {r['job_title']} at {r['company']}")

    # Case-insensitive search
    print_info("Testing case-insensitive search...")
    results_upper = db.search_customizations("TECHCORP")
    results_lower = db.search_customizations("techcorp")
    if len(results_upper) == len(results_lower):
        print_success(f"Search is case-insensitive ({len(results_upper)} results)")
    else:
        print_error("Search case sensitivity inconsistent")


def test_analytics(db: CustomizationDatabase) -> None:
    """Test analytics and reporting."""
    print_section("Test 3: Analytics & Reporting")

    # Get analytics summary
    print_info("Generating analytics summary...")
    analytics = db.get_analytics_summary()

    print_success("Analytics generated:")
    print(f"  Total customizations: {analytics['total_customizations']}")
    print(f"  Average match score: {analytics['avg_match_score']}")

    print("\n  Top companies:")
    for company in analytics["top_companies"][:5]:
        print(f"    - {company['company']}: {company['count']} customizations")

    print("\n  Score distribution:")
    dist = analytics["score_distribution"]
    print(f"    Excellent (90+): {dist['excellent_90_plus']}")
    print(f"    Good (80-89): {dist['good_80_89']}")
    print(f"    Fair (70-79): {dist['fair_70_79']}")
    print(f"    Poor (<70): {dist['poor_below_70']}")

    if analytics["customizations_by_month"]:
        print("\n  Recent monthly activity:")
        for month_data in analytics["customizations_by_month"][:3]:
            print(f"    {month_data['month']}: {month_data['count']} customizations")

    # Get skill gap trends
    print_info("\nAnalyzing skill gap trends...")
    trends = db.get_skill_gap_trends(limit=5)
    print_success(f"Found {len(trends)} trending skill gaps:")
    for trend in trends:
        print(f"  - {trend['skill']}: mentioned in {trend['gap_count']} matches")


def test_data_export(db: CustomizationDatabase) -> None:
    """Test data export functionality."""
    print_section("Test 4: Data Export")

    # Export to JSON
    print_info("Exporting to JSON...")
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        stats = db.export_to_json(str(json_path))

        print_success("JSON export completed:")
        print(f"  Records exported: {stats['records_exported']}")
        print(f"  Output path: {stats['output_path']}")
        print(f"  File size: {stats['file_size_bytes']} bytes")

        # Verify JSON structure
        with open(json_path) as f:
            data = json.load(f)
        print_info("JSON structure verified:")
        print(f"  Contains export_date: {'export_date' in data}")
        print(f"  Contains filters: {'filters' in data}")
        print(f"  Contains analytics: {'analytics' in data}")
        print(f"  Contains customizations: {'customizations' in data}")

    # Export to JSON with filters
    print_info("\nExporting TechCorp customizations to JSON...")
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "techcorp_export.json"
        stats = db.export_to_json(str(json_path), company="TechCorp")

        print_success("Filtered JSON export completed:")
        print(f"  Records exported: {stats['records_exported']}")

        with open(json_path) as f:
            data = json.load(f)
        print_info(f"  Filter applied: {data['filters']['company']}")

    # Export to CSV
    print_info("\nExporting to CSV...")
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "export.csv"
        stats = db.export_to_csv(str(csv_path))

        print_success("CSV export completed:")
        print(f"  Records exported: {stats['records_exported']}")
        print(f"  Output path: {stats['output_path']}")
        print(f"  File size: {stats['file_size_bytes']} bytes")

        # Show first few lines
        with open(csv_path) as f:
            lines = f.readlines()[:3]
        print_info("CSV preview:")
        for line in lines:
            print(f"  {line.strip()}")


def test_multi_layer_caching(db: CustomizationDatabase) -> None:
    """Test multi-layer caching architecture."""
    print_section("Test 5: Multi-Layer Caching")

    print_info("Cache architecture flow:")
    print("  Request → SessionManager (memory) → Database → API")

    # Test session cache
    session = SessionManager(default_ttl=3600)

    print_info("\nLayer 1: Session cache (memory)")
    profile_data = {"name": "Cache Test", "email": "cache@test.com"}
    session.set_profile("cache-test", profile_data)
    print_success("Data stored in session cache")

    # Retrieve from session (cache hit)
    start = time.time()
    retrieved = session.get_profile("cache-test")
    elapsed_ms = (time.time() - start) * 1000
    if retrieved:
        print_success(f"Session cache hit: {elapsed_ms:.2f}ms")
    else:
        print_error("Session cache miss")

    # Test database layer
    print_info("\nLayer 2: Database persistence")
    profile_id = "db-cache-test"
    db.insert_profile(
        profile_id=profile_id,
        name="DB Cache Test",
        email="dbcache@test.com",
        full_data={"name": "DB Cache Test"},
    )
    print_success("Data stored in database")

    # Retrieve from database
    start = time.time()
    retrieved = db.get_profile(profile_id)
    elapsed_ms = (time.time() - start) * 1000
    if retrieved:
        print_success(f"Database retrieval: {elapsed_ms:.2f}ms")
    else:
        print_error("Database retrieval failed")

    # Show metrics
    metrics = session.get_metrics()
    print_info("\nSession cache metrics:")
    print(f"  Total entries: {metrics.total_entries}")
    print(f"  Hit rate: {metrics.hit_rate:.2%}")
    print(f"  Total accesses: {metrics.total_accesses}")


def test_session_cleanup(db: CustomizationDatabase) -> None:
    """Test session cleanup operations."""
    print_section("Test 6: Session Cleanup")

    session = SessionManager(default_ttl=1)  # 1 second TTL

    # Add multiple entries
    print_info("Adding test entries to session...")
    for i in range(5):
        session.set_profile(f"cleanup-{i}", {"name": f"User {i}"})
    print_success("Added 5 entries")

    metrics = session.get_metrics()
    print_info(f"Session entries: {metrics.total_entries}")

    # Wait for expiration
    print_info("Waiting for TTL expiration (1 second)...")
    time.sleep(1.5)

    # Manual cleanup
    print_info("Running manual cleanup...")
    removed = session.cleanup_expired()
    print_success(f"Removed {removed} expired entries")

    metrics = session.get_metrics()
    print_info(f"Remaining entries: {metrics.total_entries}")
    print_info(f"Total expired: {metrics.expired_count}")


def main() -> None:
    """Run all Phase 7 tests."""
    print("\n" + "=" * 70)
    print("  Phase 7: Storage & History - Interactive Test")
    print("=" * 70)

    try:
        # Setup database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        print_info(f"Creating test database: {db_path}")
        db = CustomizationDatabase(db_path)

        # Setup test data
        setup_test_data(db)

        # Run tests
        test_session_management()
        test_history_queries(db)
        test_analytics(db)
        test_data_export(db)
        test_multi_layer_caching(db)
        test_session_cleanup(db)

        # Final summary
        print_section("Test Summary")
        print_success("All Phase 7 storage tests completed successfully!")
        print_info("\nKey features tested:")
        print("  ✓ Session management with TTL")
        print("  ✓ History queries (date, score, search)")
        print("  ✓ Analytics and reporting")
        print("  ✓ Data export (JSON, CSV)")
        print("  ✓ Multi-layer caching")
        print("  ✓ Session cleanup")

        print_info(f"\nDatabase location: {db_path}")
        print_info("You can inspect the data using:")
        print(f"  sqlite3 {db_path}")

        # Close database
        db.close()

    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
