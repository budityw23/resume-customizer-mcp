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
    handle_load_job_description,
    handle_load_user_profile,
)


@pytest.fixture
def resume_file():
    """Use the actual resume template file."""
    import os
    # Get the path to the docs folder
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resume_path = os.path.join(current_dir, "docs", "resume_template.md")
    return resume_path


@pytest.fixture
def job_file():
    """Use the actual job template file."""
    import os
    # Get the path to the docs folder
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    job_path = os.path.join(current_dir, "docs", "job_template.md")
    return job_path


@pytest.fixture(autouse=True)
def clear_session_state():
    """Clear session state before each test."""
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    yield
    # Clean up after test
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()


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
        assert "not found" in result["message"].lower()

    def test_load_missing_file_path_param(self):
        """Test missing file_path parameter."""
        result = handle_load_user_profile({})

        assert result["status"] == "error"
        assert "missing" in result["message"].lower()


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
        assert "not found" in result["message"].lower()

    def test_load_missing_file_path_param(self):
        """Test missing file_path parameter."""
        result = handle_load_job_description({})

        assert result["status"] == "error"
        assert "missing" in result["message"].lower()


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
        assert "profile not found" in match_result["message"].lower()

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

    def test_analyze_missing_profile_id(self, job_file):
        """Test analyzing without profile_id parameter."""
        job_result = handle_load_job_description({"file_path": job_file})
        job_id = job_result["job_id"]

        match_result = handle_analyze_match({
            "job_id": job_id,
        })

        assert match_result["status"] == "error"
        assert "missing" in match_result["message"].lower()

    def test_analyze_missing_job_id(self, resume_file):
        """Test analyzing without job_id parameter."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        profile_id = profile_result["profile_id"]

        match_result = handle_analyze_match({
            "profile_id": profile_id,
        })

        assert match_result["status"] == "error"
        assert "missing" in match_result["message"].lower()


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
