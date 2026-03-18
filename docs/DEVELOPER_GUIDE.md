# Resume Customizer MCP Server - Developer Guide

**Version**: 1.0.0
**Last Updated**: January 5, 2026

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Testing](#testing)
6. [Code Quality](#code-quality)
7. [Contributing](#contributing)
8. [Release Process](#release-process)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop                          │
│                   (MCP Client)                              │
└────────────────┬────────────────────────────────────────────┘
                 │ MCP Protocol (stdio)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  server.py - MCP Server Entry Point                  │   │
│  │  handlers.py - Tool Call Handlers                    │   │
│  │  tools.py - Tool Definitions                         │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│  ┌────────────────┬──────────────────┬──────────────────┐   │
│  │   Parser       │    Matcher       │   Customizer     │   │
│  │  (Markdown)    │  (Algorithm)     │   (Logic)        │   │
│  └────────────────┴──────────────────┴──────────────────┘   │
│  ┌────────────────┬──────────────────┬──────────────────┐   │
│  │  AI Service    │  Template Engine │   Storage        │   │
│  │  (Claude API)  │  (PDF/DOCX)      │   (SQLite)       │   │
│  └────────────────┴──────────────────┴──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. User provides resume.md and job.md
   │
   ▼
2. Markdown Parser extracts structured data
   │
   ▼
3. Matcher analyzes profile vs job requirements
   │
   ▼
4. AI Service enhances with Claude (optional)
   │
   ▼
5. Customizer reorders/selects content
   │
   ▼
6. Template Engine generates PDF/DOCX
   │
   ▼
7. Files saved to disk
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Runtime** | Python 3.11+ | Core language |
| **MCP SDK** | `mcp` | Model Context Protocol implementation |
| **AI** | Anthropic SDK | Claude API integration |
| **NLP** | spaCy | Natural language processing |
| **PDF** | WeasyPrint | PDF generation |
| **DOCX** | python-docx | Word document generation |
| **Database** | SQLite | Local data persistence |
| **Templates** | Jinja2 | HTML template rendering |
| **Testing** | pytest | Test framework |
| **Type Checking** | mypy | Static type analysis |
| **Linting** | ruff | Fast Python linter |
| **Formatting** | black | Code formatter |

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pip and venv

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd "resume customizer mcp server"

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install spaCy model
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Development Dependencies

The `[dev]` extras include:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks (optional)

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance (Microsoft)
- Ruff (Astral)
- MyPy Type Checker

Workspace settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm

1. Open project
2. Configure Python interpreter (venv)
3. Enable pytest as test runner
4. Configure Black as external tool
5. Install Ruff plugin

---

## Project Structure

```
resume-customizer-mcp/
├── src/resume_customizer/          # Main application code
│   ├── __init__.py
│   ├── server.py                   # MCP server entry point
│   ├── config.py                   # Configuration management
│   │
│   ├── mcp/                        # MCP layer
│   │   ├── __init__.py
│   │   ├── tools.py                # Tool definitions
│   │   └── handlers.py             # Tool call handlers
│   │
│   ├── parsers/                    # Markdown parsing
│   │   ├── __init__.py
│   │   ├── markdown_parser.py      # Resume/job parsing
│   │   └── validator.py            # Data validation
│   │
│   ├── core/                       # Business logic
│   │   ├── __init__.py
│   │   ├── models.py               # Data models (dataclasses)
│   │   ├── matcher.py              # Matching algorithm
│   │   ├── customizer.py           # Customization logic
│   │   ├── ai_service.py           # Claude API integration
│   │   └── exceptions.py           # Custom exceptions
│   │
│   ├── generators/                 # Document generation
│   │   ├── __init__.py
│   │   └── template_engine.py      # PDF/DOCX generation
│   │
│   ├── storage/                    # Data persistence
│   │   ├── __init__.py
│   │   ├── database.py             # SQLite operations
│   │   └── session.py              # In-memory session management
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── helpers.py              # General utilities
│       ├── logger.py               # Logging setup
│       └── validation.py           # Input validation
│
├── templates/                      # Resume templates
│   ├── modern.html
│   ├── classic.html
│   └── ats_optimized.html
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── fixtures/                   # Test data
│   │   ├── test_resume.md
│   │   └── test_job.md
│   ├── test_*.py                   # Test modules
│   └── integration/                # Integration tests
│
├── docs/                           # Documentation
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── TECHNICAL_DESIGN.md
│   └── *.md
│
├── examples/                       # Example files
│   ├── resume.md
│   └── job.md
│
├── pyproject.toml                  # Project metadata & dependencies
├── pytest.ini                      # Pytest configuration
├── .env.example                    # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

### Key Files

| File | Purpose |
|------|---------|
| `server.py` | MCP server initialization and lifecycle |
| `handlers.py` | Implements all 6 MCP tool handlers |
| `tools.py` | Defines MCP tool schemas (JSON Schema) |
| `matcher.py` | Skill matching and scoring algorithms |
| `customizer.py` | Resume customization logic |
| `ai_service.py` | Claude API wrapper with caching |
| `template_engine.py` | PDF/DOCX generation |
| `database.py` | SQLite database operations |
| `session.py` | In-memory session state management |

---

## Core Components

### 1. MCP Server (`server.py`)

Entry point for the MCP server. Handles:
- Server initialization
- Tool registration
- Request/response lifecycle
- Error handling
- Graceful shutdown

```python
# server.py structure
server = Server("resume_customizer")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return ALL_TOOLS

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Dispatch to appropriate handler
    pass
```

### 2. Markdown Parser (`parsers/markdown_parser.py`)

Extracts structured data from Markdown files.

**Key Functions**:
- `parse_resume(markdown_text: str) -> UserProfile`
- `parse_job_description(markdown_text: str) -> JobDescription`

**Parsing Strategy**:
1. Split by headers
2. Extract sections by pattern matching
3. Parse lists and structured data
4. Validate required fields
5. Return structured dataclass

### 3. Matcher (`core/matcher.py`)

Analyzes how well a profile matches job requirements.

**Components**:
- `SkillMatcher`: Matches skills with synonyms and fuzzy matching
- `rank_achievements()`: Ranks achievements by relevance
- `calculate_match_score()`: Computes overall match score

**Scoring Algorithm**:
```
Overall Score = (
    Technical Skills × 0.40 +
    Experience Level × 0.25 +
    Domain Knowledge × 0.20 +
    Keyword Coverage × 0.15
)
```

### 4. Customizer (`core/customizer.py`)

Customizes resume based on match results.

**Key Functions**:
- `reorder_achievements()`: Prioritizes relevant achievements
- `optimize_skills()`: Reorders skills by relevance
- `customize_resume()`: Main orchestration function

**Customization Strategy**:
1. Score all achievements/skills against job
2. Apply selection strategy (top N, min threshold)
3. Reorder by relevance
4. Validate truthfulness (no fabrication)
5. Generate change log

### 5. AI Service (`core/ai_service.py`)

Integrates with Claude API.

**Features**:
- Prompt caching (reduces cost by ~80%)
- Exponential backoff retry
- spaCy fallback for offline mode
- Token usage tracking

**Key Methods**:
- `extract_keywords()`: Extract job keywords with AI
- `rephrase_achievement()`: Optimize achievement text
- `generate_custom_summary()`: Create job-specific summary

### 6. Template Engine (`generators/template_engine.py`)

Generates PDF and DOCX files.

**Templates**:
- **Modern**: Two-column, accent colors, contemporary
- **Classic**: Single-column, serif fonts, traditional
- **ATS Optimized**: Plain text, maximum parsability

**Generation Pipeline**:
1. Load Jinja2 template
2. Prepare context (profile, skills, etc.)
3. Render HTML (for PDF) or build DOCX structure
4. Generate output file
5. Return file path

### 7. Database (`storage/database.py`)

SQLite database for persistence.

**Schema**:
- `profiles`: Cached user profiles
- `jobs`: Cached job descriptions
- `match_results`: Match analyses
- `customizations`: Customized resumes

**Operations**:
- Full CRUD for all tables
- Query by date range, score, company
- Export to JSON/CSV
- Analytics and reporting

### 8. Session Manager (`storage/session.py`)

In-memory cache for fast access.

**Features**:
- TTL-based expiration (default: 1 hour)
- Automatic cleanup
- Hit/miss tracking
- Type-safe generic storage

---

## Testing

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/                      # Test data
│   ├── test_resume.md
│   └── test_job.md
├── test_parsers.py                # Parser tests
├── test_matcher.py                # Matching algorithm tests
├── test_customizer.py             # Customization logic tests
├── test_ai_service.py             # AI integration tests
├── test_template_engine.py        # PDF/DOCX generation tests
├── test_database.py               # Database tests
├── test_session.py                # Session management tests
├── test_handlers_integration.py   # MCP handler tests
└── test_mcp_integration.py        # End-to-end tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/resume_customizer --cov-report=html

# Run specific test file
pytest tests/test_matcher.py

# Run specific test
pytest tests/test_matcher.py::test_skill_matching

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "match"

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Test Coverage

Current coverage: **90.06%**

Coverage by module:
- Core logic: >95% (matcher, customizer, models)
- Utilities: >98% (helpers, validation)
- Storage: >91% (database, session)
- Parsers: >87%
- Generators: >90%

### Writing Tests

#### Unit Test Example

```python
def test_skill_matching():
    """Test exact skill matching."""
    matcher = SkillMatcher()
    user_skills = ["Python", "JavaScript", "React"]
    required_skills = ["python", "javascript"]

    matched, missing = matcher.match_skills(user_skills, required_skills)

    assert len(matched) == 2
    assert len(missing) == 0
```

#### Integration Test Example

```python
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test full workflow from load to generate."""
    # Load resume
    result1 = await handle_load_user_profile({"file_path": "resume.md"})
    profile_id = extract_id(result1)

    # Load job
    result2 = await handle_load_job_description({"file_path": "job.md"})
    job_id = extract_id(result2)

    # Analyze match
    result3 = await handle_analyze_match({
        "profile_id": profile_id,
        "job_id": job_id
    })
    match_id = extract_id(result3)

    # Customize
    result4 = await handle_customize_resume({"match_id": match_id})
    customization_id = extract_id(result4)

    # Generate files
    result5 = await handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["pdf", "docx"]
    })

    assert "pdf" in result5.text
    assert "docx" in result5.text
```

### Test Fixtures

Common fixtures in `conftest.py`:

```python
@pytest.fixture
def sample_profile() -> UserProfile:
    """Create a sample user profile for testing."""
    return UserProfile(
        name="John Doe",
        contact=ContactInfo(email="john@example.com", ...),
        skills=["Python", "JavaScript", ...],
        experiences=[...],
        education=[...],
    )

@pytest.fixture
def sample_job() -> JobDescription:
    """Create a sample job description for testing."""
    return JobDescription(
        title="Senior Software Engineer",
        company="Acme Corp",
        requirements=JobRequirements(
            required_skills=["Python", "Docker"],
            ...
        ),
        ...
    )
```

---

## Code Quality

### Linting with Ruff

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Check specific file
ruff check src/resume_customizer/core/matcher.py
```

Configuration in `pyproject.toml`:
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]
ignore = []
```

### Type Checking with MyPy

```bash
# Check entire project
mypy src/

# Check specific module
mypy src/resume_customizer/core/

# Strict mode
mypy --strict src/
```

Configuration in `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Code Formatting with Black

```bash
# Format code
black src/ tests/

# Check without modifying
black --check src/ tests/

# Format specific file
black src/resume_customizer/core/matcher.py
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

### Pre-commit Hooks (Optional)

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

---

## Contributing

### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   # Format code
   black src/ tests/

   # Lint
   ruff check src/ tests/

   # Type check
   mypy src/

   # Run tests
   pytest
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build/tooling changes

Examples:
```
feat(matcher): add fuzzy skill matching
fix(parser): handle missing education section
docs(api): update tool documentation
test(customizer): add edge case tests
```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Coverage doesn't decrease
- [ ] Documentation updated
- [ ] No new linter warnings
- [ ] Type hints added
- [ ] Commit messages follow convention

---

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features (backward compatible)
- **Patch** (1.0.1): Bug fixes

### Release Checklist

1. **Update version**
   - `pyproject.toml`: `version = "1.1.0"`
   - `src/resume_customizer/__init__.py`: `__version__ = "1.1.0"`

2. **Update CHANGELOG.md**
   ```markdown
   ## [1.1.0] - 2026-01-15

   ### Added
   - New feature X
   - Support for Y

   ### Fixed
   - Bug in Z

   ### Changed
   - Improved performance of A
   ```

3. **Run full test suite**
   ```bash
   pytest --cov=src/resume_customizer --cov-report=html
   ```

4. **Build distribution**
   ```bash
   python -m build
   ```

5. **Create git tag**
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```

6. **Create GitHub release**
   - Go to GitHub Releases
   - Create new release from tag
   - Add release notes
   - Attach distribution files (optional)

### Deployment

For local deployment (users):
```bash
pip install -e .
```

For PyPI deployment (future):
```bash
twine upload dist/*
```

---

## Architecture Decisions

### Why SQLite?
- Lightweight, no separate server needed
- ACID compliance
- Good performance for single-user applications
- Easy backup (single file)

### Why dataclasses over Pydantic?
- Simpler, less overhead
- Native Python (3.7+)
- Sufficient for our needs
- Easy to serialize/deserialize

### Why Jinja2 for templates?
- Mature, well-tested
- Clean separation of logic and presentation
- Good documentation
- Wide adoption

### Why WeasyPrint for PDF?
- Pure Python (easier deployment)
- Good CSS support
- Professional output quality
- Active maintenance

### Why in-memory session + SQLite?
- Fast access for active sessions
- Persistent storage for history
- TTL expiration prevents memory leaks
- Best of both worlds

---

## Performance Considerations

### Bottlenecks

1. **Claude API calls**: ~1-3 seconds per call
   - **Mitigation**: Aggressive prompt caching, spaCy fallback

2. **PDF generation**: ~500ms per document
   - **Mitigation**: Acceptable for single documents

3. **Database queries**: <10ms for typical operations
   - **Mitigation**: Indexes on common query patterns

### Optimization Tips

1. **Cache aggressively**: AI responses, parsed profiles
2. **Use prompt caching**: Saves ~80% on repeated content
3. **Batch operations**: Process multiple customizations together
4. **Lazy loading**: Load large data only when needed
5. **Connection pooling**: Reuse database connections

---

## Debugging

### Enable Debug Logging

```python
# In config.py or .env
LOG_LEVEL=DEBUG
```

### Common Issues

#### "Model not found" error
```bash
python -m spacy download en_core_web_sm
```

#### Import errors
```bash
pip install -e .  # Reinstall in development mode
```

#### Database locked
```python
# Use context manager for all database operations
with DatabaseManager() as db:
    db.get_customization(id)
```

#### MCP server not responding
```bash
# Check Claude Desktop logs
# macOS: ~/Library/Logs/Claude/
# Windows: %APPDATA%\Claude\logs\
```

---

## Resources

### Documentation
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [spaCy Documentation](https://spacy.io/)
- [pytest Documentation](https://docs.pytest.org/)

### Tools
- [Python Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Ruff Rules](https://beta.ruff.rs/docs/rules/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Happy coding! 🚀**

For questions or discussions, use GitHub Issues or Discussions.
