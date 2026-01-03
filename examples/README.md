# Examples

This directory contains example scripts demonstrating how to use the Resume Customizer MCP Server.

## Manual Testing

### Phase 6 Manual Test

`manual_test_phase6.py` - Demonstrates the complete Phase 6 workflow without the MCP server.

**Prerequisites:**
```bash
# Install the package in development mode
pip install -e .

# Or activate your virtual environment first
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows
```

**Usage:**
```bash
python3 examples/manual_test_phase6.py
```

**What it tests:**
1. Loading user profile from markdown
2. Loading job description from markdown
3. Analyzing match score between profile and job
4. Customizing resume based on match
5. Listing customizations from database
6. Error handling with helpful suggestions

**Expected output:**
- Successful workflow with match scores, customization details
- Database persistence verification
- Error messages with actionable suggestions
