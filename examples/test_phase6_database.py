#!/usr/bin/env python3
"""
Interactive manual testing script for Phase 6 - Database Persistence.

This script tests:
- Profile storage and retrieval
- Job storage and retrieval
- Match result storage and retrieval
- Customization storage and retrieval
- Foreign key constraints
- Database indexes

Usage:
    python examples/test_phase6_database.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import tempfile
from datetime import datetime

from resume_customizer.storage.database import CustomizationDatabase


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


def test_database_initialization() -> CustomizationDatabase:
    """Test database initialization."""
    print_section("Test 1: Database Initialization")

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    print_info(f"Creating database at: {db_path}")
    db = CustomizationDatabase(db_path)

    print_success("Database created successfully")
    print_info(f"Database path: {db.db_path}")

    return db


def test_profile_operations(db: CustomizationDatabase) -> str:
    """Test profile CRUD operations."""
    print_section("Test 2: Profile Operations")

    # Insert profile
    profile_id = "profile-test-001"
    profile_data = {
        "profile_id": profile_id,
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0123",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/janedoe",
        "github": "https://github.com/janedoe",
        "website": "https://janedoe.dev",
        "summary": "Senior Software Engineer with 8 years of experience",
        "skills_count": 15,
        "experiences_count": 3,
        "education_count": 1,
        "certifications_count": 2,
        "full_data": {
            "name": "Jane Doe",
            "skills": ["Python", "JavaScript", "SQL", "Docker"],
            "experiences": [],
        },
    }

    print_info("Inserting profile...")
    db.insert_profile(**profile_data)
    print_success(f"Profile inserted: {profile_id}")

    # Retrieve profile
    print_info("Retrieving profile...")
    retrieved = db.get_profile(profile_id)
    if retrieved:
        print_success(f"Profile retrieved: {retrieved['name']}")
        print(f"  Email: {retrieved['email']}")
        print(f"  Skills count: {retrieved['skills_count']}")
        print(f"  Full data: {json.dumps(retrieved['full_data'], indent=2)}")
    else:
        print_error("Failed to retrieve profile")

    # Update profile
    print_info("Updating profile...")
    updated = db.update_profile(
        profile_id=profile_id,
        full_data={"name": "Jane Doe", "skills": ["Python", "Go", "Rust"]},
        skills_count=20,
        summary="Senior Software Engineer with 10 years of experience",
    )
    if updated:
        print_success("Profile updated")
        retrieved = db.get_profile(profile_id)
        print(f"  New skills count: {retrieved['skills_count']}")
        print(f"  New summary: {retrieved['summary']}")
    else:
        print_error("Failed to update profile")

    return profile_id


def test_job_operations(db: CustomizationDatabase) -> str:
    """Test job CRUD operations."""
    print_section("Test 3: Job Operations")

    # Insert job
    job_id = "job-test-001"
    job_data = {
        "job_id": job_id,
        "title": "Senior Backend Engineer",
        "company": "TechCorp Inc.",
        "location": "Remote",
        "job_type": "Full-time",
        "experience_level": "Senior",
        "salary_range": "$150k-$200k",
        "required_skills_count": 8,
        "preferred_skills_count": 5,
        "full_data": {
            "title": "Senior Backend Engineer",
            "company": "TechCorp Inc.",
            "requirements": {"required_skills": ["Python", "SQL", "Docker"]},
        },
    }

    print_info("Inserting job...")
    db.insert_job(**job_data)
    print_success(f"Job inserted: {job_id}")

    # Retrieve job
    print_info("Retrieving job...")
    retrieved = db.get_job(job_id)
    if retrieved:
        print_success(f"Job retrieved: {retrieved['title']} at {retrieved['company']}")
        print(f"  Location: {retrieved['location']}")
        print(f"  Salary range: {retrieved['salary_range']}")
        print(f"  Required skills: {retrieved['required_skills_count']}")
    else:
        print_error("Failed to retrieve job")

    # Update job
    print_info("Updating job...")
    updated = db.update_job(
        job_id=job_id,
        full_data={"title": "Staff Engineer", "company": "TechCorp Inc."},
        title="Staff Engineer",
        salary_range="$180k-$230k",
    )
    if updated:
        print_success("Job updated")
        retrieved = db.get_job(job_id)
        print(f"  New title: {retrieved['title']}")
        print(f"  New salary: {retrieved['salary_range']}")
    else:
        print_error("Failed to update job")

    return job_id


def test_match_operations(
    db: CustomizationDatabase, profile_id: str, job_id: str
) -> str:
    """Test match result operations."""
    print_section("Test 4: Match Result Operations")

    # Insert match result
    match_id = "match-test-001"
    match_data = {
        "match_id": match_id,
        "profile_id": profile_id,
        "job_id": job_id,
        "overall_score": 87,
        "technical_score": 90,
        "experience_score": 85,
        "domain_score": 88,
        "keyword_coverage": 82,
        "matched_skills_count": 12,
        "missing_skills_count": 3,
        "full_data": {
            "overall_score": 87,
            "matched_skills": ["Python", "SQL", "Docker"],
            "missing_required_skills": ["Kubernetes", "AWS", "Redis"],
        },
    }

    print_info("Inserting match result...")
    db.insert_match(**match_data)
    print_success(f"Match result inserted: {match_id}")

    # Retrieve match result
    print_info("Retrieving match result...")
    retrieved = db.get_match(match_id)
    if retrieved:
        print_success(f"Match result retrieved: {retrieved['overall_score']}% match")
        print(f"  Technical score: {retrieved['technical_score']}")
        print(f"  Experience score: {retrieved['experience_score']}")
        print(f"  Matched skills: {retrieved['matched_skills_count']}")
        print(f"  Missing skills: {retrieved['missing_skills_count']}")
        print(f"  Missing: {retrieved['full_data']['missing_required_skills']}")
    else:
        print_error("Failed to retrieve match result")

    return match_id


def test_customization_operations(
    db: CustomizationDatabase, profile_id: str, job_id: str
) -> str:
    """Test customization operations."""
    print_section("Test 5: Customization Operations")

    # Insert customization
    customization_id = "custom-test-001"
    customization_data = {
        "customization_id": customization_id,
        "profile_id": profile_id,
        "job_id": job_id,
        "profile_name": "Jane Doe",
        "job_title": "Staff Engineer",
        "company": "TechCorp Inc.",
        "overall_score": 87,
        "template": "modern",
        "created_at": datetime.now().isoformat(),
        "metadata": json.dumps({"version": "1.0", "test": True}),
    }

    print_info("Inserting customization...")
    db.insert_customization(**customization_data)
    print_success(f"Customization inserted: {customization_id}")

    # Retrieve customization
    print_info("Retrieving customization...")
    retrieved = db.get_customization_by_id(customization_id)
    if retrieved:
        print_success(
            f"Customization retrieved: {retrieved['profile_name']} → {retrieved['job_title']}"
        )
        print(f"  Company: {retrieved['company']}")
        print(f"  Score: {retrieved['overall_score']}")
        print(f"  Template: {retrieved['template']}")
        print(f"  Metadata: {retrieved['metadata']}")
    else:
        print_error("Failed to retrieve customization")

    # Get all customizations
    print_info("Retrieving all customizations...")
    all_customizations = db.get_customizations()
    print_success(f"Found {len(all_customizations)} customization(s)")
    for c in all_customizations:
        print(f"  - {c['customization_id']}: {c['job_title']} at {c['company']}")

    return customization_id


def test_foreign_key_constraints(db: CustomizationDatabase, profile_id: str) -> None:
    """Test foreign key constraints."""
    print_section("Test 6: Foreign Key Constraints")

    print_info("Testing foreign key constraint enforcement...")
    print_info("Attempting to delete profile with customizations...")

    try:
        db.delete_profile(profile_id)
        print_error("Foreign key constraint NOT enforced (unexpected)")
    except Exception as e:
        print_success(f"Foreign key constraint enforced: {type(e).__name__}")
        print(f"  Error: {str(e)}")


def test_database_queries(db: CustomizationDatabase) -> None:
    """Test database query operations."""
    print_section("Test 7: Database Queries")

    # Query by company
    print_info("Querying customizations by company...")
    results = db.get_customizations(company="TechCorp Inc.")
    print_success(f"Found {len(results)} customization(s) for TechCorp Inc.")

    # Query by score (using Phase 7.3 method)
    print_info("Querying customizations with score >= 80...")
    results = db.query_customizations_by_score(min_score=80)
    print_success(f"Found {len(results)} high-scoring customization(s)")
    for r in results:
        print(f"  - {r['job_title']}: {r['overall_score']}%")


def test_database_cleanup(db: CustomizationDatabase, customization_id: str) -> None:
    """Test database cleanup operations."""
    print_section("Test 8: Database Cleanup")

    print_info("Deleting customization...")
    deleted = db.delete_customization(customization_id)
    if deleted:
        print_success(f"Customization deleted: {customization_id}")
    else:
        print_error("Failed to delete customization")

    # Verify deletion
    print_info("Verifying deletion...")
    retrieved = db.get_customization_by_id(customization_id)
    if retrieved is None:
        print_success("Customization successfully deleted")
    else:
        print_error("Customization still exists")


def test_database_context_manager(db_path: Path) -> None:
    """Test database context manager."""
    print_section("Test 9: Database Context Manager")

    print_info("Testing database as context manager...")

    # Create profile and job for the test
    with CustomizationDatabase(db_path) as db:
        db.insert_profile(
            profile_id="ctx-profile",
            name="Context Test",
            email="ctx@test.com",
            full_data={"name": "Context Test"},
        )
        db.insert_job(
            job_id="ctx-job",
            title="Test Job",
            company="TestCo",
            full_data={"title": "Test Job"},
        )
        db.insert_customization(
            customization_id="ctx-test",
            profile_id="ctx-profile",
            job_id="ctx-job",
            profile_name="Context Test",
            job_title="Test Job",
            company="TestCo",
            overall_score=75,
            template="minimal",
            created_at=datetime.now().isoformat(),
        )
        print_success("Data written within context manager")

    # Verify data persists after context exit
    with CustomizationDatabase(db_path) as db:
        retrieved = db.get_customization_by_id("ctx-test")
        if retrieved:
            print_success("Data persisted after context manager exit")
            print(f"  Retrieved: {retrieved['customization_id']}")
        else:
            print_error("Data not persisted")


def main() -> None:
    """Run all Phase 6 tests."""
    print("\n" + "=" * 70)
    print("  Phase 6: Database Persistence - Interactive Test")
    print("=" * 70)

    try:
        # Test 1: Initialize database
        db = test_database_initialization()

        # Test 2: Profile operations
        profile_id = test_profile_operations(db)

        # Test 3: Job operations
        job_id = test_job_operations(db)

        # Test 4: Match operations
        match_id = test_match_operations(db, profile_id, job_id)

        # Test 5: Customization operations
        customization_id = test_customization_operations(db, profile_id, job_id)

        # Test 6: Foreign key constraints
        test_foreign_key_constraints(db, profile_id)

        # Test 7: Database queries
        test_database_queries(db)

        # Test 8: Database cleanup
        test_database_cleanup(db, customization_id)

        # Test 9: Context manager
        test_database_context_manager(db.db_path)

        # Final summary
        print_section("Test Summary")
        print_success("All Phase 6 database tests completed successfully!")
        print_info(f"Database location: {db.db_path}")
        print_info("You can inspect the database using:")
        print(f"  sqlite3 {db.db_path}")
        print_info("To view tables:")
        print("  .tables")
        print_info("To view customizations:")
        print("  SELECT * FROM customizations;")

        # Close database
        db.close()

    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
