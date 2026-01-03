#!/usr/bin/env python3
"""
Manual test script for Phase 6 MCP handlers.

Run this script to test the Phase 6 functionality without the MCP server.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_customizer.mcp.handlers import (
    handle_analyze_match,
    handle_customize_resume,
    handle_list_customizations,
    handle_load_job_description,
    handle_load_user_profile,
)


def test_phase6():
    """Test Phase 6 handlers manually."""
    print("=" * 60)
    print("Phase 6 Manual Test")
    print("=" * 60)

    # Step 1: Load user profile
    print("\n1. Loading user profile...")
    profile_result = handle_load_user_profile({
        "file_path": "tests/fixtures/test_resume.md"
    })
    print(f"   Status: {profile_result['status']}")
    if profile_result['status'] == 'success':
        print(f"   Profile ID: {profile_result['profile_id']}")
        print(f"   Name: {profile_result['name']}")
        print(f"   Skills: {profile_result['skills_count']}")
        print(f"   Experiences: {profile_result['experiences_count']}")
        profile_id = profile_result['profile_id']
    else:
        print(f"   Error: {profile_result['message']}")
        return

    # Step 2: Load job description
    print("\n2. Loading job description...")
    job_result = handle_load_job_description({
        "file_path": "tests/fixtures/test_job.md"
    })
    print(f"   Status: {job_result['status']}")
    if job_result['status'] == 'success':
        print(f"   Job ID: {job_result['job_id']}")
        print(f"   Title: {job_result['title']}")
        print(f"   Company: {job_result['company']}")
        print(f"   Required Skills: {job_result['required_skills_count']}")
        job_id = job_result['job_id']
    else:
        print(f"   Error: {job_result['message']}")
        return

    # Step 3: Analyze match
    print("\n3. Analyzing match...")
    match_result = handle_analyze_match({
        "profile_id": profile_id,
        "job_id": job_id,
    })
    print(f"   Status: {match_result['status']}")
    if match_result['status'] == 'success':
        print(f"   Match ID: {match_result['match_id']}")
        print(f"   Overall Score: {match_result['overall_score']}%")
        print(f"   Matched Skills: {match_result['matched_skills_count']}")
        print(f"   Missing Skills: {len(match_result['missing_required_skills'])}")
        match_id = match_result['match_id']
    else:
        print(f"   Error: {match_result['message']}")
        return

    # Step 4: Customize resume
    print("\n4. Customizing resume...")
    customize_result = handle_customize_resume({
        "match_id": match_id,
        "preferences": {
            "achievements_per_role": 3,
            "max_skills": 10,
            "template": "modern",
        }
    })
    print(f"   Status: {customize_result['status']}")
    if customize_result['status'] == 'success':
        print(f"   Customization ID: {customize_result['customization_id']}")
        print(f"   Template: {customize_result['template']}")
        print(f"   Experiences: {customize_result['experiences_count']}")
        print(f"   Skills: {customize_result['skills_count']}")
    else:
        print(f"   Error: {customize_result['message']}")
        return

    # Step 5: List customizations
    print("\n5. Listing customizations...")
    list_result = handle_list_customizations({})
    print(f"   Status: {list_result['status']}")
    if list_result['status'] == 'success':
        print(f"   Count: {list_result['count']}")
        if list_result['customizations']:
            for i, custom in enumerate(list_result['customizations'], 1):
                print(f"\n   Customization {i}:")
                print(f"     ID: {custom['customization_id']}")
                print(f"     Name: {custom['profile_name']}")
                print(f"     Company: {custom['company']}")
                print(f"     Score: {custom['overall_score']}%")
                print(f"     Created: {custom['created_at']}")
    else:
        print(f"   Error: {list_result['message']}")

    # Step 6: Test error handling
    print("\n6. Testing error handling...")
    print("   a) Invalid file path:")
    error_result = handle_load_user_profile({"file_path": "/nonexistent.md"})
    print(f"      Status: {error_result['status']}")
    print(f"      Message: {error_result['message']}")
    if 'suggestion' in error_result:
        print(f"      Suggestion: {error_result['suggestion']}")

    print("\n   b) Missing parameter:")
    error_result = handle_analyze_match({"profile_id": profile_id})
    print(f"      Status: {error_result['status']}")
    print(f"      Message: {error_result['message']}")
    if 'suggestion' in error_result:
        print(f"      Suggestion: {error_result['suggestion']}")

    print("\n" + "=" * 60)
    print("Phase 6 Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase6()
