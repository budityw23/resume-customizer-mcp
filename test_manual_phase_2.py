#!/usr/bin/env python3
"""
Manual test script for Phase 2 - Resume Customizer MCP Server
Tests the complete workflow: load profile, load job, analyze match
"""

import json
from resume_customizer.mcp.handlers import (
    handle_load_user_profile,
    handle_load_job_description,
    handle_analyze_match,
)


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


def test_complete_workflow():
    """Test the complete workflow with Budi's resume and sample jobs."""

    print_separator("PHASE 2 MANUAL TEST - COMPLETE WORKFLOW")

    # Step 1: Load profile
    print("Step 1: Loading user profile...")
    print("File: examples/budi_resume.md")

    profile_result = handle_load_user_profile({
        "file_path": "examples/budi_resume.md"
    })

    if profile_result.get("status") == "error":
        print(f"❌ Error loading profile: {profile_result.get('message')}")
        return

    print(f"✅ Profile loaded successfully!")
    print(f"   Name: {profile_result.get('name')}")
    print(f"   Profile ID: {profile_result.get('profile_id')}")
    print(f"   Skills: {profile_result.get('skills_count')} skills")
    print(f"   Experience: {profile_result.get('experiences_count')} positions")

    # Step 2: Test with Backend Engineer job
    print_separator("Step 2: Testing with Senior Backend Engineer Job")
    print("File: examples/senior_backend_job.md")

    job_result = handle_load_job_description({
        "file_path": "examples/senior_backend_job.md"
    })

    if job_result.get("status") == "error":
        print(f"❌ Error loading job: {job_result.get('message')}")
        return

    print(f"✅ Job loaded successfully!")
    print(f"   Title: {job_result.get('title')}")
    print(f"   Job ID: {job_result.get('job_id')}")
    print(f"   Required Skills: {job_result.get('required_skills_count')} skills")

    # Step 3: Analyze match
    print_separator("Step 3: Analyzing Match")

    match_result = handle_analyze_match({
        "profile_id": profile_result['profile_id'],
        "job_id": job_result['job_id'],
    })

    if match_result.get("status") == "error":
        print(f"❌ Error analyzing match: {match_result.get('message')}")
        return

    print(f"✅ Match analysis completed!\n")

    # Display results
    print_separator("MATCH RESULTS - SENIOR BACKEND ENGINEER")

    print(f"🎯 Overall Match Score: {match_result['overall_score']:.1f}%\n")

    print("📊 Score Breakdown:")
    breakdown = match_result['breakdown']
    print(f"   • Technical Skills:  {breakdown['technical_skills_score']:.1f}%")
    print(f"   • Experience Level:  {breakdown['experience_score']:.1f}%")
    print(f"   • Domain Match:      {breakdown['domain_score']:.1f}%")
    print(f"   • Keywords:          {breakdown['keyword_coverage_score']:.1f}%")

    print(f"\n✅ Matched Skills ({breakdown['matched_skills_count']}/{breakdown['total_required_skills']}):")
    for skill in match_result['matched_skills'][:10]:  # Show first 10
        print(f"   • {skill}")

    if match_result['missing_required_skills']:
        print(f"\n⚠️  Missing Required Skills ({len(match_result['missing_required_skills'])}):")
        for skill in match_result['missing_required_skills'][:5]:  # Show first 5
            print(f"   • {skill}")

    print(f"\n💡 Top Achievements ({len(match_result['top_achievements'])}):")
    for i, achievement in enumerate(match_result['top_achievements'][:5], 1):
        print(f"   {i}. {achievement['text'][:100]}...")
        print(f"      Score: {achievement['score']:.2f}, Matched Keywords: {len(achievement['matched_keywords'])}")

    if match_result['suggestions']:
        print(f"\n📝 Suggestions:")
        for suggestion in match_result['suggestions'][:3]:  # Show first 3
            print(f"   • {suggestion}")

    # Step 4: Test with Full Stack Engineer job
    print_separator("Step 4: Testing with Full Stack Engineer Job")
    print("File: examples/fullstack_engineer_job.md")

    job_result2 = handle_load_job_description({
        "file_path": "examples/fullstack_engineer_job.md"
    })

    if job_result2.get("status") == "error":
        print(f"❌ Error loading job: {job_result2.get('message')}")
        return

    print(f"✅ Job loaded successfully!")
    print(f"   Title: {job_result2.get('title')}")
    print(f"   Job ID: {job_result2.get('job_id')}")

    match_result2 = handle_analyze_match({
        "profile_id": profile_result['profile_id'],
        "job_id": job_result2['job_id'],
    })

    if match_result2.get("status") == "error":
        print(f"❌ Error analyzing match: {match_result2.get('message')}")
        return

    print(f"✅ Match analysis completed!\n")

    print_separator("MATCH RESULTS - FULL STACK ENGINEER")

    print(f"🎯 Overall Match Score: {match_result2['overall_score']:.1f}%\n")

    print("📊 Score Breakdown:")
    breakdown2 = match_result2['breakdown']
    print(f"   • Technical Skills:  {breakdown2['technical_skills_score']:.1f}%")
    print(f"   • Experience Level:  {breakdown2['experience_score']:.1f}%")
    print(f"   • Domain Match:      {breakdown2['domain_score']:.1f}%")
    print(f"   • Keywords:          {breakdown2['keyword_coverage_score']:.1f}%")

    print(f"\n✅ Matched Skills ({breakdown2['matched_skills_count']}/{breakdown2['total_required_skills']}):")
    for skill in match_result2['matched_skills'][:10]:
        print(f"   • {skill}")

    if match_result2['missing_required_skills']:
        print(f"\n⚠️  Missing Required Skills ({len(match_result2['missing_required_skills'])}):")
        for skill in match_result2['missing_required_skills'][:5]:
            print(f"   • {skill}")

    # Summary comparison
    print_separator("COMPARISON SUMMARY")

    print(f"Backend Engineer Job:    {match_result['overall_score']:.1f}%")
    print(f"Full Stack Engineer Job: {match_result2['overall_score']:.1f}%")

    best_match = "Backend Engineer" if match_result['overall_score'] > match_result2['overall_score'] else "Full Stack Engineer"
    print(f"\n🏆 Best Match: {best_match}")

    print_separator("TEST COMPLETED SUCCESSFULLY")


def test_error_handling():
    """Test error handling scenarios."""

    print_separator("TESTING ERROR HANDLING")

    # Test 1: Invalid file path
    print("Test 1: Loading non-existent file...")
    result = handle_load_user_profile({"file_path": "nonexistent.md"})
    if result.get("status") == "error":
        print(f"✅ Correctly handled: {result.get('message')}\n")
    else:
        print(f"❌ Should have returned error\n")

    # Test 2: Missing parameters
    print("Test 2: Analyzing match with missing parameters...")
    result = handle_analyze_match({"profile_id": "test-123"})
    if result.get("status") == "error":
        print(f"✅ Correctly handled: {result.get('message')}\n")
    else:
        print(f"❌ Should have returned error\n")

    # Test 3: Non-existent IDs
    print("Test 3: Analyzing match with non-existent IDs...")
    result = handle_analyze_match({
        "profile_id": "fake-id-123",
        "job_id": "fake-job-456"
    })
    if result.get("status") == "error":
        print(f"✅ Correctly handled: {result.get('message')}\n")
    else:
        print(f"❌ Should have returned error\n")

    print("Error handling tests completed!\n")


if __name__ == "__main__":
    try:
        # Run complete workflow test
        test_complete_workflow()

        # Run error handling tests
        test_error_handling()

        print("\n✅ All tests completed successfully!")
        print("\nNote: Make sure you have downloaded the spaCy model:")
        print("  python -m spacy download en_core_web_sm")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
