# Resume Customizer MCP Server - Project Configuration

This file contains custom instructions and guidelines for working on this project.

## Project Overview

This is an MCP (Model Context Protocol) server for AI-powered resume customization. The project uses Python 3.10+, follows Domain-Driven Design principles, and integrates with Claude AI for intelligent resume optimization.

## Working Style with Claude Code

### Response Guidelines
- **Be Concise**: No summaries, explanations, or "What We Built" sections unless explicitly asked
- **No New Docs**: Don't create documentation files unless explicitly requested
- **Completion Format**: Just confirm completion with test results:
  ```
  Phase X.Y complete ✅
  
  Created/Modified:
  - file1.py
  - file2.py
  
  Tests: X/X passing
  Coverage: XX%
  Ruff: ✅
  MyPy: ✅
  ```
- **No Code Examples**: Don't include usage examples in responses unless asked
- **No "Next Steps"**: Don't suggest what to do next - I'll tell you
- **Errors Only**: Only provide details if something failed

### What TO Include
- ✅ Implementation (code only)
- ✅ Tests
- ✅ Run linters and report results
- ✅ Fix any issues found
- ✅ Brief file list of what changed

### What NOT to Include
- ❌ Summaries of what was built
- ❌ "How It Works" explanations
- ❌ "Key Features" lists
- ❌ Usage examples in responses
- ❌ "Next Steps" suggestions
- ❌ Creating README.md sections
- ❌ Creating new documentation files
- ❌ Verbose explanations

### Example Workflow
```
User: "Implement Phase 5.1"

Good Response:
---
Phase 5.1 complete ✅

Created:
- src/resume_customizer/generators/template_engine.py
- templates/modern.html
- templates/classic.html
- tests/test_template_engine.py

Tests: 31/31 passing
Coverage: 89%
Ruff: ✅
MyPy: ✅
---

Bad Response:
---
Perfect! Phase 5.1 Template System is now complete! 🎉

What We Built:
1. Template Engine with amazing features...
[500 lines of summary]

Key Features:
- Smart Data Merging...
[More explanations]

How It Works:
```python
[Code examples]
```

Next Steps:
Would you like to...
---
```

### When Verbose Responses Are OK
- When debugging complex errors
- When explicitly asked: "Explain how X works"
- When explicitly asked: "Summarize what we've done"
- When proposing architectural decisions

## Code Style and Standards

### Python Style
- **Style Guide**: Follow PEP 8
- **Line Length**: Maximum 100 characters (configured in pyproject.toml)
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Use Google-style docstrings for all public functions
- **Linting**: Use `ruff` for linting and formatting
- **Type Checking**: Use `mypy` for static type checking

### Testing Standards
- **Framework**: pytest
- **Coverage**: Maintain >80% code coverage
- **Test Files**: Name test files as `test_<module_name>.py`
- **Test Functions**: Name test functions as `test_<behavior>_<expected_result>()`
- **Fixtures**: Use pytest fixtures for common test setup
- **Assertions**: Use descriptive assertion messages

### File and Directory Naming

#### General Rules
- **Python Files**: Use `snake_case.py` (e.g., `ai_service.py`, `match_scorer.py`)
- **Test Files**: Use `test_snake_case.py` (e.g., `test_ai_service.py`)
- **Directories**: Use `snake_case/` (e.g., `resume_customizer/`, `test_data/`)
- **Config Files**: Use `snake_case.yaml` or `snake_case.json`

#### Documentation Files
- **Location**: All documentation must go in the `docs/` folder
- **Naming**: Use `SCREAMING_SNAKE_CASE.md` for main docs (e.g., `README.md`, `IMPLEMENTATION_CHECKLIST.md`)
- **Naming**: Use `snake_case.md` for guides and supporting docs (e.g., `phase2_manual_testing.md`, `api_reference.md`)
- **Examples**:
  - `docs/README.md` - Main documentation
  - `docs/IMPLEMENTATION_CHECKLIST.md` - Implementation tracking
  - `docs/api_reference.md` - API documentation
  - `docs/deployment_guide.md` - Deployment instructions

#### Example Files
- **Location**: All examples must go in the `examples/` folder
- **Organization**: Group by type in subdirectories
  - `examples/resumes/` - Example resume files
  - `examples/jobs/` - Example job description files
  - `examples/scripts/` - Example usage scripts

## Project Structure

```
resume-customizer-mcp/
├── .claude/                 # Claude Code configuration
├── config/                  # Configuration files (YAML, JSON)
├── docs/                    # All documentation
├── examples/                # Example files
├── src/
│   └── resume_customizer/   # Main package
│       ├── core/            # Core business logic
│       ├── mcp/             # MCP server implementation
│       ├── parsers/         # File parsers
│       └── utils/           # Utility functions
├── tests/                   # All test files
└── templates/               # Document templates
```

## Git Commit Guidelines

### Commit Message Format
Use Conventional Commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build process, dependencies, etc.
- `style`: Code style changes (formatting, missing semicolons, etc.)

### Important Rules
- **NO Attribution Footers**: Do NOT include these lines:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
  ```
- **Commit Message**: First line should be ≤72 characters
- **Body**: Wrap at 72 characters, explain what and why (not how)
- **Scope**: Use module names (e.g., `matcher`, `handlers`, `tests`)

### Examples
```
feat(matcher): add fuzzy skill matching with configurable threshold

Implements fuzzy string matching for skills using rapidfuzz library.
Allows matching skills with small typos or variations.

- Added configurable similarity threshold (default: 0.85)
- Added unit tests for various matching scenarios
- Updated skill_synonyms.yaml with common variations
```

```
fix(parsers): handle resume files without phone number

Previously crashed when phone field was missing. Now treats
phone as optional field with None default.

Fixes #42
```

## Code Organization

### Imports Order
1. Standard library imports
2. Third-party imports
3. Local application imports

Use blank lines to separate groups.

```python
import os
from typing import Any

from anthropic import Anthropic
import spacy

from resume_customizer.core.matcher import calculate_match_score
from resume_customizer.utils.logger import get_logger
```

### Function Organization
- Put public functions first
- Private functions (prefixed with `_`) last
- Group related functions together
- Add section comments for major groups

## Testing Guidelines

### Test Organization
- One test file per module
- Group related tests in classes
- Use descriptive test names that explain the scenario

```python
class TestSkillMatcher:
    def test_exact_match_returns_100_percent_score(self):
        """Test that identical skills return perfect match score."""
        # Arrange, Act, Assert
```

### Test Data
- Store test data in `tests/fixtures/` or `tests/test_data/`
- Use pytest fixtures for reusable test data
- Name fixture files clearly: `resume_samples.py`, `job_samples.py`

### Running Tests
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_matcher.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_matcher.py::test_skill_matching
```

## Documentation Guidelines

### Code Documentation
- All public functions must have docstrings
- Use Google-style docstrings
- Include Args, Returns, Raises sections
- Add usage examples for complex functions

```python
def calculate_match_score(profile: UserProfile, job: JobDescription) -> MatchResult:
    """
    Calculate comprehensive match score between a profile and job.

    This function analyzes technical skills, experience level, domain knowledge,
    and keyword coverage to produce an overall match score.

    Args:
        profile: User's profile with skills and experience
        job: Job description with requirements

    Returns:
        MatchResult object containing scores and analysis

    Raises:
        ValueError: If profile or job is missing required fields

    Example:
        >>> profile = parse_resume("resume.md")
        >>> job = parse_job_description("job.md")
        >>> result = calculate_match_score(profile, job)
        >>> print(f"Match: {result.overall_score}%")
    """
```

### Markdown Documentation
- Use proper heading hierarchy (# > ## > ###)
- Include table of contents for long documents
- Use code blocks with language specification
- Add links to related documents

## Environment Setup

### Required Environment Variables
Create a `.env` file (never commit this):
```bash
ANTHROPIC_API_KEY=sk-ant-xxx
LOG_LEVEL=INFO
CACHE_DIR=.cache
```

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Download spaCy model
python -m spacy download en_core_web_sm

# Run tests
pytest
```

## Performance Guidelines

- **Caching**: Cache expensive operations (API calls, file parsing)
- **Lazy Loading**: Load large resources only when needed
- **Async**: Use async/await for I/O operations where appropriate
- **Profiling**: Profile performance-critical code
- **Target**: Matching should complete in <5 seconds

## Security Guidelines

- **Never commit**: API keys, credentials, or sensitive data
- **Use .env**: Store secrets in environment variables
- **Validate Input**: Validate all user inputs and file uploads
- **Sanitize**: Sanitize data before using in prompts or queries
- **Rate Limiting**: Implement rate limiting for API calls
- **Error Messages**: Don't expose internal details in error messages

## AI/LLM Guidelines

### Prompt Engineering
- Store prompts in `config/prompts/` directory
- Use template files with placeholders
- Version prompts (include version in filename)
- Document expected input/output format

### API Usage
- Always handle API errors gracefully
- Implement retry logic with exponential backoff
- Cache API responses when appropriate
- Monitor API costs and usage

## Dependency Management

### Adding Dependencies
1. Add to `pyproject.toml` in appropriate section
2. Run `pip install -e ".[dev]"` to install
3. Update README if it's a major dependency
4. Document why the dependency was added

### Updating Dependencies
```bash
# Update all dependencies
pip install --upgrade -e ".[dev]"

# Check for outdated packages
pip list --outdated
```

## Common Tasks

### Running Quality Checks
```bash
# Run all checks before committing
ruff check src/ tests/          # Linting
mypy src/                       # Type checking
pytest --cov                     # Tests with coverage
```

### Building Documentation
```bash
# Generate API documentation
# (Add specific commands when documentation is set up)
```

### Creating a Release
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
5. Push tag: `git push origin v1.0.0`

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure package is installed in editable mode: `pip install -e .`
2. **spaCy model missing**: Download model: `python -m spacy download en_core_web_sm`
3. **API errors**: Check `.env` file has correct `ANTHROPIC_API_KEY`
4. **Test failures**: Clear pytest cache: `pytest --cache-clear`

## Project-Specific Notes

### Phase Tracking
- Implementation progress tracked in `docs/IMPLEMENTATION_CHECKLIST.md`
- Mark items complete with `[x]` only when fully tested
- Add sign-off date when completing phases

### Session State
- MCP handlers use module-level `_session_state` dictionary
- Clear state between tests using fixtures
- State includes: profiles, jobs, matches, customizations

### Skill Matching
- Skill synonyms defined in `config/skill_synonyms.yaml`
- Hierarchies defined in `config/skill_hierarchies.yaml`
- Fuzzy matching threshold: 85% (configurable)

## Questions or Issues?

- Check existing documentation in `docs/`
- Review test files for usage examples
- Check GitHub issues for known problems
- Follow existing code patterns in the codebase