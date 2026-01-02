"""Integration tests for generate_resume_files handler."""

from pathlib import Path

import pytest

from resume_customizer.mcp.handlers import (
    _session_state,
    handle_analyze_match,
    handle_customize_resume,
    handle_generate_resume_files,
    handle_load_job_description,
    handle_load_user_profile,
)


@pytest.fixture(autouse=True)
def clear_session():
    """Clear session state before each test."""
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()
    yield


def test_generate_pdf_success(tmp_path: Path):
    """Test successful PDF generation."""
    # Setup: Load profile, job, analyze match, customize resume
    profile_result = handle_load_user_profile({
        "file_path": "examples/resumes/budi_resume.md"
    })
    assert profile_result["status"] == "success"

    job_result = handle_load_job_description({
        "file_path": "examples/jobs/fullstack_engineer_job.md"
    })
    assert job_result["status"] == "success"

    match_result = handle_analyze_match({
        "profile_id": profile_result["profile_id"],
        "job_id": job_result["job_id"],
    })
    assert match_result["status"] == "success"

    custom_result = handle_customize_resume({
        "match_id": match_result["match_id"],
    })
    assert custom_result["status"] == "success"

    # Test: Generate PDF
    output_dir = tmp_path / "output"
    result = handle_generate_resume_files({
        "customization_id": custom_result["customization_id"],
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
    })

    # Verify
    assert result["status"] == "success"
    assert result["customization_id"] == custom_result["customization_id"]
    assert "generated_files" in result
    assert "pdf" in result["generated_files"]
    assert result["generated_files"]["pdf"] is not None

    # Verify PDF file exists
    pdf_path = Path(result["generated_files"]["pdf"])
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 0


def test_generate_with_custom_template(tmp_path: Path):
    """Test PDF generation with custom template override."""
    # Setup
    profile_result = handle_load_user_profile({
        "file_path": "examples/resumes/budi_resume.md"
    })
    job_result = handle_load_job_description({
        "file_path": "examples/jobs/fullstack_engineer_job.md"
    })
    match_result = handle_analyze_match({
        "profile_id": profile_result["profile_id"],
        "job_id": job_result["job_id"],
    })
    custom_result = handle_customize_resume({
        "match_id": match_result["match_id"],
        "preferences": {"template": "modern"},
    })

    # Test: Generate with different template
    output_dir = tmp_path / "output"
    result = handle_generate_resume_files({
        "customization_id": custom_result["customization_id"],
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
        "template": "classic",  # Override to classic
    })

    # Verify
    assert result["status"] == "success"
    assert result["template"] == "classic"
    pdf_path = Path(result["generated_files"]["pdf"])
    assert pdf_path.exists()


def test_generate_with_custom_filename(tmp_path: Path):
    """Test PDF generation with custom filename prefix."""
    # Setup
    profile_result = handle_load_user_profile({
        "file_path": "examples/resumes/budi_resume.md"
    })
    job_result = handle_load_job_description({
        "file_path": "examples/jobs/fullstack_engineer_job.md"
    })
    match_result = handle_analyze_match({
        "profile_id": profile_result["profile_id"],
        "job_id": job_result["job_id"],
    })
    custom_result = handle_customize_resume({
        "match_id": match_result["match_id"],
    })

    # Test: Generate with custom filename
    output_dir = tmp_path / "output"
    result = handle_generate_resume_files({
        "customization_id": custom_result["customization_id"],
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
        "filename_prefix": "my_resume",
    })

    # Verify filename starts with prefix
    pdf_path = Path(result["generated_files"]["pdf"])
    assert pdf_path.name.startswith("my_resume_")


def test_generate_missing_customization_id():
    """Test error when customization_id is missing."""
    result = handle_generate_resume_files({})

    assert result["status"] == "error"
    assert "Missing required field" in result["message"]


def test_generate_invalid_customization_id():
    """Test error when customization_id doesn't exist."""
    result = handle_generate_resume_files({
        "customization_id": "nonexistent-id",
    })

    assert result["status"] == "error"
    assert "not found" in result["message"]


def test_generate_creates_output_directory(tmp_path: Path):
    """Test that output directory is created if it doesn't exist."""
    # Setup
    profile_result = handle_load_user_profile({
        "file_path": "examples/resumes/budi_resume.md"
    })
    job_result = handle_load_job_description({
        "file_path": "examples/jobs/fullstack_engineer_job.md"
    })
    match_result = handle_analyze_match({
        "profile_id": profile_result["profile_id"],
        "job_id": job_result["job_id"],
    })
    custom_result = handle_customize_resume({
        "match_id": match_result["match_id"],
    })

    # Test: Generate with nested directory that doesn't exist
    output_dir = tmp_path / "nested" / "output" / "dir"
    result = handle_generate_resume_files({
        "customization_id": custom_result["customization_id"],
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
    })

    # Verify directory was created
    assert result["status"] == "success"
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_generate_all_templates(tmp_path: Path):
    """Test PDF generation with all three templates."""
    # Setup
    profile_result = handle_load_user_profile({
        "file_path": "examples/resumes/budi_resume.md"
    })
    job_result = handle_load_job_description({
        "file_path": "examples/jobs/fullstack_engineer_job.md"
    })
    match_result = handle_analyze_match({
        "profile_id": profile_result["profile_id"],
        "job_id": job_result["job_id"],
    })
    custom_result = handle_customize_resume({
        "match_id": match_result["match_id"],
    })

    # Test each template
    templates = ["modern", "classic", "ats_optimized"]
    for template in templates:
        output_dir = tmp_path / template
        result = handle_generate_resume_files({
            "customization_id": custom_result["customization_id"],
            "output_formats": ["pdf"],
            "output_directory": str(output_dir),
            "template": template,
        })

        assert result["status"] == "success"
        assert result["template"] == template
        pdf_path = Path(result["generated_files"]["pdf"])
        assert pdf_path.exists()


def test_generate_docx_success(tmp_path: Path):
    """Test successful DOCX generation."""
    # Setup
    profile_result = handle_load_user_profile({
        "file_path": "examples/resumes/budi_resume.md"
    })
    job_result = handle_load_job_description({
        "file_path": "examples/jobs/fullstack_engineer_job.md"
    })
    match_result = handle_analyze_match({
        "profile_id": profile_result["profile_id"],
        "job_id": job_result["job_id"],
    })
    custom_result = handle_customize_resume({
        "match_id": match_result["match_id"],
    })

    # Test: Request DOCX generation
    output_dir = tmp_path / "output"
    result = handle_generate_resume_files({
        "customization_id": custom_result["customization_id"],
        "output_formats": ["docx"],
        "output_directory": str(output_dir),
    })

    # Verify DOCX generated successfully
    assert result["status"] == "success"
    assert "docx" in result["generated_files"]
    assert result["generated_files"]["docx"] is not None

    # Verify DOCX file exists
    docx_path = Path(result["generated_files"]["docx"])
    assert docx_path.exists()
    assert docx_path.suffix == ".docx"
    assert docx_path.stat().st_size > 0
