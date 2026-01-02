"""
Pytest configuration and fixtures for Resume Customizer MCP Server tests.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest

from resume_customizer.config import Config
from resume_customizer.core.models import (
    Achievement,
    ContactInfo,
    Education,
    Experience,
    MatchBreakdown,
    MatchResult,
    Skill,
    SkillMatch,
    UserProfile,
)


@pytest.fixture
def test_config() -> Config:
    """
    Provide a test configuration with mock API key.

    Returns:
        Test configuration object
    """
    # Set a test API key
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key-for-testing"

    config = Config(
        anthropic_api_key="sk-ant-test-key-for-testing",
        anthropic_model="claude-sonnet-4-20250514",
        max_tokens=4096,
        mcp_server_name="resume_customizer_test",
        mcp_server_version="1.0.0",
        log_level="DEBUG",
        database_path=Path("./test_data/test.db"),
        output_directory=Path("./test_output"),
        cache_directory=Path("./test_cache"),
        enable_ai_extraction=False,  # Disable AI for most tests
        enable_cache=False,  # Disable cache for tests
        cache_ttl_hours=1,
        default_template="modern",
        templates_dir=Path("./templates"),
    )

    return config


@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provide a temporary directory for test files.

    Args:
        tmp_path: Pytest's built-in temp directory fixture

    Yields:
        Path to temporary test directory
    """
    test_dir = tmp_path / "test_resume_customizer"
    test_dir.mkdir(exist_ok=True)

    yield test_dir

    # Cleanup is automatic with tmp_path


@pytest.fixture
def sample_resume_md() -> str:
    """
    Provide sample resume markdown content for testing.

    Returns:
        Sample resume markdown string
    """
    return """# John Doe

## Contact Information
- **Email:** john.doe@example.com
- **Phone:** +1-555-123-4567
- **Location:** San Francisco, CA, USA
- **LinkedIn:** linkedin.com/in/johndoe
- **GitHub:** github.com/johndoe

## Professional Summary
Experienced software engineer with 8 years of expertise in full-stack development,
specializing in Python, AWS, and distributed systems.

## Work Experience

### Senior Software Engineer at Tech Corp
**Jan 2020 - Present** | San Francisco, CA | Remote

**Key Achievements:**
- Reduced API latency by 60% through database optimization and caching strategies
- Led migration of monolithic system to microservices, improving deployment frequency by 5x
- Mentored team of 5 junior engineers, improving code quality and team productivity

**Technologies:** Python, AWS, PostgreSQL, Docker, Kubernetes

### Software Engineer at StartupXYZ
**Jun 2017 - Dec 2019** | San Francisco, CA

**Key Achievements:**
- Built real-time analytics dashboard processing 1M events/day
- Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes

**Technologies:** Python, React, MongoDB, Redis

## Skills

### Programming Languages
Python (Expert, 8 years), JavaScript (Advanced, 6 years), Go (Intermediate, 2 years)

### Frameworks & Libraries
Django, FastAPI, React, Node.js

### Cloud & DevOps
AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes, Terraform

### Databases
PostgreSQL, MongoDB, Redis

## Education

### Bachelor of Science in Computer Science
**Stanford University** | 2017
GPA: 3.8/4.0
"""


@pytest.fixture
def sample_job_md() -> str:
    """
    Provide sample job description markdown content for testing.

    Returns:
        Sample job description markdown string
    """
    return """# Senior Backend Engineer at Amazing Company

## Job Details
- **Company:** Amazing Company
- **Location:** San Francisco, CA / Remote
- **Job Type:** Full-time
- **Posted:** 2025-12-20

## About the Role
We're looking for an experienced backend engineer to join our platform team.

### Responsibilities
- Design and build scalable backend services
- Optimize database performance and queries
- Mentor junior engineers
- Collaborate with product and design teams

### Required Qualifications
- 5+ years of backend development experience
- Strong Python expertise
- Experience with AWS cloud services
- Database optimization skills (PostgreSQL preferred)
- Microservices architecture experience

### Preferred Qualifications
- Kubernetes experience
- Terraform or infrastructure-as-code experience
- Experience with real-time systems

### Technical Requirements
- Python, Django or FastAPI
- AWS (Lambda, RDS, EC2)
- PostgreSQL or similar relational database
- Docker containerization
"""


@pytest.fixture
def complete_profile() -> UserProfile:
    """Create a complete profile with experiences and skills."""
    return UserProfile(
        name="Jane Developer",
        contact=ContactInfo(email="jane@example.com", phone="555-0100"),
        summary="Experienced software engineer with 5 years of experience",
        experiences=[
            Experience(
                company="Tech Corp",
                title="Senior Software Engineer",
                start_date="2022-01",
                end_date="Present",
                achievements=[
                    Achievement(
                        text="Led team of 5 engineers to deliver critical microservices platform",
                        technologies=["Python", "Docker", "Kubernetes"],
                        metrics=["5 engineers", "3 months"],
                        relevance_score=95.0,
                    ),
                    Achievement(
                        text="Reduced API latency by 40% through caching optimization",
                        technologies=["Redis", "Python"],
                        metrics=["40%"],
                        relevance_score=85.0,
                    ),
                    Achievement(
                        text="Implemented CI/CD pipeline reducing deployment time by 60%",
                        technologies=["GitLab CI", "Docker"],
                        metrics=["60%"],
                        relevance_score=80.0,
                    ),
                ],
            ),
            Experience(
                company="StartupXYZ",
                title="Software Engineer",
                start_date="2020-01",
                end_date="2021-12",
                achievements=[
                    Achievement(
                        text="Developed real-time analytics dashboard using React",
                        technologies=["React", "WebSockets"],
                        metrics=[],
                        relevance_score=75.0,
                    ),
                    Achievement(
                        text="Mentored 2 junior engineers on best practices",
                        technologies=[],
                        metrics=["2 engineers"],
                        relevance_score=70.0,
                    ),
                ],
            ),
        ],
        skills=[
            Skill(name="Python", category="Programming", proficiency="Expert", years=5),
            Skill(name="JavaScript", category="Programming", proficiency="Advanced", years=4),
            Skill(name="React", category="Frontend", proficiency="Advanced", years=3),
            Skill(name="Docker", category="DevOps", proficiency="Intermediate", years=2),
            Skill(name="Redis", category="Database", proficiency="Intermediate", years=2),
        ],
        education=[
            Education(
                degree="Bachelor of Science in Computer Science",
                institution="Stanford University",
                graduation_year="2017",
                gpa="3.8",
            )
        ],
    )


@pytest.fixture
def complete_match_result(complete_profile: UserProfile) -> MatchResult:
    """Create a complete match result."""
    # Collect all achievements with scores
    ranked = [
        (complete_profile.experiences[0].achievements[0], 95.0),  # Leadership
        (complete_profile.experiences[0].achievements[1], 85.0),  # Performance
        (complete_profile.experiences[0].achievements[2], 80.0),  # CI/CD
        (complete_profile.experiences[1].achievements[0], 75.0),  # Dashboard
        (complete_profile.experiences[1].achievements[1], 70.0),  # Mentoring
    ]

    return MatchResult(
        profile_id="profile-123",
        job_id="job-456",
        overall_score=85,
        breakdown=MatchBreakdown(
            technical_skills_score=90.0,
            experience_score=85.0,
            domain_score=80.0,
            keyword_coverage_score=75.0,
            total_score=85.0,
        ),
        matched_skills=[
            SkillMatch(
                skill="Python",
                matched=True,
                category="required",
                user_proficiency="Expert",
            ),
            SkillMatch(
                skill="React",
                matched=True,
                category="preferred",
                user_proficiency="Advanced",
            ),
        ],
        missing_required_skills=[],
        missing_preferred_skills=["Kubernetes", "Terraform"],
        ranked_achievements=ranked,
    )
