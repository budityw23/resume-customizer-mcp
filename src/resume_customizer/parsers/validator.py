"""
Validation functions for resume and job description data.

This module provides functions to validate parsed data and ensure it meets
quality standards and required fields.
"""

import re

from resume_customizer.core.models import JobDescription, UserProfile
from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_user_profile(profile: UserProfile) -> list[str]:
    """
    Validate a user profile and return list of validation errors.

    Args:
        profile: UserProfile to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    # Required fields
    if not profile.name or len(profile.name) < 2:
        errors.append("Name is required and must be at least 2 characters")

    # Contact validation
    email_errors = validate_email(profile.contact.email)
    errors.extend(email_errors)

    if profile.contact.phone:
        phone_errors = validate_phone(profile.contact.phone)
        errors.extend(phone_errors)

    # URL validation
    if profile.contact.linkedin:
        url_errors = validate_url(profile.contact.linkedin, "LinkedIn")
        errors.extend(url_errors)

    if profile.contact.github:
        url_errors = validate_url(profile.contact.github, "GitHub")
        errors.extend(url_errors)

    if profile.contact.portfolio:
        url_errors = validate_url(profile.contact.portfolio, "Portfolio")
        errors.extend(url_errors)

    # Summary validation
    if not profile.summary or len(profile.summary) < 50:
        errors.append("Professional summary is required and should be at least 50 characters")

    if len(profile.summary) > 1000:
        errors.append("Professional summary should not exceed 1000 characters")

    # Experience validation
    if not profile.experiences:
        errors.append("At least one work experience is required")
    else:
        for i, exp in enumerate(profile.experiences):
            exp_errors = validate_experience(exp, i)
            errors.extend(exp_errors)

    # Skills validation
    if not profile.skills:
        errors.append("At least one skill is required")
    elif len(profile.skills) < 5:
        errors.append("Add at least 5 skills for a complete profile")

    # Education validation
    if not profile.education:
        errors.append("At least one education entry is required")
    else:
        for i, edu in enumerate(profile.education):
            edu_errors = validate_education(edu, i)
            errors.extend(edu_errors)

    if errors:
        logger.warning(f"Profile validation found {len(errors)} error(s)")

    return errors


def validate_job_description(job: JobDescription) -> list[str]:
    """
    Validate a job description and return list of validation errors.

    Args:
        job: JobDescription to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: list[str] = []

    # Required fields
    if not job.title or len(job.title) < 3:
        errors.append("Job title is required and must be at least 3 characters")

    if not job.company or len(job.company) < 2:
        errors.append("Company name is required and must be at least 2 characters")

    # Description validation
    if job.description and len(job.description) > 10000:
        errors.append("Job description is too long (max 10000 characters)")

    # Responsibilities validation
    if not job.responsibilities:
        errors.append("At least one responsibility should be listed")

    # Requirements validation
    if not job.requirements.required_skills:
        errors.append("At least one required skill should be specified")

    # URL validation
    if job.apply_url:
        url_errors = validate_url(job.apply_url, "Apply URL")
        errors.extend(url_errors)

    if errors:
        logger.warning(f"Job description validation found {len(errors)} error(s)")

    return errors


def validate_email(email: str) -> list[str]:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        List of validation error messages
    """
    errors: list[str] = []

    if not email:
        errors.append("Email address is required")
        return errors

    # Basic email regex
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        errors.append(f"Invalid email format: {email}")

    return errors


def validate_phone(phone: str) -> list[str]:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        List of validation error messages
    """
    errors: list[str] = []

    if not phone:
        return errors

    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\(\)\+\.]", "", phone)

    # Check if it contains only digits after cleaning
    if not cleaned.isdigit():
        errors.append(f"Phone number should contain only digits and formatting characters: {phone}")
    elif len(cleaned) < 10 or len(cleaned) > 15:
        errors.append(f"Phone number should be between 10 and 15 digits: {phone}")

    return errors


def validate_url(url: str, field_name: str = "URL") -> list[str]:
    """
    Validate URL format.

    Args:
        url: URL to validate
        field_name: Name of the field for error messages

    Returns:
        List of validation error messages
    """
    errors: list[str] = []

    if not url:
        return errors

    # Basic URL validation - check for common patterns
    url_pattern = r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$"

    # Also allow URLs without protocol for social media
    if not re.match(url_pattern, url, re.IGNORECASE):
        # Check if it's a social media handle without protocol
        if not ("/" in url or "." in url):
            # Likely a username/handle, which is acceptable
            pass
        else:
            errors.append(f"Invalid {field_name} format: {url}")

    return errors


def validate_date_format(date_str: str) -> list[str]:
    """
    Validate date format.

    Args:
        date_str: Date string to validate

    Returns:
        List of validation error messages
    """
    errors: list[str] = []

    if not date_str:
        return errors

    # Allow "Present" for current jobs
    if date_str.lower() in ["present", "current", "now"]:
        return errors

    # Common formats: "2025-12", "December 2025", "2025"
    valid_formats = [
        r"^\d{4}$",  # 2025
        r"^\d{4}-\d{2}$",  # 2025-12
        r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$",
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}$",
    ]

    is_valid = any(re.match(pattern, date_str) for pattern in valid_formats)

    if not is_valid:
        errors.append(
            f"Invalid date format: {date_str}. Use formats like '2025-12', 'December 2025', or 'Present'"
        )

    return errors


def validate_date_logic(start_date: str, end_date: str) -> list[str]:
    """
    Validate that end date is after start date.

    Args:
        start_date: Start date string
        end_date: End date string

    Returns:
        List of validation error messages
    """
    errors: list[str] = []

    if not start_date or not end_date:
        return errors

    # Skip validation if end date is "Present"
    if end_date.lower() in ["present", "current", "now"]:
        return errors

    try:
        # Try to parse years
        start_year_match = re.search(r"\d{4}", start_date)
        end_year_match = re.search(r"\d{4}", end_date)

        if start_year_match and end_year_match:
            start_year = int(start_year_match.group())
            end_year = int(end_year_match.group())

            if end_year < start_year:
                errors.append(f"End date ({end_date}) cannot be before start date ({start_date})")

            # Also try to parse months if available
            start_month = _extract_month(start_date)
            end_month = _extract_month(end_date)

            if start_year == end_year and start_month and end_month:
                if end_month < start_month:
                    errors.append(
                        f"End date ({end_date}) cannot be before start date ({start_date})"
                    )

    except (ValueError, AttributeError):
        pass  # If parsing fails, skip this validation

    return errors


def validate_experience(exp: "Experience", index: int) -> list[str]:  # type: ignore # noqa: F821
    """Validate a work experience entry."""
    errors: list[str] = []
    prefix = f"Experience {index + 1}"

    if not exp.company:
        errors.append(f"{prefix}: Company name is required")

    if not exp.title:
        errors.append(f"{prefix}: Job title is required")

    if not exp.start_date:
        errors.append(f"{prefix}: Start date is required")

    if not exp.end_date:
        errors.append(f"{prefix}: End date is required")

    # Validate date formats
    if exp.start_date:
        errors.extend([f"{prefix}: {e}" for e in validate_date_format(exp.start_date)])

    if exp.end_date:
        errors.extend([f"{prefix}: {e}" for e in validate_date_format(exp.end_date)])

    # Validate date logic
    if exp.start_date and exp.end_date:
        errors.extend([f"{prefix}: {e}" for e in validate_date_logic(exp.start_date, exp.end_date)])

    # Achievements validation
    if not exp.achievements:
        errors.append(f"{prefix}: At least one achievement is recommended")

    return errors


def validate_education(edu: "Education", index: int) -> list[str]:  # type: ignore # noqa: F821
    """Validate an education entry."""
    errors: list[str] = []
    prefix = f"Education {index + 1}"

    if not edu.degree:
        errors.append(f"{prefix}: Degree name is required")

    if not edu.institution:
        errors.append(f"{prefix}: Institution name is required")

    # GPA validation
    if edu.gpa:
        # Check if GPA is in valid format (e.g., "3.8/4.0" or "3.8")
        gpa_match = re.match(r"^(\d+\.?\d*)\s*/?\s*(\d+\.?\d*)?$", edu.gpa)
        if not gpa_match:
            errors.append(f"{prefix}: Invalid GPA format: {edu.gpa}")
        else:
            gpa_value = float(gpa_match.group(1))
            max_gpa = float(gpa_match.group(2)) if gpa_match.group(2) else 4.0

            if gpa_value > max_gpa:
                errors.append(f"{prefix}: GPA value cannot exceed maximum: {edu.gpa}")

    return errors


def _extract_month(date_str: str) -> int | None:
    """Extract month number from date string."""
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    for month_name, month_num in months.items():
        if month_name in date_str.lower():
            return month_num

    # Try to extract month from YYYY-MM format
    month_match = re.search(r"-(\d{2})", date_str)
    if month_match:
        return int(month_match.group(1))

    return None
