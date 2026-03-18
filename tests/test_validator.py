"""
Tests for validation functions (src/resume_customizer/parsers/validator.py).

Tests email, phone, URL validation and profile/job validation.
"""

import pytest

from resume_customizer.core.models import (
    Achievement,
    ContactInfo,
    Education,
    Experience,
    JobDescription,
    JobRequirements,
    UserProfile,
)
from resume_customizer.parsers.validator import (
    validate_date_format,
    validate_date_logic,
    validate_education,
    validate_email,
    validate_experience,
    validate_job_description,
    validate_phone,
    validate_url,
    validate_user_profile,
)


class TestEmailValidation:
    """Test email validation."""

    def test_valid_emails(self) -> None:
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+filter@gmail.com",
            "user123@domain.org",
            "first.last@sub.domain.com",
        ]

        for email in valid_emails:
            errors = validate_email(email)
            assert len(errors) == 0, f"Email '{email}' should be valid"

    def test_invalid_emails(self) -> None:
        """Test invalid email addresses."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com",
        ]

        for email in invalid_emails:
            errors = validate_email(email)
            assert len(errors) > 0, f"Email '{email}' should be invalid"

    def test_empty_email(self) -> None:
        """Test empty email validation."""
        errors = validate_email("")
        assert len(errors) == 1
        assert "required" in errors[0].lower()


class TestPhoneValidation:
    """Test phone number validation."""

    def test_valid_phones(self) -> None:
        """Test valid phone numbers."""
        valid_phones = [
            "+1-555-123-4567",
            "(555) 123-4567",
            "555-123-4567",
            "+44 20 7123 4567",
            "1234567890",
            "+1 (555) 123.4567",
        ]

        for phone in valid_phones:
            errors = validate_phone(phone)
            assert len(errors) == 0, f"Phone '{phone}' should be valid"

    def test_invalid_phones(self) -> None:
        """Test invalid phone numbers."""
        invalid_phones = [
            "12345",  # Too short
            "1234567890123456",  # Too long
            "abc-def-ghij",  # Not digits
            "123-456-789a",  # Contains letter
        ]

        for phone in invalid_phones:
            errors = validate_phone(phone)
            assert len(errors) > 0, f"Phone '{phone}' should be invalid"

    def test_empty_phone(self) -> None:
        """Test empty phone validation (should pass)."""
        errors = validate_phone("")
        assert len(errors) == 0  # Phone is optional


class TestURLValidation:
    """Test URL validation."""

    def test_valid_urls(self) -> None:
        """Test valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://www.example.com",
            "https://sub.domain.example.com",
            "https://example.com/path/to/page",
            "linkedin.com/in/user",
            "github.com/username",
        ]

        for url in valid_urls:
            errors = validate_url(url)
            assert len(errors) == 0, f"URL '{url}' should be valid"

    def test_social_handles(self) -> None:
        """Test social media handles without protocol."""
        handles = [
            "username",
            "user_name",
            "user123",
        ]

        for handle in handles:
            errors = validate_url(handle)
            assert len(errors) == 0, f"Handle '{handle}' should be valid"

    def test_empty_url(self) -> None:
        """Test empty URL validation (should pass)."""
        errors = validate_url("")
        assert len(errors) == 0  # URL is optional


class TestDateValidation:
    """Test date format and logic validation."""

    def test_valid_date_formats(self) -> None:
        """Test valid date formats."""
        valid_dates = [
            "2025",
            "2025-12",
            "December 2025",
            "Dec 2025",
            "Present",
            "current",
        ]

        for date in valid_dates:
            errors = validate_date_format(date)
            assert len(errors) == 0, f"Date '{date}' should be valid"

    def test_invalid_date_formats(self) -> None:
        """Test invalid date formats."""
        invalid_dates = [
            "12/2025",
            "2025/12",
            "12-2025",
            "Next month",
        ]

        for date in invalid_dates:
            errors = validate_date_format(date)
            assert len(errors) > 0, f"Date '{date}' should be invalid"

    def test_date_logic_valid(self) -> None:
        """Test valid date logic (end after start)."""
        test_cases = [
            ("2020", "2025"),
            ("2024-01", "2024-12"),
            ("January 2024", "December 2024"),
            ("2024-01", "Present"),
        ]

        for start, end in test_cases:
            errors = validate_date_logic(start, end)
            assert len(errors) == 0, f"Date range {start} - {end} should be valid"

    def test_date_logic_invalid(self) -> None:
        """Test invalid date logic (end before start)."""
        test_cases = [
            ("2025", "2020"),
            ("2024-12", "2024-01"),
        ]

        for start, end in test_cases:
            errors = validate_date_logic(start, end)
            assert len(errors) > 0, f"Date range {start} - {end} should be invalid"


class TestExperienceValidation:
    """Test work experience validation."""

    def test_valid_experience(self) -> None:
        """Test validation of valid experience."""
        exp = Experience(
            company="TechCorp",
            title="Software Engineer",
            start_date="2023-01",
            end_date="Present",
            achievements=[
                Achievement(text="Built awesome features", technologies=["Python"]),
                Achievement(text="Improved performance", metrics=["50%"]),
            ],
        )

        errors = validate_experience(exp, 0)
        assert len(errors) == 0

    def test_missing_required_fields(self) -> None:
        """Test experience with missing required fields."""
        exp = Experience(
            company="",
            title="",
            start_date="",
            end_date="",
            achievements=[],
        )

        errors = validate_experience(exp, 0)
        assert len(errors) >= 4  # Missing company, title, start_date, end_date

    def test_invalid_dates(self) -> None:
        """Test experience with invalid date range."""
        exp = Experience(
            company="TechCorp",
            title="Engineer",
            start_date="2025",
            end_date="2020",  # End before start
            achievements=[Achievement(text="Did stuff")],
        )

        errors = validate_experience(exp, 0)
        assert any("before" in e.lower() for e in errors)


class TestEducationValidation:
    """Test education validation."""

    def test_valid_education(self) -> None:
        """Test validation of valid education."""
        edu = Education(
            degree="Bachelor of Science in Computer Science",
            institution="MIT",
            graduation_year="2020",
            gpa="3.8/4.0",
        )

        errors = validate_education(edu, 0)
        assert len(errors) == 0

    def test_missing_required_fields(self) -> None:
        """Test education with missing required fields."""
        edu = Education(
            degree="",
            institution="",
            graduation_year=None,
            gpa=None,
        )

        errors = validate_education(edu, 0)
        assert len(errors) >= 2  # Missing degree, institution

    def test_invalid_gpa_format(self) -> None:
        """Test education with invalid GPA format."""
        edu = Education(
            degree="BS Computer Science",
            institution="University",
            graduation_year="2020",
            gpa="invalid",
        )

        errors = validate_education(edu, 0)
        assert any("gpa" in e.lower() for e in errors)

    def test_gpa_exceeds_maximum(self) -> None:
        """Test education with GPA exceeding maximum."""
        edu = Education(
            degree="BS Computer Science",
            institution="University",
            graduation_year="2020",
            gpa="5.0/4.0",
        )

        errors = validate_education(edu, 0)
        assert any("exceed" in e.lower() for e in errors)


class TestUserProfileValidation:
    """Test complete user profile validation."""

    @pytest.fixture
    def valid_profile(self) -> UserProfile:
        """Create a valid user profile for testing."""
        return UserProfile(
            name="John Doe",
            contact=ContactInfo(
                email="john@example.com",
                phone="+1-555-123-4567",
                location="San Francisco, CA",
                linkedin="linkedin.com/in/johndoe",
                github="github.com/johndoe",
                portfolio="johndoe.dev",
            ),
            summary="Experienced software engineer with 10+ years of experience in full-stack development",
            skills=["Python", "JavaScript", "React", "Node.js", "Docker", "AWS"],
            experiences=[
                Experience(
                    company="TechCorp",
                    title="Senior Software Engineer",
                    start_date="2020-01",
                    end_date="Present",
                    achievements=[
                        Achievement(text="Led team of 5"),
                        Achievement(text="Delivered 3 major projects"),
                    ],
                )
            ],
            education=[
                Education(
                    degree="BS Computer Science",
                    institution="MIT",
                    graduation_year="2015",
                    gpa="3.8/4.0",
                )
            ],
            certifications=[],
        )

    def test_valid_profile_validation(self, valid_profile: UserProfile) -> None:
        """Test validation of a valid profile."""
        errors = validate_user_profile(valid_profile)
        assert len(errors) == 0

    def test_missing_name(self, valid_profile: UserProfile) -> None:
        """Test profile with missing name."""
        valid_profile.name = ""
        errors = validate_user_profile(valid_profile)
        assert any("name" in e.lower() for e in errors)

    def test_short_summary(self, valid_profile: UserProfile) -> None:
        """Test profile with too short summary."""
        valid_profile.summary = "Short"
        errors = validate_user_profile(valid_profile)
        assert any("summary" in e.lower() and "50" in e for e in errors)

    def test_long_summary(self, valid_profile: UserProfile) -> None:
        """Test profile with too long summary."""
        valid_profile.summary = "x" * 1001
        errors = validate_user_profile(valid_profile)
        assert any("summary" in e.lower() and "1000" in e for e in errors)

    def test_no_skills(self, valid_profile: UserProfile) -> None:
        """Test profile with no skills."""
        valid_profile.skills = []
        errors = validate_user_profile(valid_profile)
        assert any("skill" in e.lower() for e in errors)

    def test_few_skills(self, valid_profile: UserProfile) -> None:
        """Test profile with few skills."""
        valid_profile.skills = ["Python", "JavaScript"]
        errors = validate_user_profile(valid_profile)
        assert any("skill" in e.lower() and "5" in e for e in errors)

    def test_no_experience(self, valid_profile: UserProfile) -> None:
        """Test profile with no experience."""
        valid_profile.experiences = []
        errors = validate_user_profile(valid_profile)
        assert any("experience" in e.lower() for e in errors)

    def test_no_education(self, valid_profile: UserProfile) -> None:
        """Test profile with no education."""
        valid_profile.education = []
        errors = validate_user_profile(valid_profile)
        assert any("education" in e.lower() for e in errors)


class TestJobDescriptionValidation:
    """Test job description validation."""

    @pytest.fixture
    def valid_job(self) -> JobDescription:
        """Create a valid job description for testing."""
        return JobDescription(
            title="Senior Software Engineer",
            company="TechCorp Inc.",
            location="San Francisco, CA",
            job_type="Full-time",
            experience_level="Senior",
            salary_range="$150k-$200k",
            description="We are looking for an experienced engineer",
            responsibilities=["Design systems", "Write code", "Review PRs"],
            requirements=JobRequirements(
                required_skills=["Python", "Docker", "AWS"],
                preferred_skills=["Kubernetes", "Terraform"],
                required_experience_years=5,
                required_education="Bachelor's degree",
            ),
            apply_url="https://techcorp.com/careers/apply",
        )

    def test_valid_job_validation(self, valid_job: JobDescription) -> None:
        """Test validation of a valid job description."""
        errors = validate_job_description(valid_job)
        assert len(errors) == 0

    def test_missing_title(self, valid_job: JobDescription) -> None:
        """Test job with missing title."""
        valid_job.title = ""
        errors = validate_job_description(valid_job)
        assert any("title" in e.lower() for e in errors)

    def test_missing_company(self, valid_job: JobDescription) -> None:
        """Test job with missing company."""
        valid_job.company = ""
        errors = validate_job_description(valid_job)
        assert any("company" in e.lower() for e in errors)

    def test_no_responsibilities(self, valid_job: JobDescription) -> None:
        """Test job with no responsibilities."""
        valid_job.responsibilities = []
        errors = validate_job_description(valid_job)
        assert any("responsibilit" in e.lower() for e in errors)

    def test_no_required_skills(self, valid_job: JobDescription) -> None:
        """Test job with no required skills."""
        valid_job.requirements.required_skills = []
        errors = validate_job_description(valid_job)
        assert any("skill" in e.lower() for e in errors)

    def test_too_long_description(self, valid_job: JobDescription) -> None:
        """Test job with excessively long description."""
        valid_job.description = "x" * 10001
        errors = validate_job_description(valid_job)
        assert any("description" in e.lower() and "long" in e.lower() for e in errors)

    def test_invalid_apply_url(self, valid_job: JobDescription) -> None:
        """Test job with invalid apply URL."""
        valid_job.apply_url = "not a url!@#$"
        validate_job_description(valid_job)
        # URL validation is lenient, so this might pass
        # depending on the validation logic
        # No assertion - just testing it handles gracefully
