"""
End-to-end MCP integration tests (Phase 6.4).

Tests the complete MCP tool workflow from loading data
through customization and listing history.
"""

import pytest

from resume_customizer.mcp.handlers import (
    _session_state,
    handle_analyze_match,
    handle_customize_resume,
    handle_list_customizations,
    handle_load_job_description,
    handle_load_user_profile,
)


@pytest.fixture
def resume_file():
    """Path to test resume file."""
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "fixtures", "test_resume.md")


@pytest.fixture
def job_file():
    """Path to test job file."""
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "fixtures", "test_job.md")


@pytest.fixture(autouse=True)
def clear_state(tmp_path):
    """Clear session state and database before each test."""
    import resume_customizer.mcp.handlers as handlers
    from resume_customizer.storage.database import CustomizationDatabase

    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()

    db_path = tmp_path / "test_integration.db"
    handlers._database = CustomizationDatabase(db_path)

    yield

    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()

    if handlers._database:
        handlers._database.close()
    if db_path.exists():
        db_path.unlink()


class TestEndToEndWorkflow:
    """Test complete end-to-end MCP workflow."""

    def test_full_workflow_all_tools(self, resume_file, job_file):
        """Test complete workflow using all MCP tools."""
        # Step 1: Load user profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        assert profile_result["status"] == "success"
        profile_id = profile_result["profile_id"]

        # Step 2: Load job description
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
        assert match_result["overall_score"] > 0

        # Step 4: Customize resume
        customize_result = handle_customize_resume({
            "match_id": match_id,
        })
        assert customize_result["status"] == "success"
        customization_id = customize_result["customization_id"]

        # Step 5: List customizations
        list_result = handle_list_customizations({})
        assert list_result["status"] == "success"
        assert list_result["count"] == 1
        assert len(list_result["customizations"]) == 1

        # Verify customization is in database
        stored = list_result["customizations"][0]
        assert stored["customization_id"] == customization_id
        assert stored["profile_name"] == "John Doe"
        assert stored["company"] == "InnovateTech Solutions"

    def test_workflow_with_preferences(self, resume_file, job_file):
        """Test workflow with custom preferences."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })

        customize_result = handle_customize_resume({
            "match_id": match_result["match_id"],
            "preferences": {
                "achievements_per_role": 3,
                "max_skills": 10,
                "template": "modern",
            },
        })

        assert customize_result["status"] == "success"
        assert customize_result["template"] == "modern"

    def test_workflow_error_recovery(self, resume_file, job_file):
        """Test workflow handles errors gracefully."""
        # Load valid profile
        profile_result = handle_load_user_profile({"file_path": resume_file})
        assert profile_result["status"] == "success"

        # Try to analyze with invalid job_id
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": "invalid-job-id",
        })
        assert match_result["status"] == "error"
        assert "suggestion" in match_result

        # Now load valid job and continue
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })
        assert match_result["status"] == "success"


class TestMultipleCustomizations:
    """Test creating and listing multiple customizations."""

    def test_create_multiple_customizations(self, resume_file, job_file):
        """Test creating multiple customizations and listing them."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})

        # Create 3 customizations
        customization_ids = []
        for _ in range(3):
            match_result = handle_analyze_match({
                "profile_id": profile_result["profile_id"],
                "job_id": job_result["job_id"],
            })
            customize_result = handle_customize_resume({
                "match_id": match_result["match_id"],
            })
            customization_ids.append(customize_result["customization_id"])

        # List all customizations
        list_result = handle_list_customizations({})
        assert list_result["status"] == "success"
        assert list_result["count"] == 3

        # Verify all customizations are in database
        stored_ids = [c["customization_id"] for c in list_result["customizations"]]
        for cid in customization_ids:
            assert cid in stored_ids

    def test_filter_customizations_by_company(self, resume_file, job_file):
        """Test filtering customizations by company."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        job_result = handle_load_job_description({"file_path": job_file})
        match_result = handle_analyze_match({
            "profile_id": profile_result["profile_id"],
            "job_id": job_result["job_id"],
        })
        handle_customize_resume({"match_id": match_result["match_id"]})

        # Filter by partial company name
        list_result = handle_list_customizations({
            "filter_by_company": "Innovate",
        })
        assert list_result["status"] == "success"
        assert list_result["count"] == 1

        # Filter by non-existent company
        list_result = handle_list_customizations({
            "filter_by_company": "NonExistent",
        })
        assert list_result["count"] == 0


class TestSessionStateManagement:
    """Test session state is properly managed."""

    def test_session_state_persists_across_calls(self, resume_file, job_file):
        """Test session state persists between handler calls."""
        profile_result = handle_load_user_profile({"file_path": resume_file})
        profile_id = profile_result["profile_id"]

        # Verify profile is in session
        assert profile_id in _session_state["profiles"]

        # Load job in separate call
        job_result = handle_load_job_description({"file_path": job_file})
        job_id = job_result["job_id"]

        # Verify both are still in session
        assert profile_id in _session_state["profiles"]
        assert job_id in _session_state["jobs"]

        # Analyze match using session data
        match_result = handle_analyze_match({
            "profile_id": profile_id,
            "job_id": job_id,
        })
        assert match_result["status"] == "success"
        assert match_result["match_id"] in _session_state["matches"]


class TestErrorHandling:
    """Test comprehensive error handling across tools."""

    def test_all_tools_require_parameters(self):
        """Test all tools validate required parameters."""
        # load_user_profile requires file_path
        result = handle_load_user_profile({})
        assert result["status"] == "error"
        assert "suggestion" in result

        # load_job_description requires file_path
        result = handle_load_job_description({})
        assert result["status"] == "error"
        assert "suggestion" in result

        # analyze_match requires profile_id and job_id
        result = handle_analyze_match({})
        assert result["status"] == "error"
        assert "suggestion" in result

    def test_all_errors_include_suggestions(self, resume_file):
        """Test all error responses include helpful suggestions."""
        # Invalid file path
        result = handle_load_user_profile({"file_path": "/nonexistent.md"})
        assert result["status"] == "error"
        assert "suggestion" in result
        assert len(result["suggestion"]) > 10

        # Invalid profile_id
        job_result = handle_load_job_description({"file_path": resume_file})
        result = handle_analyze_match({
            "profile_id": "invalid",
            "job_id": job_result["job_id"],
        })
        assert result["status"] == "error"
        assert "suggestion" in result
