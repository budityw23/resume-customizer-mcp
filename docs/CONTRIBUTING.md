# Contributing to Resume Customizer MCP Server

Thank you for your interest in contributing to Resume Customizer MCP Server! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation](#documentation)
7. [Submitting Changes](#submitting-changes)
8. [Release Process](#release-process)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. We expect all contributors to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discriminatory comments, or personal attacks
- Trolling, insulting/derogatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- Claude API key (for testing AI features)

### Development Setup

1. **Fork the repository**
   ```bash
   # On GitHub, click "Fork" button
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/resume-customizer-mcp.git
   cd "resume customizer mcp server"
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/resume-customizer-mcp.git
   ```

4. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Add your ANTHROPIC_API_KEY to .env
   ```

6. **Verify setup**
   ```bash
   pytest
   ruff check src/ tests/
   mypy src/
   ```

---

## Development Workflow

### Creating a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Branch Naming Convention

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/modifications
- `chore/description` - Build/tooling changes

### Making Changes

1. **Write code**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

2. **Run quality checks**
   ```bash
   # Format code
   black src/ tests/

   # Lint
   ruff check src/ tests/

   # Type check
   mypy src/

   # Run tests
   pytest

   # Check coverage
   pytest --cov=src/resume_customizer --cov-report=term-missing
   ```

3. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

### Keeping Your Branch Updated

```bash
# Fetch latest changes from upstream
git fetch upstream

# Rebase your branch
git rebase upstream/main

# Force push to your fork
git push origin feature/your-feature-name --force
```

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these tools:

#### Black (Code Formatting)
- Line length: 88 characters
- Run: `black src/ tests/`

#### Ruff (Linting)
- Enforces PEP 8, import order, and best practices
- Run: `ruff check src/ tests/ --fix`

#### MyPy (Type Checking)
- All functions must have type hints
- Run: `mypy src/`

### Code Organization

```python
# 1. Standard library imports
import os
import sys
from pathlib import Path

# 2. Third-party imports
import anthropic
from mcp.types import Tool

# 3. Local imports
from resume_customizer.core.models import UserProfile
from resume_customizer.utils.logger import get_logger
```

### Docstrings

Use Google-style docstrings:

```python
def customize_resume(
    profile: UserProfile,
    match_result: MatchResult,
    preferences: CustomizationPreferences | None = None,
) -> CustomizedResume:
    """
    Customize a resume based on match analysis.

    Args:
        profile: The user's profile to customize
        match_result: Match analysis result
        preferences: Customization preferences (optional)

    Returns:
        Customized resume with reordered achievements and skills

    Raises:
        ValidationError: If profile or match_result is invalid
        ValueError: If achievements contain fabricated content
    """
    pass
```

### Type Hints

All functions must have complete type hints:

```python
def process_data(
    data: dict[str, Any],
    options: list[str] | None = None,
) -> tuple[bool, str]:
    """Process data and return status."""
    pass
```

### Error Handling

Use custom exceptions with helpful messages:

```python
from resume_customizer.core.exceptions import ValidationError

if not file_path:
    raise ValidationError(
        field="file_path",
        message="File path is required",
        suggestion="Please provide a valid file path."
    )
```

### Logging

Use structured logging:

```python
from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Processing profile", extra={"profile_id": profile_id})
logger.warning("Low match score", extra={"score": score})
logger.error("API call failed", extra={"error": str(e)})
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py                # Shared fixtures
├── fixtures/                  # Test data
├── test_parsers.py           # Parser tests
├── test_matcher.py           # Matching tests
└── test_customizer.py        # Customization tests
```

### Writing Tests

#### Unit Tests

```python
def test_skill_matching():
    """Test exact skill matching."""
    matcher = SkillMatcher()
    user_skills = ["Python", "JavaScript"]
    required_skills = ["python", "javascript"]

    matched, missing = matcher.match_skills(user_skills, required_skills)

    assert len(matched) == 2
    assert len(missing) == 0
```

#### Fixtures

```python
@pytest.fixture
def sample_profile() -> UserProfile:
    """Create a sample user profile for testing."""
    return UserProfile(
        name="John Doe",
        contact=ContactInfo(email="john@example.com"),
        skills=["Python", "JavaScript"],
        experiences=[...],
        education=[...],
    )
```

#### Parametrized Tests

```python
@pytest.mark.parametrize("email,expected", [
    ("valid@example.com", True),
    ("invalid", False),
    ("@example.com", False),
])
def test_email_validation(email, expected):
    """Test email validation with multiple inputs."""
    is_valid = validate_email(email)
    assert is_valid == expected
```

### Test Coverage

- **Minimum**: 80% coverage for new code
- **Target**: 90% coverage overall
- **Critical paths**: 100% coverage (matching, customization, validation)

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_matcher.py

# Specific test
pytest tests/test_matcher.py::test_skill_matching

# With coverage
pytest --cov=src/resume_customizer --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

---

## Documentation

### Code Documentation

- **All functions**: Docstrings with Args, Returns, Raises
- **All classes**: Class docstring with purpose and usage
- **All modules**: Module docstring with overview
- **Complex logic**: Inline comments explaining why, not what

### User Documentation

Update when adding features:
- `docs/USER_GUIDE.md` - User-facing documentation
- `docs/API_REFERENCE.md` - MCP tool documentation
- `README.md` - Project overview

### Developer Documentation

Update when changing architecture:
- `docs/DEVELOPER_GUIDE.md` - Development guide
- `docs/TECHNICAL_DESIGN.md` - Architecture docs

---

## Submitting Changes

### Before Submitting

**Checklist**:
- [ ] Code follows style guidelines
- [ ] All tests pass (`pytest`)
- [ ] No linter errors (`ruff check src/ tests/`)
- [ ] Type checks pass (`mypy src/`)
- [ ] Code is formatted (`black src/ tests/`)
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Coverage doesn't decrease
- [ ] Commit messages follow convention

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build/tooling changes
- `style`: Code style changes (formatting, no logic change)

**Examples**:
```
feat(matcher): add fuzzy skill matching
fix(parser): handle missing education section
docs(api): update tool documentation
test(customizer): add edge case tests
refactor(ai): simplify prompt generation
```

### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**
   - Go to your fork on GitHub
   - Click "Pull Request"
   - Select your feature branch
   - Fill in the PR template

3. **PR Title**
   ```
   feat: Add fuzzy skill matching to matcher
   ```

4. **PR Description**
   ```markdown
   ## Summary
   Adds fuzzy matching capability to skill matcher using Levenshtein distance.

   ## Changes
   - Added fuzzy_match() function to SkillMatcher
   - Added threshold parameter (default: 0.8)
   - Added tests for fuzzy matching
   - Updated documentation

   ## Testing
   - Added 15 unit tests
   - All existing tests pass
   - Coverage increased from 95% to 96%

   ## Related Issues
   Closes #42
   ```

### Code Review Process

1. **Automated Checks**
   - GitHub Actions run tests, linting, type checking
   - All checks must pass

2. **Maintainer Review**
   - Code quality
   - Test coverage
   - Documentation
   - Design decisions

3. **Addressing Feedback**
   ```bash
   # Make requested changes
   git add .
   git commit -m "refactor: apply review feedback"
   git push origin feature/your-feature-name
   ```

4. **Merging**
   - Maintainer will merge when approved
   - Branch will be deleted automatically

---

## Release Process

### Version Numbers

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: New features, backward compatible (e.g., 1.0.0 → 1.1.0)
- **PATCH**: Bug fixes, backward compatible (e.g., 1.0.0 → 1.0.1)

### Release Checklist

For maintainers:

1. **Update version**
   - `pyproject.toml`: `version = "1.1.0"`
   - `src/resume_customizer/__init__.py`: `__version__ = "1.1.0"`

2. **Update CHANGELOG.md**
   ```markdown
   ## [1.1.0] - 2026-02-01

   ### Added
   - New feature X

   ### Fixed
   - Bug in Y

   ### Changed
   - Improved Z
   ```

3. **Run full test suite**
   ```bash
   pytest --cov=src/resume_customizer
   ruff check src/ tests/
   mypy src/
   ```

4. **Create git tag**
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

5. **Create GitHub release**
   - Go to GitHub Releases
   - Create new release from tag
   - Add release notes from CHANGELOG
   - Attach distribution files (optional)

---

## Questions?

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Documentation**: See `docs/` directory

---

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes
- Project documentation

Thank you for contributing to Resume Customizer MCP Server! 🎉
