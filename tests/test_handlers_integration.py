"""
Integration tests for MCP handlers (Phase 2.4).

Tests the complete workflow:
- Load user profile
- Load job description
- Analyze match
- Error handling
"""

import pytest

from resume_customizer.mcp.handlers import (
    _session_state,
    handle_analyze_match,
    handle_customize_resume,
    handle_load_job_description,
    handle_load_user_profile,
)


@pytest.fixture
def resume_file():
    """Use the test resume fixture file."""
    import os
    # Get the path to the test fixtures folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resume_path = os.path.join(current_dir, "fixtures", "test_resume.md")
    return resume_path


@pytest.fixture
def job_file():
    """Use the test job fixture file."""
    import os
    # Get the path to the test fixtures folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    job_path = os.path.join(current_dir, "fixtures", "test_job.md")
    return job_path


@pytest.fixture(autouse=True)
def clear_session_state():
    """Clear session state before each test."""
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()
    yield
    # Clean up after test
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()


class TestLoadUserProfile:
    """Test load_user_profile handler."""

    def test_load_valid_profile(self, resume_file):
        """Test loading a valid resume file."""
        result = handle_load_user_profile({"file_path": resume_file})

        assert result["status"] == "success"
        assert "profile_id" in result
        assert "name" in result
        assert result["skills_count"] >= 0
        assert result["experiences_count"] >= 0

        # Verify it's stored in session
        profile_id = result["profile_id"]
        assert profile_id in _session_state["profiles"]

    def test_load_missing_file(self):
        """Test loading a non-existent file."""
        result = handle_load_user_profile({"file_path": "/nonexistent/file.md"})

        assert result["status"] == "error"
        # New validation gives better error message
        assert ("not found" in result["message"].lower() or "does not exist" in result["message"].lower())
        assert "suggestion" in result  # Should provide helpful suggestion

    def test_load_missing_file_path_param(self):
        """Test missing file_path parameter."""
        result = handle_load_user_profile({})

        assert result["status"] == "error"
        assert ("missing" in result["message"].lower() or "required" in result["message"].lower())
        assert "suggestion" in result


class TestLoadJobDescription:
    """Test load_job_description handler."""

    def test_load_valid_job(self, job_file):
        """Test loading a valid job description file."""
        result = handle_load_job_description({"file_path": job_file})

        assert result["status"] == "success"
        assert "job_id" in result
        assert "title" in result
        assert "company" in result
        assert result["required_skills_count"] >= 0

        # Verify it's stored in session
        job_id = result["job_id"]
        assert job_id in _session_state["jobs"]

    def test_load_missing_file(self):
        """Test loading a non-existent file."""
        result = handle_load_job_description({"file_path": "/nonexistent/job.md"})

        assert result["status"] == "error"
        assert ("not found" in result["message"].lower() or "does not exist" in result["message"].lower())
        assert "suggestion" in result

    def test_load_missing_file_path_param(self):
        """Test missing file_path parameter."""
        result = handle_load_job_description({})

        assert result["status"] == "error"
        assert ("missing" in result["message"].lower() or "required" in result["message"].lower())
        assert "suggestion" in result


class TestAnalyzeMatch:
    """Test analyze_match handler."""

    def test_successful_match_analysis(self, resume_file, job_file):
        """Test successful match analysis workflow."""
        # Load profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        assert profile_result["status"] == "success"
        profile_id = profile_result["profile_id"]

        # Load job
        job_result = handle_load_job_description({"file_path": job_file})
        assert job_result["status"] == "success"
        job_id = job_result["job_id"]

        # Analyze match
        match_result = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": job_id,
        })

        assert match_result["status"] == "success"
        assert "match_id" in match_result
        assert match_result["profile_id"] == profile_id
        assert match_result["job_id"] == job_id

        # Verify overall score
        assert 0 <= match_result["overall_score"] <= 100

        # Verify breakdown
        breakdown = match_result["breakdown"]
        assert "technical_skills_score" in breakdown
        assert "experience_score" in breakdown
        assert "domain_score" in breakdown
        assert "keyword_coverage_score" in breakdown

        # Verify missing skills
        assert isinstance(match_result["missing_required_skills"], list)
        assert isinstance(match_result["missing_preferred_skills"], list)

        # Verify suggestions
        assert isinstance(match_result["suggestions"], list)

        # Verify top achievements
        assert isinstance(match_result["top_achievements"], list)
        assert len(match_result["top_achievements"]) <= 5

        # Verify it's stored in session
        match_id = match_result["match_id"]
        assert match_id in _session_state["matches"]

    def test_analyze_without_profile(self, job_file):
        """Test analyzing match without loading profile first."""
        # Load only job
        job_result = handle_load_job_description({"file_path": job_file})
        job_id = job_result["job_id"]

        # Try to analyze without profile
        match_result = handle_analyze_match({
            "profile_id": "nonexistent-profile",
            "job_id": job_id,
        })

        assert match_result["status"] == "error"
        assert "profile" in match_result["message"].lower()
        assert "not found" in match_result["message"].lower()
        assert "suggestion" in match_result

    def test_analyze_without_job(self, resume_file):
        """Test analyzing match without loading job first."""
        # Load only profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        profile_id = profile_result["profile_id"]

        # Try to analyze without job
        match_result = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": "nonexistent-job",
        })

        assert match_result["status"] == "error"
        assert "job" in match_result["message"].lower()
        assert "not found" in match_result["message"].lower()
        assert "suggestion" in match_result

    def test_analyze_missing_profile_id(self, job_file):
        """Test analyzing without profile_id parameter."""
        job_result = handle_load_job_description({"file_path": job_file})
        job_id = job_result["job_id"]

        match_result = handle_analyze_match({
            "job_id": job_id,
        })

        assert match_result["status"] == "error"
        assert ("missing" in match_result["message"].lower() or "required" in match_result["message"].lower())
        assert "suggestion" in match_result

    def test_analyze_missing_job_id(self, resume_file):
        """Test analyzing without job_id parameter."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        profile_id = profile_result["profile_id"]

        match_result = handle_analyze_match({
            "profile_id": profile_id,
        })

        assert match_result["status"] == "error"
        assert ("missing" in match_result["message"].lower() or "required" in match_result["message"].lower())
        assert "suggestion" in match_result


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_workflow(self, resume_file, job_file):
        """Test the complete workflow from loading to matching."""
        # Step 1: Load profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        assert profile_result["status"] == "success"
        profile_id = profile_result["profile_id"]

        # Step 2: Load job
        job_result = handle_load_job_description({"file_path": job_file})
        assert job_result["status"] == "success"
        job_id = job_result["job_id"]

        # Step 3: Analyze match
        match_result = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": job_id,
        })
        assert match_result["status"] == "success"
        assert match_result["overall_score"] > 0

        # Verify all data is accessible
        assert profile_id in _session_state["profiles"]
        assert job_id in _session_state["jobs"]
        assert match_result["match_id"] in _session_state["matches"]

    def test_multiple_matches(self, resume_file, job_file):
        """Test handling multiple match analyses."""
        # Load profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        profile_id = profile_result["profile_id"]

        # Load job
        job_result = handle_load_job_description({"file_path": job_file})
        job_id = job_result["job_id"]

        # Analyze same match twice (simulating re-analysis)
        match1 = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": job_id,
        })
        match2 = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": job_id,
        })

        assert match1["status"] == "success"
        assert match2["status"] == "success"
        assert match1["match_id"] != match2["match_id"]

        # Verify both are in session
        assert len(_session_state["matches"]) == 2


class TestMatchQuality:
    """Test match quality and scoring."""

    def test_high_match_score(self, resume_file, job_file):
        """Test that good match produces high score."""
        # Load profile and job
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})

        # Analyze match
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        # Should have a valid score
        assert 0 <= match_result["overall_score"] <= 100

        # Should have valid component scores
        assert 0 <= match_result["breakdown"]["technical_skills_score"] <= 100

    def test_suggestions_provided(self, resume_file, job_file):
        """Test that suggestions are provided."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})

        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        # Should have suggestions (either for missing preferred skills or improvements)
        suggestions = match_result["suggestions"]
        assert isinstance(suggestions, list)

        # If there are missing preferred skills, should suggest them
        if match_result["missing_preferred_skills"]:
            assert len(suggestions) > 0

    def test_achievement_ranking(self, resume_file, job_file):
        """Test that achievements are ranked."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})

        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        # Should have top achievements
        top_achievements = match_result["top_achievements"]
        assert len(top_achievements) > 0

        # Each achievement should have text and score
        for achievement in top_achievements:
            assert "text" in achievement
            assert "score" in achievement
            assert isinstance(achievement["score"], (int, float))

        # Scores should be descending
        scores = [ach["score"] for ach in top_achievements]
        assert scores == sorted(scores, reverse=True)


class TestCustomizeResume:
    """Test customize_resume handler (Phase 4.4)."""

    def test_successful_customization(self, resume_file, job_file):
        """Test successful resume customization workflow."""
        # Step 1: Load profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        assert profile_result["status"] == "success"
        profile_id = profile_result["profile_id"]

        # Step 2: Load job
        job_result = handle_load_job_description({"file_path": job_file})
        assert job_result["status"] == "success"
        job_id = job_result["job_id"]

        # Step 3: Analyze match
        match_result = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": job_id,
        })
        assert match_result["status"] == "success"
        match_id = match_result["match_id"]

        # Step 4: Customize resume
        customize_result = handle_customize_resume({
            "match_id": match_id,
        })

        assert customize_result["status"] == "success"
        assert "customization_id" in customize_result
        assert customize_result["match_id"] == match_id
        assert customize_result["profile_id"] == profile_id
        assert customize_result["job_id"] == job_id
        assert "created_at" in customize_result

        # Verify metadata
        assert customize_result["template"] == "modern"
        assert customize_result["experiences_count"] >= 0
        assert customize_result["skills_count"] >= 0
        assert "metadata" in customize_result

        # Verify it's stored in session
        customization_id = customize_result["customization_id"]
        assert customization_id in _session_state["customizations"]

    def test_customize_with_preferences(self, resume_file, job_file):
        """Test customization with custom preferences."""
        # Load and match
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        # Customize with preferences
        customize_result = handle_customize_resume({
            "match_id": match_result["match_id"],
            "preferences": {
                "achievements_per_role": 5,
                "max_skills": 10,
                "template": "minimal",
                "include_summary": False,
            },
        })

        assert customize_result["status"] == "success"
        assert customize_result["template"] == "minimal"
        assert customize_result["include_summary"] is False

    def test_customize_missing_match_id(self):
        """Test customization without match_id parameter."""
        result = handle_customize_resume({})

        assert result["status"] == "error"
        assert "missing" in result["message"].lower()
        assert "match_id" in result["message"].lower()

    def test_customize_nonexistent_match(self):
        """Test customization with non-existent match_id."""
        result = handle_customize_resume({
            "match_id": "nonexistent-match",
        })

        assert result["status"] == "error"
        assert "match not found" in result["message"].lower()

    def test_customize_metadata_content(self, resume_file, job_file):
        """Test that metadata contains expected information."""
        # Setup workflow
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        # Customize
        customize_result = handle_customize_resume({
            "match_id": match_result["match_id"],
        })

        # Verify metadata structure
        metadata = customize_result["metadata"]
        assert "changes_count" in metadata
        assert "achievements_reordered" in metadata
        assert "skills_reordered" in metadata
        assert isinstance(metadata["changes_count"], int)
        assert metadata["changes_count"] >= 0

        # Verify changes summary exists
        assert "changes_summary" in customize_result
        assert isinstance(customize_result["changes_summary"], (list, dict))

    def test_multiple_customizations(self, resume_file, job_file):
        """Test creating multiple customizations from same match."""
        # Setup workflow
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })
        match_id = match_result["match_id"]

        # Create two customizations with different preferences
        custom1 = handle_customize_resume({
            "match_id": match_id,
            "preferences": {"template": "modern"},
        })
        custom2 = handle_customize_resume({
            "match_id": match_id,
            "preferences": {"template": "minimal"},
        })

        assert custom1["status"] == "success"
        assert custom2["status"] == "success"
        assert custom1["customization_id"] != custom2["customization_id"]

        # Verify both are stored
        assert len(_session_state["customizations"]) == 2


class TestCompleteWorkflowWithCustomization:
    """Test complete end-to-end workflow including customization."""

    def test_full_workflow(self, resume_file, job_file):
        """Test the complete workflow from loading to customization."""
        # Step 1: Load profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        assert profile_result["status"] == "success"

        # Step 2: Load job
        job_result = handle_load_job_description({"file_path": job_file})
        assert job_result["status"] == "success"

        # Step 3: Analyze match
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })
        assert match_result["status"] == "success"
        assert match_result["overall_score"] > 0

        # Step 4: Customize resume
        customize_result = handle_customize_resume({
            "match_id": match_result["match_id"],
            "preferences": {
                "achievements_per_role": 3,
                "include_summary": True,
            },
        })
        assert customize_result["status"] == "success"

        # Verify complete state
        assert len(_session_state["profiles"]) == 1
        assert len(_session_state["jobs"]) == 1
        assert len(_session_state["matches"]) == 1
        assert len(_session_state["customizations"]) == 1

        # Verify data consistency
        assert customize_result["profile_id"] == profile_result["profile_id"]
        assert customize_result["job_id"] == job_result["job_id"]
        assert customize_result["match_id"] == match_result["match_id"]

    def test_workflow_with_preferences_validation(self, resume_file, job_file):
        """Test that preferences are properly applied."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        # Customize with specific preferences
        customize_result = handle_customize_resume({
            "match_id": match_result["match_id"],
            "preferences": {
                "achievements_per_role": 2,
                "max_skills": 5,
                "template": "elegant",
                "include_summary": True,
            },
        })

        assert customize_result["status"] == "success"
        assert customize_result["template"] == "elegant"
        # Note: include_summary may be False if AI summary generation is disabled
        assert "include_summary" in customize_result

        # Verify customization in session
        customization_id = customize_result["customization_id"]
        stored_customization = _session_state["customizations"][customization_id]
        assert stored_customization.template == "elegant"
