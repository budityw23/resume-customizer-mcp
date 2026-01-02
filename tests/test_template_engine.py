"""Tests for template engine."""

from pathlib import Path

import pytest

from resume_customizer.core.customizer import customize_resume
from resume_customizer.core.models import (
    CustomizedResume,
    MatchResult,
    UserProfile,
)
from resume_customizer.generators.template_engine import (
    TemplateEngine,
    TemplateNotFoundError,
    _format_date_range,
    _group_skills_by_category,
    _prepare_template_context,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def template_engine() -> TemplateEngine:
    """Create TemplateEngine with project templates."""
    # Use actual templates/ directory from project root
    return TemplateEngine()


@pytest.fixture
def sample_customized_resume(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
) -> CustomizedResume:
    """Create sample CustomizedResume for testing."""
    # Use the customize_resume function from Phase 4
    customized = customize_resume(complete_profile, complete_match_result)
    return customized


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_format_date_range_year_month():
    """Test date range formatting with YYYY-MM format."""
    result = _format_date_range("2020-01", "2023-06")
    assert result == "Jan 2020 - Jun 2023"


def test_format_date_range_present():
    """Test date range formatting with Present."""
    result = _format_date_range("2020-01", "Present")
    assert result == "Jan 2020 - Present"


def test_format_date_range_year_only():
    """Test date range formatting with year only."""
    result = _format_date_range("2020", "2023")
    assert result == "2020 - 2023"


def test_format_date_range_invalid():
    """Test date range formatting with invalid format."""
    result = _format_date_range("Summer 2020", "Fall 2023")
    assert result == "Summer 2020 - Fall 2023"


def test_group_skills_by_category(complete_profile: UserProfile):
    """Test grouping skills by category."""
    skills = complete_profile.skills
    grouped = _group_skills_by_category(skills)

    assert isinstance(grouped, dict)
    assert len(grouped) > 0

    # Check that skills are grouped correctly
    for category, category_skills in grouped.items():
        assert isinstance(category, str)
        assert isinstance(category_skills, list)
        assert len(category_skills) > 0

        # All skills in category should have the same category
        for skill_dict in category_skills:
            assert "name" in skill_dict


def test_prepare_template_context(
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test template context preparation."""
    context = _prepare_template_context(sample_customized_resume, complete_profile)

    # Check structure
    assert isinstance(context, dict)

    # Check personal information
    assert "name" in context
    assert context["name"] == complete_profile.name
    assert "contact" in context
    assert "email" in context["contact"]

    # Check customized sections
    assert "summary" in context
    assert "experiences" in context
    assert "skills" in context
    assert "skills_by_category" in context

    # Check unchanged sections
    assert "education" in context
    assert "certifications" in context
    assert "projects" in context

    # Check metadata
    assert "metadata" in context
    assert "match_score" in context["metadata"]
    assert "customization_id" in context["metadata"]


def test_prepare_template_context_uses_customized_summary(
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test that context uses customized summary when available."""
    # Set a custom summary
    sample_customized_resume.customized_summary = "Custom summary for this job"

    context = _prepare_template_context(sample_customized_resume, complete_profile)

    assert context["summary"] == "Custom summary for this job"


def test_prepare_template_context_falls_back_to_original_summary(
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test that context falls back to original summary when no custom summary."""
    # Ensure no customized summary
    sample_customized_resume.customized_summary = None

    context = _prepare_template_context(sample_customized_resume, complete_profile)

    assert context["summary"] == complete_profile.summary


# ============================================================================
# Template Engine Initialization Tests
# ============================================================================


def test_template_engine_initialization():
    """Test TemplateEngine initializes successfully."""
    engine = TemplateEngine()
    assert engine.templates_dir.exists()
    assert engine.env is not None


def test_template_engine_custom_directory(tmp_path: Path):
    """Test TemplateEngine with custom templates directory."""
    # Create a custom templates directory
    custom_dir = tmp_path / "custom_templates"
    custom_dir.mkdir()

    # Create a dummy template
    (custom_dir / "test.html").write_text("<html><body>{{ name }}</body></html>")

    engine = TemplateEngine(templates_dir=custom_dir)
    assert engine.templates_dir == custom_dir


def test_template_engine_invalid_directory():
    """Test TemplateEngine raises error for invalid directory."""
    with pytest.raises(FileNotFoundError):
        TemplateEngine(templates_dir=Path("/nonexistent/path"))


# ============================================================================
# Template Loading Tests
# ============================================================================


def test_list_templates(template_engine: TemplateEngine):
    """Test listing available templates."""
    templates = template_engine.list_templates()

    assert isinstance(templates, list)
    assert len(templates) >= 3  # modern, classic, ats_optimized
    assert "modern" in templates
    assert "classic" in templates
    assert "ats_optimized" in templates


def test_load_modern_template(template_engine: TemplateEngine):
    """Test loading modern template."""
    template = template_engine.load_template("modern")
    assert template is not None


def test_load_classic_template(template_engine: TemplateEngine):
    """Test loading classic template."""
    template = template_engine.load_template("classic")
    assert template is not None


def test_load_ats_template(template_engine: TemplateEngine):
    """Test loading ATS-optimized template."""
    template = template_engine.load_template("ats_optimized")
    assert template is not None


def test_load_nonexistent_template(template_engine: TemplateEngine):
    """Test loading nonexistent template raises error."""
    with pytest.raises(TemplateNotFoundError) as exc_info:
        template_engine.load_template("nonexistent")

    assert "nonexistent" in str(exc_info.value)
    assert "Available templates:" in str(exc_info.value)


# ============================================================================
# DOCX Generation Tests
# ============================================================================


def test_generate_docx_success(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test successful DOCX generation."""
    output_path = tmp_path / "test_resume.docx"

    result = template_engine.generate_docx(
        sample_customized_resume, complete_profile, output_path, "modern"
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.suffix == ".docx"
    assert output_path.stat().st_size > 0


def test_generate_docx_all_templates(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test DOCX generation with all three templates."""
    templates = ["modern", "classic", "ats_optimized"]

    for template_name in templates:
        output_path = tmp_path / f"test_resume_{template_name}.docx"
        result = template_engine.generate_docx(
            sample_customized_resume, complete_profile, output_path, template_name
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_generate_docx_creates_output_directory(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test DOCX generation creates output directory if it doesn't exist."""
    output_dir = tmp_path / "nested" / "output" / "dir"
    output_path = output_dir / "test_resume.docx"

    result = template_engine.generate_docx(
        sample_customized_resume, complete_profile, output_path, "modern"
    )

    assert result == output_path
    assert output_path.exists()
    assert output_dir.exists()


def test_generate_docx_reasonable_file_size(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test DOCX file size is reasonable (< 500KB)."""
    output_path = tmp_path / "test_resume.docx"

    template_engine.generate_docx(
        sample_customized_resume, complete_profile, output_path, "modern"
    )

    file_size_kb = output_path.stat().st_size / 1024
    assert file_size_kb < 500, f"DOCX file too large: {file_size_kb:.2f}KB"


def test_generate_docx_with_missing_optional_sections(
    template_engine: TemplateEngine,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test DOCX generation handles missing optional sections gracefully."""
    # Create profile without certifications and projects
    profile_minimal = UserProfile(
        name=complete_profile.name,
        contact=complete_profile.contact,
        summary=complete_profile.summary,
        experiences=complete_profile.experiences,
        skills=complete_profile.skills,
        education=complete_profile.education,
        certifications=None,  # Optional
        projects=None,  # Optional
    )

    # Create minimal customized resume
    from resume_customizer.core.customizer import customize_resume
    from resume_customizer.core.models import MatchBreakdown, MatchResult, SkillMatch

    match_result = MatchResult(
        profile_id="test-profile",
        job_id="test-job",
        overall_score=85,
        breakdown=MatchBreakdown(
            technical_skills_score=85.0,
            experience_score=80.0,
            domain_score=75.0,
            keyword_coverage_score=80.0,
            total_score=85.0,
        ),
        matched_skills=[
            SkillMatch(
                skill="Python",
                matched=True,
                category="required",
                user_proficiency="Expert",
            )
        ],
        missing_required_skills=[],
        missing_preferred_skills=[],
        suggestions=["Good match"],
    )

    customized = customize_resume(profile_minimal, match_result)
    output_path = tmp_path / "test_minimal.docx"

    result = template_engine.generate_docx(
        customized, profile_minimal, output_path, "modern"
    )

    assert result == output_path
    assert output_path.exists()


# ============================================================================
# HTML Rendering Tests
# ============================================================================


def test_render_html_modern(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test HTML rendering with modern template."""
    html = template_engine.render_html(
        sample_customized_resume, complete_profile, "modern"
    )

    assert isinstance(html, str)
    assert len(html) > 0
    assert "<!DOCTYPE html>" in html
    assert complete_profile.name in html


def test_render_html_contains_name(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendered HTML contains user name."""
    html = template_engine.render_html(
        sample_customized_resume, complete_profile, "modern"
    )

    assert complete_profile.name in html


def test_render_html_contains_contact_info(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendered HTML contains contact information."""
    html = template_engine.render_html(
        sample_customized_resume, complete_profile, "modern"
    )

    assert complete_profile.contact.email in html


def test_render_html_contains_experiences(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendered HTML contains work experiences."""
    html = template_engine.render_html(
        sample_customized_resume, complete_profile, "modern"
    )

    # Check that experiences are included
    for exp in sample_customized_resume.selected_experiences[:3]:  # Check first 3
        assert exp.company in html
        assert exp.title in html


def test_render_html_contains_skills(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendered HTML contains skills."""
    html = template_engine.render_html(
        sample_customized_resume, complete_profile, "modern"
    )

    # Check that skills are included
    for skill in sample_customized_resume.reordered_skills[:5]:  # Check first 5
        assert skill.name in html


def test_render_html_contains_education(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendered HTML contains education."""
    html = template_engine.render_html(
        sample_customized_resume, complete_profile, "modern"
    )

    # Check that education is included
    for edu in complete_profile.education:
        assert edu.degree in html
        assert edu.institution in html


def test_render_html_all_templates(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendering with all available templates."""
    templates = ["modern", "classic", "ats_optimized"]

    for template_name in templates:
        html = template_engine.render_html(
            sample_customized_resume, complete_profile, template_name
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert complete_profile.name in html


def test_render_html_nonexistent_template(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test rendering with nonexistent template raises error."""
    with pytest.raises(TemplateNotFoundError):
        template_engine.render_html(
            sample_customized_resume, complete_profile, "nonexistent"
        )


# ============================================================================
# PDF Generation Tests
# ============================================================================


def test_generate_pdf_creates_file(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test PDF generation creates a file."""
    output_path = tmp_path / "resume.pdf"

    result_path = template_engine.generate_pdf(
        sample_customized_resume, complete_profile, output_path, "modern"
    )

    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_pdf_file_size_reasonable(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test generated PDF file size is reasonable."""
    output_path = tmp_path / "resume.pdf"

    template_engine.generate_pdf(
        sample_customized_resume, complete_profile, output_path, "modern"
    )

    file_size = output_path.stat().st_size
    # PDF should be less than 500KB for a simple resume
    assert file_size < 500 * 1024


def test_generate_pdf_all_templates(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test PDF generation with all templates."""
    templates = ["modern", "classic", "ats_optimized"]

    for template_name in templates:
        output_path = tmp_path / f"resume_{template_name}.pdf"

        template_engine.generate_pdf(
            sample_customized_resume, complete_profile, output_path, template_name
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_generate_pdf_creates_output_directory(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test PDF generation creates output directory if needed."""
    output_path = tmp_path / "nested" / "dir" / "resume.pdf"

    template_engine.generate_pdf(
        sample_customized_resume, complete_profile, output_path, "modern"
    )

    assert output_path.exists()
    assert output_path.parent.exists()


def test_generate_pdf_nonexistent_template(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
    tmp_path: Path,
):
    """Test PDF generation with nonexistent template raises error."""
    output_path = tmp_path / "resume.pdf"

    with pytest.raises(TemplateNotFoundError):
        template_engine.generate_pdf(
            sample_customized_resume, complete_profile, output_path, "nonexistent"
        )


# ============================================================================
# Integration Tests
# ============================================================================


def test_end_to_end_pdf_generation(
    template_engine: TemplateEngine,
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
    tmp_path: Path,
):
    """Test complete end-to-end PDF generation workflow."""
    # Step 1: Customize resume
    customized_resume = customize_resume(complete_profile, complete_match_result)

    # Step 2: Generate PDF
    output_path = tmp_path / "final_resume.pdf"
    template_engine.generate_pdf(
        customized_resume, complete_profile, output_path, "modern"
    )

    # Verify PDF exists and has content
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_all_templates_render_without_errors(
    template_engine: TemplateEngine,
    sample_customized_resume: CustomizedResume,
    complete_profile: UserProfile,
):
    """Test that all templates render without errors."""
    templates = template_engine.list_templates()

    for template_name in templates:
        # Should not raise any exceptions
        html = template_engine.render_html(
            sample_customized_resume, complete_profile, template_name
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
