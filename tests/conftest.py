"""
Pytest configuration and fixtures for Resume Customizer MCP Server tests.
"""

import os
from collections.abc import Generator
from pathlib import Path

import pytest

from resume_customizer.config import Config


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
