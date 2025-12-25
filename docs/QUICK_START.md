# Resume Customizer MCP - Quick Start Guide

## 🎯 What This Tool Does

Automatically customizes your resume for specific job applications using AI. Just provide:
1. Your resume (as `resume.md`)
2. Job description (as `job.md`)
3. Chat with Claude to customize!

**Result:** Professional PDF/DOCX resume optimized for the specific job, with 87%+ match scores.

---

## 📋 For Users: How to Use

### Step 1: Create Your Base Resume

Copy `resume_template.md` and fill it with your information:

```bash
cp resume_template.md my_resume.md
# Edit my_resume.md with your details
```

**What to include:**
- ✅ Personal contact info
- ✅ Professional summary
- ✅ Work experience (3-7 achievements per role with metrics!)
- ✅ Skills (organized by category)
- ✅ Education & certifications
- ✅ Projects (optional but valuable)

**Pro tips:**
- Include quantifiable metrics in every achievement
- Use action verbs: "Built", "Reduced", "Increased", "Led"
- Mention specific technologies used
- Keep achievements 1-2 lines max

### Step 2: Create Job Description File

For each job you want to apply to:

```bash
cp job_template.md atlassian_data_engineer.md
# Paste the full job posting into the file
```

**What to include:**
- ✅ Job title and company
- ✅ Full job description (copy-paste everything!)
- ✅ Required and preferred qualifications
- ✅ Your personal notes about why you're interested

### Step 3: Talk to Claude

Open Claude Desktop and start a conversation:

```
You: Hi Claude! I need to customize my resume for a Senior Data Engineer 
     role at Atlassian. 
     
     My resume: ./my_resume.md
     Job description: ./atlassian_data_engineer.md
     
     Can you analyze how well I match and customize my resume?

Claude: I'll help you! Let me analyze your profile against the Atlassian 
        position.
        
[Claude uses MCP tools to load files, analyze match, customize, and generate PDFs]

Claude: ✅ Done! Your resume has been customized:
        
        📊 Match Score: 87%
        
        Strong matches:
        - Python, GCP, BigQuery ✅
        - 9 years experience (exceeds 7+ requirement) ✅
        - Healthcare data background ✅
        
        Generated files:
        📄 John_Doe_Resume_Atlassian_DataEngineer_2025-12-21.pdf
        📄 John_Doe_Resume_Atlassian_DataEngineer_2025-12-21.docx
```

### Step 4: Review and Submit

- Open the generated PDF
- Review customizations
- Ask Claude to make adjustments if needed
- Submit your application!

**Common requests:**
- "Make the summary more technical"
- "Emphasize my leadership experience"
- "Add more keywords about healthcare"
- "Make it fit on one page"

---

## 🛠️ For Developers: How to Build

### Prerequisites

- Python 3.10+
- Claude Desktop or MCP client
- Anthropic API key

### Installation

```bash
# Clone repo
git clone https://github.com/yourusername/resume-customizer-mcp
cd resume-customizer-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install NLP models
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Development Workflow

```bash
# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
black src/

# Start server (for testing)
python -m resume_customizer.server
```

### Project Structure

```
resume-customizer-mcp/
├── src/resume_customizer/
│   ├── server.py           # MCP server entry point
│   ├── mcp/                # MCP tools & handlers
│   ├── parsers/            # Markdown parsing
│   ├── core/               # Business logic
│   ├── generators/         # PDF/DOCX generation
│   └── storage/            # Database & files
├── templates/              # Resume templates
├── examples/               # Example resume & job files
└── tests/                  # Test suite
```

### Connect to Claude Desktop

Edit Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop.

### Testing MCP Tools

Use the MCP inspector or client:

```bash
# Install MCP client
npm install -g @modelcontextprotocol/inspector

# Test tools
mcp-inspector python -m resume_customizer.server

# Or use Claude directly
# Just start a conversation and Claude will discover the tools
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `TECHNICAL_DESIGN.md` | Complete technical architecture & implementation guide |
| `resume_customizer_prd.md` | Product requirements document |
| `input_requirements_summary.md` | What inputs are needed and why |
| `resume_template.md` | Template for user's resume |
| `job_template.md` | Template for job descriptions |
| This file | Quick start guide |

---

## 🔧 Implementation Phases

### Phase 1: Core (Week 1-2)
- [x] Project setup
- [ ] Markdown parsers
- [ ] Data models
- [ ] Basic MCP server

### Phase 2: Matching (Week 2-3)
- [ ] Skill matching algorithm
- [ ] Achievement ranking
- [ ] Match scoring

### Phase 3: AI Integration (Week 3-4)
- [ ] Claude API service
- [ ] Keyword extraction
- [ ] Summary generation

### Phase 4: Customization (Week 4-5)
- [ ] Resume customization engine
- [ ] Truthfulness validation

### Phase 5: Generation (Week 5-6)
- [ ] Template system
- [ ] PDF generator
- [ ] DOCX generator

### Phase 6: MCP Tools (Week 6-7)
- [ ] All 6 MCP tools
- [ ] Error handling

### Phase 7: Polish (Week 7-8)
- [ ] Testing
- [ ] Documentation
- [ ] Examples

---

## 🎯 Success Criteria

✅ Parse 95%+ valid markdown resumes  
✅ Match scores align with human judgment  
✅ End-to-end < 30 seconds  
✅ No fabricated information  
✅ ATS-friendly output  
✅ Users can customize without manual edits  

---

## 💡 Example Workflows

### Workflow 1: First Time User

```
1. Copy resume_template.md → my_resume.md
2. Fill in all sections with your info
3. Find job posting → create job.md
4. Chat with Claude: "Customize my resume for this job"
5. Get PDF/DOCX in 30 seconds
6. Apply!
```

### Workflow 2: Applying to Multiple Jobs

```
1. Keep one base resume.md (update occasionally)
2. For each job:
   - Create new job.md (e.g., company_role.md)
   - Ask Claude to customize for that job
   - Get customized resume in seconds
3. Track: "Claude, show me my customization history"
```

### Workflow 3: Iterative Refinement

```
User: Customize my resume for this Atlassian job
Claude: [Creates initial version]

User: Make it more technical and emphasize data pipelines
Claude: [Updates customization]

User: Perfect! But can you fit it on one page?
Claude: [Regenerates with length constraint]

User: Great! Generate final files
Claude: [Exports PDF + DOCX]
```

---

## 🐛 Troubleshooting

### "Claude can't find my files"
- Ensure file paths are correct (relative to where Claude is running)
- Use full paths if needed: `/Users/you/Documents/resume.md`

### "Match score seems wrong"
- Check that your resume.md has all required sections
- Ensure achievements include technologies and metrics
- Verify job.md has complete job description

### "PDF looks weird"
- Template rendering issue - try different template
- Check for special characters in your resume
- Verify all markdown formatting is correct

### "Missing required skills"
- Add those skills to your resume if you have them
- If you don't have them, Claude will note it in gap analysis
- Consider learning them or applying anyway with cover letter

---

## 📞 Support & Contribution

- **Documentation:** See `TECHNICAL_DESIGN.md`
- **Issues:** [GitHub Issues](https://github.com/yourusername/resume-customizer-mcp/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/resume-customizer-mcp/discussions)

---

## 🚀 Ready to Build!

For development: Start with `TECHNICAL_DESIGN.md`  
For usage: Use `resume_template.md` and `job_template.md`

**Let's help job seekers land their dream roles! 🎉**
