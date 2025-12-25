"""
Markdown parser for resumes and job descriptions.

This module provides functions to parse markdown-formatted resumes and job
descriptions into structured data models.
"""

import re
from pathlib import Path

from resume_customizer.core.models import (
    Achievement,
    Certification,
    ContactInfo,
    Education,
    Experience,
    JobDescription,
    JobRequirements,
    Project,
    Skill,
    UserProfile,
)
from resume_customizer.utils.helpers import generate_id, get_timestamp
from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)


def parse_resume(file_path: Path | str) -> UserProfile:
    """
    Parse a markdown resume file into a UserProfile object.

    Args:
        file_path: Path to the markdown resume file

    Returns:
        UserProfile object with parsed data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required fields are missing
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    logger.info(f"Parsing resume from {file_path}")

    # Split content into sections
    sections = _split_into_sections(content)

    # Parse name (first H1)
    name = _extract_name(content)

    # Parse contact information
    contact = _parse_contact_section(sections.get("Contact Information", ""))

    # Parse professional summary
    summary = _parse_summary(sections.get("Professional Summary", ""))

    # Parse work experience
    experiences = _parse_experiences(sections.get("Work Experience", ""))

    # Parse skills
    skills = _parse_skills(sections.get("Skills", ""))

    # Parse education
    education = _parse_education(sections.get("Education", ""))

    # Parse certifications
    certifications = _parse_certifications(sections.get("Certifications", ""))

    # Parse projects
    projects = _parse_projects(sections.get("Projects", ""))

    # Parse preferences
    preferences = _parse_preferences(sections.get("Preferences", ""))

    profile = UserProfile(
        name=name,
        contact=contact,
        summary=summary,
        experiences=experiences,
        skills=skills,
        education=education,
        certifications=certifications,
        projects=projects,
        preferences=preferences,
        profile_id=generate_id("profile"),
        created_at=get_timestamp(),
    )

    logger.info(f"Successfully parsed resume: {name}")
    return profile


def parse_job_description(file_path: Path | str) -> JobDescription:
    """
    Parse a markdown job description file into a JobDescription object.

    Args:
        file_path: Path to the markdown job description file

    Returns:
        JobDescription object with parsed data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required fields are missing
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Job description file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    logger.info(f"Parsing job description from {file_path}")

    # Split content into sections
    sections = _split_into_sections(content)

    # Parse job title and company (first H1)
    title, company = _extract_job_title_company(content)

    # Parse job details
    job_details = _parse_job_details(sections.get("Job Details", ""))

    # Parse responsibilities
    responsibilities = _parse_list_section(sections.get("Responsibilities", ""))

    # Parse requirements
    requirements = _parse_requirements(
        sections.get("Required Qualifications", ""),
        sections.get("Preferred Qualifications", ""),
    )

    # Parse technical stack
    technical_stack = _parse_technical_stack(sections.get("Technical Stack", ""))

    # Extract description
    description = sections.get("Job Description", "").strip()

    # Company description
    company_description = sections.get("About the Company", "").strip()

    # Ensure company is not None
    final_company = company if company else job_details.get("company")
    if not final_company:
        final_company = "Unknown"

    job = JobDescription(
        title=title,
        company=final_company,
        location=job_details.get("location"),
        job_type=job_details.get("job_type"),
        experience_level=job_details.get("experience_level"),
        salary_range=job_details.get("salary_range"),
        description=description,
        responsibilities=responsibilities,
        requirements=requirements,
        technical_stack=technical_stack,
        company_description=company_description,
        apply_url=job_details.get("apply_url"),
        posted_date=job_details.get("posted_date"),
        job_id=generate_id("job"),
        created_at=get_timestamp(),
    )

    logger.info(f"Successfully parsed job: {title} at {company}")
    return job


# Helper functions


def _split_into_sections(content: str) -> dict[str, str]:
    """Split markdown content into sections based on H2 headers."""
    sections: dict[str, str] = {}
    current_section = None
    current_content: list[str] = []

    for line in content.split("\n"):
        # H2 header (## Section Name)
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    # Add last section
    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _extract_name(content: str) -> str:
    """Extract name from first H1 header."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not match:
        raise ValueError("Resume must start with name in H1 header (# Name)")
    name = match.group(1).strip()
    # Remove template brackets if present
    name = re.sub(r"\[|\]", "", name)
    if not name or name.lower() in ["your full name", "name"]:
        raise ValueError("Please replace [Your Full Name] with your actual name")
    return name


def _extract_job_title_company(content: str) -> tuple[str, str]:
    """Extract job title and company from first H1 header."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if not match:
        raise ValueError("Job description must start with title in H1 header")

    title_line = match.group(1).strip()

    # Try to parse "Title at Company" format
    if " at " in title_line:
        parts = title_line.split(" at ", 1)
        title = parts[0].strip()
        company = parts[1].strip()
    else:
        title = title_line
        company = ""

    # Remove template brackets
    title = re.sub(r"\[|\]", "", title)
    company = re.sub(r"\[|\]", "", company)

    return title, company


def _parse_contact_section(section: str) -> ContactInfo:
    """Parse contact information section."""
    contact_data: dict[str, str | None] = {
        "email": None,
        "phone": None,
        "location": None,
        "linkedin": None,
        "github": None,
        "portfolio": None,
    }
    other: dict[str, str] = {}

    for line in section.split("\n"):
        line = line.strip()
        if not line or not line.startswith("-"):
            continue

        # Remove leading "- " and split on ":"
        line = line[2:].strip()
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().replace("*", "").lower()
        value = value.strip()

        if key == "email":
            contact_data["email"] = value
        elif key == "phone":
            contact_data["phone"] = value
        elif key == "location":
            contact_data["location"] = value
        elif key == "linkedin":
            contact_data["linkedin"] = value
        elif key == "github":
            contact_data["github"] = value
        elif key in ["portfolio", "website"]:
            contact_data["portfolio"] = value
        else:
            other[key] = value

    if not contact_data["email"]:
        raise ValueError("Email is required in contact information")

    # Email is guaranteed to be str by validation above, mypy can't infer this
    email_str = str(contact_data["email"])

    return ContactInfo(
        email=email_str,
        phone=contact_data["phone"],
        location=contact_data["location"],
        linkedin=contact_data["linkedin"],
        github=contact_data["github"],
        portfolio=contact_data["portfolio"],
        other=other,
    )


def _parse_summary(section: str) -> str:
    """Parse professional summary section."""
    # Remove example text and clean up
    lines = []
    for line in section.split("\n"):
        line = line.strip()
        if line and not line.lower().startswith("example:"):
            lines.append(line)

    summary = " ".join(lines).strip()
    if not summary:
        raise ValueError("Professional summary is required")

    return summary


def _parse_experiences(section: str) -> list[Experience]:
    """Parse work experience section."""
    experiences: list[Experience] = []

    # Split by H3 (###) headers for each job
    job_sections = re.split(r"\n###\s+", section)

    for job_section in job_sections:
        if not job_section.strip():
            continue

        experience = _parse_single_experience(job_section)
        if experience:
            experiences.append(experience)

    if not experiences:
        raise ValueError("At least one work experience is required")

    return experiences


def _parse_single_experience(section: str) -> Experience | None:
    """Parse a single work experience entry."""
    lines = section.split("\n")
    if not lines:
        return None

    # First line: "Title at Company"
    title_line = lines[0].strip()
    if " at " in title_line:
        title, company = title_line.split(" at ", 1)
        title = title.strip()
        company = company.strip()
    else:
        return None

    # Second line: "Date Range | Location | Work Mode"
    if len(lines) < 2:
        return None

    date_line = lines[1].strip().replace("**", "")
    date_parts = [p.strip() for p in date_line.split("|")]

    start_date, end_date = _parse_date_range(date_parts[0] if date_parts else "")
    location = date_parts[1] if len(date_parts) > 1 else None
    work_mode = date_parts[2] if len(date_parts) > 2 else None

    # Parse description and achievements
    description = ""
    achievements: list[Achievement] = []
    technologies: list[str] = []
    in_achievements = False

    for line in lines[2:]:
        line = line.strip()

        if line.startswith("**Key Achievements:**"):
            in_achievements = True
            continue
        elif line.startswith("**Technologies:**"):
            # Extract technologies
            tech_text = line.replace("**Technologies:**", "").strip()
            technologies = [t.strip() for t in tech_text.split(",") if t.strip()]
            in_achievements = False
            continue
        elif line.startswith("---"):
            break

        if in_achievements and line.startswith("-"):
            # Achievement bullet point
            achievement_text = line[1:].strip()
            achievements.append(Achievement(text=achievement_text))
        elif not in_achievements and line and not line.startswith("**"):
            # Description
            description += line + " "

    return Experience(
        company=company,
        title=title,
        start_date=start_date,
        end_date=end_date,
        location=location,
        work_mode=work_mode,
        description=description.strip(),
        achievements=achievements,
        technologies=technologies,
    )


def _parse_date_range(date_str: str) -> tuple[str, str]:
    """Parse date range string into start and end dates."""
    if "-" in date_str:
        parts = date_str.split("-", 1)
        start = parts[0].strip()
        end = parts[1].strip()
    else:
        start = date_str.strip()
        end = "Present"

    return start, end


def _parse_skills(section: str) -> list[Skill]:
    """Parse skills section."""
    skills: list[Skill] = []
    current_category = "General"

    for line in section.split("\n"):
        line = line.strip()

        # H3 category header
        if line.startswith("###"):
            current_category = line[3:].strip()
            continue

        # Bullet point with skill
        if line.startswith("-"):
            skill_text = line[1:].strip()

            # Check for proficiency and years in parentheses
            proficiency = None
            years = None
            description = None

            # Pattern: "Python (Expert, 8+ years) - Description"
            match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*(?:-\s*(.+))?$", skill_text)
            if match:
                skill_name = match.group(1).strip()
                details = match.group(2).strip()
                description = match.group(3).strip() if match.group(3) else None

                # Parse details for proficiency and years
                detail_parts = [p.strip() for p in details.split(",")]
                for part in detail_parts:
                    if any(
                        level in part.lower()
                        for level in ["expert", "advanced", "intermediate", "basic"]
                    ):
                        proficiency = part
                    elif "year" in part.lower():
                        # Extract number
                        year_match = re.search(r"(\d+)", part)
                        if year_match:
                            years = int(year_match.group(1))
            else:
                skill_name = skill_text

            skills.append(
                Skill(
                    name=skill_name,
                    category=current_category,
                    proficiency=proficiency,
                    years=years,
                    description=description,
                )
            )
        # Comma-separated list
        elif line and not line.startswith("#"):
            skill_names = [s.strip() for s in line.split(",") if s.strip()]
            for skill_name in skill_names:
                skills.append(Skill(name=skill_name, category=current_category))

    if not skills:
        raise ValueError("At least one skill is required")

    return skills


def _parse_education(section: str) -> list[Education]:
    """Parse education section."""
    education: list[Education] = []

    # Split by H3 headers
    edu_sections = re.split(r"\n###\s+", section)

    for edu_section in edu_sections:
        if not edu_section.strip():
            continue

        lines = edu_section.split("\n")
        degree = lines[0].strip()

        institution = None
        graduation_year = None
        gpa = None
        location = None
        details: list[str] = []

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("---"):
                continue

            # Institution and year: "**University Name** | Year"
            if line.startswith("**") and "|" in line:
                parts = line.replace("**", "").split("|")
                institution = parts[0].strip()
                if len(parts) > 1:
                    graduation_year = parts[1].strip()
            elif line.lower().startswith("gpa:"):
                gpa = line.split(":", 1)[1].strip()
            elif line.lower().startswith("location:"):
                location = line.split(":", 1)[1].strip()
            elif line.startswith("-"):
                details.append(line[1:].strip())

        if degree and institution:
            education.append(
                Education(
                    degree=degree,
                    institution=institution,
                    graduation_year=graduation_year,
                    gpa=gpa,
                    location=location,
                    details=details,
                )
            )

    return education


def _parse_certifications(section: str) -> list[Certification]:
    """Parse certifications section."""
    certifications: list[Certification] = []

    for line in section.split("\n"):
        line = line.strip()
        if not line.startswith("-"):
            continue

        # Format: "- Certification Name - Issuer (Date)"
        line = line[1:].strip()

        # Try to parse structured format
        match = re.match(r"^(.+?)\s*-\s*(.+?)\s*\(([^)]+)\)$", line)
        if match:
            name = match.group(1).strip()
            issuer = match.group(2).strip()
            date = match.group(3).strip()

            certifications.append(Certification(name=name, issuer=issuer, date=date))
        else:
            # Simple format: just the certification name
            certifications.append(Certification(name=line, issuer=""))

    return certifications


def _parse_projects(section: str) -> list[Project]:
    """Parse projects section."""
    projects: list[Project] = []

    # Split by H3 headers
    project_sections = re.split(r"\n###\s+", section)

    for project_section in project_sections:
        if not project_section.strip():
            continue

        lines = project_section.split("\n")
        name = lines[0].strip()

        description = ""
        technologies: list[str] = []
        url = None
        github = None
        highlights: list[str] = []

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("---"):
                continue

            if line.lower().startswith("**technologies:**"):
                tech_text = line.split(":", 1)[1].strip()
                technologies = [t.strip() for t in tech_text.split(",") if t.strip()]
            elif line.lower().startswith("**url:**"):
                url = line.split(":", 1)[1].strip()
            elif line.lower().startswith("**github:**"):
                github = line.split(":", 1)[1].strip()
            elif line.startswith("-"):
                highlights.append(line[1:].strip())
            elif not line.startswith("**"):
                description += line + " "

        if name:
            projects.append(
                Project(
                    name=name,
                    description=description.strip(),
                    technologies=technologies,
                    url=url,
                    github=github,
                    highlights=highlights,
                )
            )

    return projects


def _parse_preferences(section: str) -> dict[str, str | int]:
    """Parse preferences section."""
    preferences: dict[str, str | int] = {}

    for line in section.split("\n"):
        line = line.strip()
        if not line or not line.startswith("-"):
            continue

        line = line[1:].strip()
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()

            # Try to parse as int
            try:
                preferences[key] = int(value)
            except ValueError:
                preferences[key] = value

    return preferences


def _parse_job_details(section: str) -> dict[str, str | None]:
    """Parse job details section."""
    details: dict[str, str | None] = {}

    for line in section.split("\n"):
        line = line.strip()
        if not line or not line.startswith("-"):
            continue

        line = line[1:].strip().replace("**", "")
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()

        details[key] = value

    return details


def _parse_list_section(section: str) -> list[str]:
    """Parse a section with bullet points into a list."""
    items: list[str] = []

    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("-"):
            items.append(line[1:].strip())

    return items


def _parse_requirements(required_section: str, preferred_section: str) -> JobRequirements:
    """Parse required and preferred qualifications."""
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    required_experience_years = None
    required_education = None
    other_requirements: list[str] = []

    # Parse required qualifications
    for line in required_section.split("\n"):
        line = line.strip()
        if not line.startswith("-"):
            continue

        requirement = line[1:].strip()

        # Extract years of experience
        year_match = re.search(r"(\d+)\+?\s*years?", requirement, re.IGNORECASE)
        if year_match and not required_experience_years:
            required_experience_years = int(year_match.group(1))

        # Check for education requirement
        if any(degree in requirement.lower() for degree in ["bachelor", "master", "phd", "degree"]):
            required_education = requirement
        else:
            required_skills.append(requirement)

    # Parse preferred qualifications
    for line in preferred_section.split("\n"):
        line = line.strip()
        if line.startswith("-"):
            preferred_skills.append(line[1:].strip())

    return JobRequirements(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        required_experience_years=required_experience_years,
        required_education=required_education,
        other_requirements=other_requirements,
    )


def _parse_technical_stack(section: str) -> list[str]:
    """Parse technical stack section."""
    technologies: list[str] = []

    for line in section.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Bullet point
        if line.startswith("-"):
            line = line[1:].strip()

        # Comma-separated or single tech
        if "," in line:
            techs = [t.strip() for t in line.split(",") if t.strip()]
            technologies.extend(techs)
        else:
            technologies.append(line)

    return technologies
