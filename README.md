# Resume Customizer MCP Server

An MCP (Model Context Protocol) server that enables Claude to intelligently customize resumes by analyzing user profiles and job descriptions, then generating optimized, professional resume outputs.

## Features

- **Smart Job Matching**: Analyzes your profile against job requirements with detailed scoring
- **AI-Powered Customization**: Uses Claude to generate job-specific summaries and keyword optimization
- **Achievement Ranking**: Automatically ranks and selects the most relevant achievements
- **Multi-Format Output**: Generates professional PDF and editable DOCX files
- **Template System**: Modern, Classic, and ATS-optimized templates
- **No Fabrication**: Maintains 100% truthfulness - never adds skills or achievements you don't have

## Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd "resume customizer mcp server"
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -e .
```

4. **Install spaCy model**
```bash
python -m spacy download en_core_web_sm
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Usage with Claude Desktop

Add to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "resume_customizer": {
      "command": "python",
      "args": ["-m", "resume_customizer.server"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Creating Your Resume

1. Create `resume.md` following the template in `docs/resume_template.md`
2. Create `job.md` with the job description using `docs/job_template.md`
3. Chat with Claude: "Customize my resume for this job"

## Project Structure

```
resume-customizer-mcp/
├── src/resume_customizer/     # Main application code
│   ├── mcp/                   # MCP server and tools
│   ├── parsers/               # Markdown parsing
│   ├── core/                  # Business logic
│   ├── generators/            # PDF/DOCX generation
│   ├── storage/               # Database and file management
│   └── utils/                 # Utility functions
├── templates/                 # Resume templates
├── examples/                  # Example resumes and jobs
├── tests/                     # Test suite
└── docs/                      # Documentation
```

## Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Development Installation
```bash
pip install -e ".[dev]"
```

## Documentation

- [Technical Design](docs/TECHNICAL_DESIGN.md) - Architecture and specifications
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Development roadmap
- [Quick Start Guide](docs/QUICK_START.md) - Getting started tutorial
- [Resume Template](docs/resume_template.md) - How to structure your resume
- [Job Template](docs/job_template.md) - How to format job descriptions

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Status

🔄 **In Development** - Phase 1: Core Foundation (v1.0.0)
