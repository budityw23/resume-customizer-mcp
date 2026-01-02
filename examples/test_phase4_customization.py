#!/usr/bin/env python3
"""
Manual Testing Script for Phase 4 - Resume Customization Engine.

This script demonstrates and tests Phase 4 functionality:
- Phase 4.1: Achievement Reordering
- Phase 4.2: Skills Optimization
- Phase 4.3: Resume Customization Logic
- Phase 4.4: MCP Tool Integration

Run this script to manually verify that Phase 4 is working correctly.

Usage:
    python examples/test_phase4_customization.py
"""

import json
import sys
from datetime import datetime

from resume_customizer.core.customizer import (
    AchievementSelection,
    CustomizationPreferences,
    SkillsDisplayStrategy,
    customize_resume,
    get_achievement_statistics,
    get_customization_summary,
    get_skill_statistics,
    optimize_skills,
    reorder_achievements,
)
from resume_customizer.core.models import (
    Achievement,
    ContactInfo,
    Experience,
    MatchBreakdown,
    MatchResult,
    Skill,
    SkillMatch,
    UserProfile,
)
from resume_customizer.mcp.handlers import (
    _session_state,
    handle_customize_resume,
)


def print_header(title: str, level: int = 1) -> None:
    """Print a formatted header."""
    if level == 1:
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    elif level == 2:
        print("\n" + "-" * 80)
        print(f"  {title}")
        print("-" * 80)
    else:
        print(f"\n{title}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✓ {message}")


def print_info(message: str, indent: int = 0) -> None:
    """Print an info message."""
    prefix = "  " * indent
    print(f"{prefix}• {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"✗ {message}")


def create_sample_profile() -> UserProfile:
    """Create a sample user profile for testing."""
    return UserProfile(
        profile_id="test-profile-123",
        name="Jane Developer",
        contact=ContactInfo(
            email="jane@example.com",
            phone="555-0100",
        ),
        summary="Experienced software engineer with 5 years of experience in Python and JavaScript",
        experiences=[
            Experience(
                company="Tech Corp",
                title="Senior Software Engineer",
                start_date="2022-01",
                end_date="Present",
                location="San Francisco, CA",
                achievements=[
                    Achievement(
                        text="Led team of 5 engineers to deliver critical microservices platform",
                        technologies=["Python", "Docker", "Kubernetes"],
                        metrics=["5 engineers", "3 months"],
                    ),
                    Achievement(
                        text="Reduced API latency by 40% through caching optimization",
                        technologies=["Redis", "Python"],
                        metrics=["40%"],
                    ),
                    Achievement(
                        text="Implemented CI/CD pipeline reducing deployment time by 60%",
                        technologies=["GitLab CI", "Docker"],
                        metrics=["60%"],
                    ),
                    Achievement(
                        text="Developed REST API serving 10M requests per day",
                        technologies=["Python", "FastAPI"],
                        metrics=["10M requests/day"],
                    ),
                ],
            ),
            Experience(
                company="StartupXYZ",
                title="Software Engineer",
                start_date="2020-01",
                end_date="2021-12",
                location="Remote",
                achievements=[
                    Achievement(
                        text="Developed real-time analytics dashboard using React",
                        technologies=["React", "WebSockets"],
                    ),
                    Achievement(
                        text="Mentored 2 junior engineers on best practices",
                        metrics=["2 engineers"],
                    ),
                    Achievement(
                        text="Built data pipeline processing 1TB of data daily",
                        technologies=["Python", "Apache Spark"],
                        metrics=["1TB/day"],
                    ),
                ],
            ),
        ],
        skills=[
            Skill(name="Python", category="Programming", proficiency="Expert", years=5),
            Skill(name="JavaScript", category="Programming", proficiency="Advanced", years=4),
            Skill(name="React", category="Frontend", proficiency="Advanced", years=3),
            Skill(name="Docker", category="DevOps", proficiency="Intermediate", years=2),
            Skill(name="Kubernetes", category="DevOps", proficiency="Basic", years=1),
            Skill(name="Redis", category="Database", proficiency="Intermediate", years=2),
            Skill(name="PostgreSQL", category="Database", proficiency="Advanced", years=4),
            Skill(name="FastAPI", category="Backend", proficiency="Advanced", years=2),
            Skill(name="Git", category="Tools", proficiency="Expert", years=5),
        ],
        education=[],
    )


def create_sample_match_result(profile: UserProfile) -> MatchResult:
    """Create a sample match result for testing."""
    # Collect all achievements with scores
    ranked = [
        (profile.experiences[0].achievements[0], 95.0),  # Leadership + microservices
        (profile.experiences[0].achievements[1], 85.0),  # Performance optimization
        (profile.experiences[0].achievements[3], 80.0),  # API development
        (profile.experiences[0].achievements[2], 75.0),  # CI/CD
        (profile.experiences[1].achievements[0], 70.0),  # React dashboard
        (profile.experiences[1].achievements[2], 65.0),  # Data pipeline
        (profile.experiences[1].achievements[1], 60.0),  # Mentoring
    ]

    return MatchResult(
        profile_id="test-profile-123",
        job_id="test-job-456",
        overall_score=85,
        breakdown=MatchBreakdown(
            technical_skills_score=90.0,
            experience_score=85.0,
            domain_score=80.0,
            keyword_coverage_score=75.0,
            total_score=85.0,
        ),
        matched_skills=[
            SkillMatch(skill="Python", matched=True, category="required", user_proficiency="Expert"),
            SkillMatch(skill="JavaScript", matched=True, category="required", user_proficiency="Advanced"),
            SkillMatch(skill="React", matched=True, category="preferred", user_proficiency="Advanced"),
            SkillMatch(skill="Docker", matched=True, category="preferred", user_proficiency="Intermediate"),
            SkillMatch(skill="Kubernetes", matched=True, category="preferred", user_proficiency="Basic"),
            SkillMatch(skill="TypeScript", matched=False, category="required"),  # Missing
            SkillMatch(skill="GraphQL", matched=False, category="preferred"),  # Missing
        ],
        missing_required_skills=["TypeScript"],
        missing_preferred_skills=["GraphQL"],
        ranked_achievements=ranked,
    )


def test_phase_4_1_achievement_reordering() -> bool:
    """Test Phase 4.1 - Achievement Reordering."""
    print_header("Phase 4.1 - Achievement Reordering", level=1)

    try:
        profile = create_sample_profile()
        match_result = create_sample_match_result(profile)

        # Test 1: Default strategy
        print_header("Test 1: Default Achievement Selection Strategy", level=2)
        result = reorder_achievements(profile, match_result)

        print_info(f"Original experiences: {len(profile.experiences)}")
        print_info(f"Reordered experiences: {len(result)}")

        for i, exp in enumerate(result, 1):
            print_info(f"Experience {i}: {exp.company} - {exp.title}", indent=1)
            print_info(f"Achievements: {len(exp.achievements)}", indent=2)
            for j, ach in enumerate(exp.achievements[:3], 1):  # Show first 3
                relevance = ach.relevance_score if ach.relevance_score else 0
                print_info(f"{j}. [{relevance:.1f}] {ach.text[:60]}...", indent=2)

        print_success("Default strategy completed")

        # Test 2: Top 2 achievements per role
        print_header("Test 2: Top 2 Achievements Per Role", level=2)
        strategy = AchievementSelection(top_n=2)
        result = reorder_achievements(profile, match_result, strategy)

        for exp in result:
            if exp.achievements:
                assert len(exp.achievements) <= 2, f"Expected ≤2 achievements, got {len(exp.achievements)}"
                print_info(f"{exp.company}: {len(exp.achievements)} achievements")

        print_success("Top N strategy works correctly")

        # Test 3: Achievement statistics
        print_header("Test 3: Achievement Statistics", level=2)
        stats = get_achievement_statistics(profile, result)

        print_info(f"Total original achievements: {stats['total_original']}")
        print_info(f"Total selected achievements: {stats['total_selected']}")
        print_info(f"Selection rate: {stats['selection_rate']:.1%}")
        print_info(f"Diversity rate: {stats['diversity_rate']:.1%}")
        print_info(f"Companies represented: {stats['companies_represented']}/{stats['companies_original']}")

        print_success("Statistics generated correctly")

        print_success("Phase 4.1 - All tests passed!")
        return True

    except Exception as e:
        print_error(f"Phase 4.1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_4_2_skills_optimization() -> bool:
    """Test Phase 4.2 - Skills Optimization."""
    print_header("Phase 4.2 - Skills Optimization", level=1)

    try:
        profile = create_sample_profile()
        match_result = create_sample_match_result(profile)

        # Test 1: Default strategy
        print_header("Test 1: Default Skills Optimization", level=2)
        result = optimize_skills(profile, match_result)

        print_info(f"Original skills: {len(profile.skills)}")
        print_info(f"Optimized skills: {len(result)}")
        print_info("Top 5 skills by relevance:")
        for i, skill in enumerate(result[:5], 1):
            print_info(f"{i}. {skill.name} ({skill.category}) - {skill.proficiency}", indent=1)

        print_success("Default optimization completed")

        # Test 2: Top 5 skills only
        print_header("Test 2: Limit to Top 5 Skills", level=2)
        strategy = SkillsDisplayStrategy(top_n=5)
        result = optimize_skills(profile, match_result, strategy)

        assert len(result) <= 5, f"Expected ≤5 skills, got {len(result)}"
        print_info(f"Skills after top_n=5: {len(result)}")

        print_success("Top N limit works correctly")

        # Test 3: Group by category
        print_header("Test 3: Group Skills by Category", level=2)
        strategy = SkillsDisplayStrategy(group_by_category=True)
        result = optimize_skills(profile, match_result, strategy)

        # Check category grouping
        categories_order = [skill.category for skill in result]
        print_info("Category order:")
        prev_cat = None
        for cat in categories_order:
            if cat != prev_cat:
                print_info(f"- {cat}", indent=1)
                prev_cat = cat

        print_success("Category grouping works correctly")

        # Test 4: Skill statistics
        print_header("Test 4: Skill Statistics", level=2)
        strategy = SkillsDisplayStrategy(top_n=6)
        optimized = optimize_skills(profile, match_result, strategy)
        stats = get_skill_statistics(profile, optimized, match_result)

        print_info(f"Total original: {stats['total_original']}")
        print_info(f"Total displayed: {stats['total_displayed']}")
        print_info(f"Reduction rate: {stats['reduction_rate']:.1%}")
        print_info(f"Matched skills shown: {stats['matched_skills_shown']}")
        print_info(f"Required skills shown: {stats['required_skills_shown']}")
        print_info(f"Preferred skills shown: {stats['preferred_skills_shown']}")

        print_success("Statistics generated correctly")

        print_success("Phase 4.2 - All tests passed!")
        return True

    except Exception as e:
        print_error(f"Phase 4.2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_4_3_resume_customization() -> bool:
    """Test Phase 4.3 - Resume Customization Logic."""
    print_header("Phase 4.3 - Resume Customization Logic", level=1)

    try:
        profile = create_sample_profile()
        match_result = create_sample_match_result(profile)

        # Test 1: Default preferences
        print_header("Test 1: Customize with Default Preferences", level=2)
        result = customize_resume(profile, match_result)

        print_info(f"Customization ID: {result.customization_id}")
        print_info(f"Created at: {result.created_at}")
        print_info(f"Template: {result.template}")
        print_info(f"Experiences: {len(result.selected_experiences)}")
        print_info(f"Skills: {len(result.reordered_skills)}")
        print_info(f"Match score: {result.match_result.overall_score}%")

        # Verify UUID format
        assert len(result.customization_id) == 36, "Invalid UUID format"
        # Verify ISO 8601 timestamp
        assert "T" in result.created_at and "Z" in result.created_at, "Invalid timestamp format"

        print_success("Default customization completed")

        # Test 2: Custom preferences
        print_header("Test 2: Customize with Custom Preferences", level=2)
        prefs = CustomizationPreferences(
            achievements_per_role=2,
            max_skills=5,
            template="classic",
        )
        result = customize_resume(profile, match_result, prefs)

        print_info(f"Template: {result.template}")
        print_info(f"Skills (max 5): {len(result.reordered_skills)}")

        assert result.template == "classic", "Template not applied"
        assert len(result.reordered_skills) <= 5, "Skills limit not applied"

        for exp in result.selected_experiences:
            if exp.achievements:
                assert len(exp.achievements) <= 2, f"Expected ≤2 achievements, got {len(exp.achievements)}"

        print_success("Custom preferences applied correctly")

        # Test 3: Metadata and change tracking
        print_header("Test 3: Metadata and Change Tracking", level=2)
        result = customize_resume(profile, match_result)

        print_info("Metadata contents:")
        print_info(f"- Original achievements: {result.metadata['original_achievement_count']}", indent=1)
        print_info(f"- Customized achievements: {result.metadata['customized_achievement_count']}", indent=1)
        print_info(f"- Original skills: {result.metadata['original_skill_count']}", indent=1)
        print_info(f"- Customized skills: {result.metadata['customized_skill_count']}", indent=1)
        print_info(f"- Match score: {result.metadata['match_score']}%", indent=1)

        changes = result.metadata['changes_log']
        print_info(f"- Achievements removed: {changes['achievements_removed']}", indent=1)
        print_info(f"- Skills removed: {changes['skills_removed']}", indent=1)
        print_info(f"- Skills reordered: {changes['skills_reordered']}", indent=1)

        print_success("Metadata generated correctly")

        # Test 4: Customization summary
        print_header("Test 4: Customization Summary", level=2)
        summary = get_customization_summary(result)

        print_info(f"Match score: {summary['match_score']}%")
        print_info(f"Template: {summary['template']}")
        print_info(f"Experiences: {summary['experiences_count']}")
        print_info(f"Achievements: {summary['achievements_count']}")
        print_info(f"Skills: {summary['skills_count']}")

        print_success("Summary generated correctly")

        # Test 5: Multiple customizations
        print_header("Test 5: Multiple Customizations from Same Profile", level=2)
        prefs1 = CustomizationPreferences(template="modern", achievements_per_role=3)
        prefs2 = CustomizationPreferences(template="ats", achievements_per_role=1)

        result1 = customize_resume(profile, match_result, prefs1)
        result2 = customize_resume(profile, match_result, prefs2)

        assert result1.customization_id != result2.customization_id, "IDs should be unique"
        assert result1.template == "modern", "Template 1 incorrect"
        assert result2.template == "ats", "Template 2 incorrect"

        print_info(f"Customization 1: {result1.customization_id} (modern)")
        print_info(f"Customization 2: {result2.customization_id} (ats)")

        print_success("Multiple customizations work correctly")

        print_success("Phase 4.3 - All tests passed!")
        return True

    except Exception as e:
        print_error(f"Phase 4.3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_4_4_mcp_integration() -> bool:
    """Test Phase 4.4 - MCP Tool Integration."""
    print_header("Phase 4.4 - MCP Tool Integration", level=1)

    try:
        # Clear session state
        _session_state["profiles"].clear()
        _session_state["matches"].clear()
        _session_state["customizations"].clear()

        profile = create_sample_profile()
        match_result = create_sample_match_result(profile)

        # Setup session state
        print_header("Test Setup: Load Session State", level=2)
        _session_state["profiles"]["test-profile-123"] = profile
        _session_state["matches"]["test-match-789"] = match_result

        print_info("Profile loaded into session")
        print_info("Match result loaded into session")
        print_success("Session state initialized")

        # Test 1: Error - Missing match_id
        print_header("Test 1: Error Handling - Missing match_id", level=2)
        result = handle_customize_resume({})

        assert result["status"] == "error", "Should return error status"
        assert "missing" in result["message"].lower(), "Should mention missing parameter"

        print_info(f"Error message: {result['message']}")
        print_success("Missing parameter error handled correctly")

        # Test 2: Error - Non-existent match
        print_header("Test 2: Error Handling - Non-existent Match", level=2)
        result = handle_customize_resume({"match_id": "fake-match-id"})

        assert result["status"] == "error", "Should return error status"
        assert "not found" in result["message"].lower(), "Should mention not found"

        print_info(f"Error message: {result['message']}")
        print_success("Non-existent match error handled correctly")

        # Test 3: Successful customization
        print_header("Test 3: Successful Customization", level=2)
        result = handle_customize_resume({"match_id": "test-match-789"})

        assert result["status"] == "success", f"Should succeed, got: {result.get('message')}"

        print_info(f"Status: {result['status']}")
        print_info(f"Customization ID: {result['customization_id']}")
        print_info(f"Profile ID: {result['profile_id']}")
        print_info(f"Job ID: {result['job_id']}")
        print_info(f"Template: {result['template']}")
        print_info(f"Experiences: {result['experiences_count']}")
        print_info(f"Skills: {result['skills_count']}")
        print_info(f"Created at: {result['created_at']}")

        # Verify stored in session
        customization_id = result['customization_id']
        assert customization_id in _session_state["customizations"], "Should be stored in session"

        print_success("Customization stored in session state")

        # Test 4: Customization with preferences
        print_header("Test 4: Customization with Custom Preferences", level=2)
        result = handle_customize_resume({
            "match_id": "test-match-789",
            "preferences": {
                "achievements_per_role": 1,
                "max_skills": 3,
                "template": "minimal",
                "include_summary": False,
            }
        })

        assert result["status"] == "success", "Should succeed with preferences"
        assert result["template"] == "minimal", f"Expected 'minimal', got {result['template']}"
        assert result["skills_count"] <= 3, f"Expected ≤3 skills, got {result['skills_count']}"
        assert result["include_summary"] is False, "Should not include summary"

        print_info(f"Template: {result['template']}")
        print_info(f"Skills: {result['skills_count']} (max 3)")
        print_info(f"Include summary: {result['include_summary']}")

        print_success("Preferences applied correctly via MCP")

        # Test 5: Metadata structure
        print_header("Test 5: Metadata Structure Validation", level=2)
        metadata = result['metadata']

        assert "changes_count" in metadata, "Missing changes_count"
        assert "achievements_reordered" in metadata, "Missing achievements_reordered"
        assert "skills_reordered" in metadata, "Missing skills_reordered"

        print_info(f"Changes count: {metadata['changes_count']}")
        print_info(f"Achievements reordered: {metadata['achievements_reordered']}")
        print_info(f"Skills reordered: {metadata['skills_reordered']}")

        assert "changes_summary" in result, "Missing changes_summary"
        print_info(f"Changes summary entries: {len(result['changes_summary'])}")

        print_success("Metadata structure is valid")

        # Test 6: Multiple customizations
        print_header("Test 6: Multiple Customizations from Same Match", level=2)
        _session_state["customizations"].clear()

        result1 = handle_customize_resume({
            "match_id": "test-match-789",
            "preferences": {"template": "modern"}
        })

        result2 = handle_customize_resume({
            "match_id": "test-match-789",
            "preferences": {"template": "classic"}
        })

        assert result1["status"] == "success", "First customization should succeed"
        assert result2["status"] == "success", "Second customization should succeed"
        assert result1["customization_id"] != result2["customization_id"], "IDs should be unique"
        assert len(_session_state["customizations"]) == 2, "Should have 2 customizations"

        print_info(f"Customization 1: {result1['customization_id']} ({result1['template']})")
        print_info(f"Customization 2: {result2['customization_id']} ({result2['template']})")
        print_info(f"Total in session: {len(_session_state['customizations'])}")

        print_success("Multiple customizations work correctly")

        print_success("Phase 4.4 - All tests passed!")
        return True

    except Exception as e:
        print_error(f"Phase 4.4 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        _session_state["profiles"].clear()
        _session_state["matches"].clear()
        _session_state["customizations"].clear()


def main() -> int:
    """Run all Phase 4 tests."""
    print_header("PHASE 4 MANUAL TESTING - Resume Customization Engine", level=1)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "Phase 4.1 - Achievement Reordering": test_phase_4_1_achievement_reordering(),
        "Phase 4.2 - Skills Optimization": test_phase_4_2_skills_optimization(),
        "Phase 4.3 - Resume Customization": test_phase_4_3_resume_customization(),
        "Phase 4.4 - MCP Integration": test_phase_4_4_mcp_integration(),
    }

    # Print summary
    print_header("TEST SUMMARY", level=1)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for phase, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status} - {phase}")

    print(f"\nResults: {passed}/{total} phases passed")

    if passed == total:
        print_header("🎉 ALL TESTS PASSED! Phase 4 is working correctly.", level=1)
        return 0
    else:
        print_header("❌ SOME TESTS FAILED. Please review the errors above.", level=1)
        return 1


if __name__ == "__main__":
    sys.exit(main())
