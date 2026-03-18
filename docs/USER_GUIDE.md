# Resume Customizer MCP Server - User Guide

**Version**: 1.0.0
**Last Updated**: January 5, 2026

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Creating Your Resume](#creating-your-resume)
5. [Creating Job Descriptions](#creating-job-descriptions)
6. [Using with Claude](#using-with-claude)
7. [Understanding Match Scores](#understanding-match-scores)
8. [Customization Options](#customization-options)
9. [Output Formats](#output-formats)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)
12. [Best Practices](#best-practices)

---

## Introduction

Resume Customizer MCP Server is an AI-powered tool that helps you create tailored resumes for specific job applications. It analyzes your profile against job requirements and generates optimized resumes that highlight your most relevant experience and skills.

### Key Features

- **Intelligent Matching**: Analyzes how well you match a job's requirements
- **Smart Customization**: Prioritizes your most relevant achievements and skills
- **AI-Powered**: Uses Claude to generate job-specific summaries
- **Multiple Templates**: Modern, Classic, and ATS-optimized designs
- **Multi-Format Output**: PDF and DOCX files
- **100% Truthful**: Never fabricates skills or experience

### How It Works

1. You provide your master resume in Markdown format
2. You provide a job description in Markdown format
3. The system analyzes the match and scores your fit
4. Claude helps customize your resume for that specific job
5. Professional documents are generated in your chosen format

---

## Installation

### Prerequisites

- **Python 3.11 or higher**
- **Claude Desktop** (for the best experience)
- **Anthropic API Key** (for AI features)

### Step-by-Step Installation

#### 1. Install Python

**macOS**:
```bash
brew install python@3.11
```

**Windows**:
Download from [python.org](https://www.python.org/downloads/)

**Linux**:
```bash
sudo apt install python3.11 python3.11-venv
```

#### 2. Clone the Repository

```bash
git clone <repository-url>
cd "resume customizer mcp server"
```

#### 3. Set Up Virtual Environment

**macOS/Linux**:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

#### 4. Install Dependencies

```bash
pip install -e .
```

This installs:
- MCP SDK
- Anthropic SDK (Claude API)
- WeasyPrint (PDF generation)
- python-docx (DOCX generation)
- spaCy (NLP)
- And other required packages

#### 5. Install spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

#### 6. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

To get an API key:
1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Go to API Keys
4. Create a new key

#### 7. Configure Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "resume_customizer": {
      "command": "python",
      "args": [
        "-m",
        "resume_customizer.server"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important**: Replace `"your-api-key-here"` with your actual API key.

#### 8. Restart Claude Desktop

Close and reopen Claude Desktop to load the MCP server.

#### 9. Verify Installation

In Claude Desktop, you should see a small hammer icon (🔨) indicating the MCP server is connected. Try asking Claude: "List available resume customizer tools"

---

## Getting Started

### Quick Start Workflow

1. **Prepare your master resume** (`resume.md`)
2. **Find a job you want to apply for** and create `job.md`
3. **Chat with Claude**: "Load my resume from resume.md"
4. **Load the job**: "Load the job description from job.md"
5. **Analyze the match**: "Analyze how well I match this job"
6. **Customize**: "Customize my resume for this job"
7. **Generate files**: "Generate PDF and DOCX files"

### File Organization

Create a workspace folder for your job applications:

```
job-applications/
├── resume.md                  # Your master resume
├── jobs/
│   ├── company-a-job.md       # Job description
│   ├── company-b-job.md
│   └── company-c-job.md
└── output/
    ├── company-a/
    │   ├── resume.pdf
    │   └── resume.docx
    └── company-b/
        ├── resume.pdf
        └── resume.docx
```

---

## Creating Your Resume

Your resume should be written in Markdown format following this structure:

### Basic Structure

```markdown
# Your Name

## Contact Information
- **Email**: your.email@example.com
- **Phone**: +1-555-123-4567
- **Location**: San Francisco, CA
- **LinkedIn**: linkedin.com/in/yourprofile
- **GitHub**: github.com/yourusername
- **Portfolio**: yourwebsite.com

## Professional Summary
A concise 2-3 sentence summary of your experience and expertise...

## Skills
- **Programming Languages**: Python, JavaScript, TypeScript, Java
- **Frameworks**: React, Node.js, Django, Flask
- **Tools**: Docker, Kubernetes, AWS, Git
- **Databases**: PostgreSQL, MongoDB, Redis

## Experience

### Senior Software Engineer | Company Name | 2020-01 - Present | San Francisco, CA
- Built and deployed microservices architecture serving 1M+ users, reducing latency by 40%
- Led team of 5 engineers in developing new features, resulting in 25% increase in user engagement
- Implemented CI/CD pipeline using GitHub Actions, reducing deployment time from 2 hours to 15 minutes

### Software Engineer | Previous Company | 2018-06 - 2019-12 | Remote
- Developed REST APIs using Python/Django handling 10K requests per second
- Optimized database queries reducing response time by 60%
- Mentored 3 junior developers in best practices and code review

## Education

### Bachelor of Science in Computer Science | MIT | 2018 | 3.8/4.0
Relevant coursework: Algorithms, Data Structures, Machine Learning, Distributed Systems

## Certifications
- AWS Certified Solutions Architect - Professional (2023)
- Kubernetes Administrator (CKA) (2022)
```

### Important Guidelines

1. **Use Metrics**: Include numbers, percentages, and concrete results
2. **Action Verbs**: Start achievements with strong verbs (Built, Led, Implemented, Optimized)
3. **Be Specific**: "Reduced latency by 40%" instead of "Improved performance"
4. **Technologies**: Mention specific technologies used in each achievement
5. **Dates**: Use YYYY-MM format or YYYY for dates
6. **Consistency**: Keep formatting consistent throughout

### Common Mistakes to Avoid

- ❌ Vague achievements: "Worked on backend systems"
- ✅ Specific achievements: "Built REST API serving 50K daily requests"

- ❌ No metrics: "Improved performance"
- ✅ With metrics: "Reduced API response time by 60% through query optimization"

- ❌ Listing duties: "Responsible for code reviews"
- ✅ Showing impact: "Established code review process, reducing bugs by 30%"

See [resume_template.md](resume_template.md) for a complete example.

---

## Creating Job Descriptions

Job descriptions should also be in Markdown format:

### Basic Structure

```markdown
# Job Title

## Company Information
**Company**: Company Name
**Location**: San Francisco, CA (Hybrid)
**Type**: Full-time
**Experience Level**: Senior
**Salary Range**: $150,000 - $200,000

## Job Description
We're looking for an experienced Senior Software Engineer to join our Platform team...

## Responsibilities
- Design and build scalable microservices architecture
- Lead technical discussions and architectural decisions
- Mentor junior engineers and conduct code reviews
- Collaborate with product managers on feature development

## Required Qualifications
- 5+ years of software engineering experience
- Strong proficiency in Python and JavaScript
- Experience with cloud platforms (AWS, GCP, or Azure)
- Deep understanding of system design and architecture

## Preferred Qualifications
- Experience with Kubernetes and container orchestration
- Familiarity with React or similar frontend frameworks
- Background in fintech or payments industry
- Open source contributions

## Technical Requirements
- **Languages**: Python, JavaScript/TypeScript
- **Frameworks**: Django, FastAPI, React
- **Infrastructure**: AWS, Docker, Kubernetes
- **Databases**: PostgreSQL, Redis
```

### Tips for Job Descriptions

1. **Copy-Paste from Posting**: Start with the actual job posting
2. **Highlight Keywords**: The system will extract them automatically
3. **Include Requirements**: Both required and preferred qualifications
4. **Technical Details**: List specific technologies mentioned

See [job_template.md](job_template.md) for a complete example.

---

## Using with Claude

### Basic Commands

Once your files are ready, use these commands with Claude:

#### 1. Load Your Resume
```
Load my resume from /path/to/resume.md
```

#### 2. Load Job Description
```
Load the job description from /path/to/job.md
```

#### 3. Analyze Match
```
Analyze how well I match this job
```

Claude will return:
- Overall match score (0-100)
- Skills breakdown (matched, missing)
- Experience level match
- Suggestions for improvement

#### 4. Customize Resume
```
Customize my resume for this job using these preferences:
- Template: modern
- Max 3 achievements per role
- Include summary
```

#### 5. Generate Files
```
Generate PDF and DOCX files in the output folder
```

### Example Conversation

```
You: Load my resume from ~/Documents/resume.md

Claude: I've loaded your resume successfully! Here's a summary:
- Name: John Doe
- Email: john@example.com
- Experience: 3 roles spanning 6 years
- Skills: 24 technical skills across 4 categories
- Education: BS Computer Science from MIT

You: Load job description from ~/Documents/jobs/acme-senior-engineer.md

Claude: Job description loaded! Position: Senior Software Engineer at Acme Corp

You: Analyze the match

Claude: Here's your match analysis:

Overall Score: 87/100 (Excellent match!)

Skills Match: 92/100
✅ Matched: Python, JavaScript, React, Docker, AWS (15 total)
❌ Missing: Kubernetes (required), Terraform (preferred)

Experience Level: 85/100
- You have 6 years, role requires 5+ years ✅
- Senior title matches ✅

Recommendations:
1. Highlight your Docker experience (relates to Kubernetes)
2. Emphasize your AWS infrastructure work
3. Mention any container orchestration experience

You: Customize my resume for this job with modern template

Claude: I've customized your resume! Changes made:
- Reordered 12 achievements by relevance
- Prioritized Python, React, and AWS skills
- Generated custom summary emphasizing infrastructure experience
- Selected top 3 achievements per role

You: Generate PDF and DOCX in ~/Documents/output/acme

Claude: Files generated successfully!
📄 ~/Documents/output/acme/John_Doe_Resume_Acme_Corp.pdf
📄 ~/Documents/output/acme/John_Doe_Resume_Acme_Corp.docx
```

---

## Understanding Match Scores

### Overall Score (0-100)

- **90-100**: Excellent match - You exceed requirements
- **80-89**: Great match - Strong candidate
- **70-79**: Good match - Qualified but may need to highlight relevant experience
- **60-69**: Fair match - Some gaps to address
- **Below 60**: Weak match - Significant gaps

### Score Components

The overall score is calculated from:

1. **Technical Skills (40%)**: Match between your skills and job requirements
2. **Experience Level (25%)**: Years of experience vs. required
3. **Domain Knowledge (20%)**: Industry/domain-specific expertise
4. **Keywords (15%)**: Coverage of important job posting terms

### What the Scores Mean

#### Technical Skills Score

- **95-100**: You have all required skills + most preferred
- **85-94**: You have all required skills
- **70-84**: Missing some required skills
- **Below 70**: Missing several critical skills

#### Experience Level Score

- **100**: Your experience exceeds requirements
- **85-99**: You meet the experience requirement
- **70-84**: Slightly under the required years
- **Below 70**: Significantly under-experienced for the role

---

## Customization Options

### Template Choices

#### Modern Template (Default)
- Clean, contemporary design
- Two-column layout
- Accent colors for headers
- Best for: Tech companies, startups, creative roles

#### Classic Template
- Traditional single-column layout
- Conservative styling
- Professional serif fonts
- Best for: Corporate, finance, legal, academia

#### ATS Optimized Template
- Simple, machine-readable format
- No graphics or complex formatting
- Maximum compatibility with ATS systems
- Best for: Large companies with automated screening

### Customization Preferences

```
Customize my resume with these options:
- Template: modern
- Achievements per role: 4
- Max skills: 20
- Include summary: yes
```

Available options:

- **template**: `modern`, `classic`, `ats_optimized`
- **achievements_per_role**: 1-10 (default: 3)
- **max_skills**: Number of skills to show (default: all relevant)
- **include_summary**: `yes` or `no` (default: yes)

---

## Output Formats

### PDF Format

- **Professional quality** suitable for printing and digital submission
- **Universal compatibility** - opens on any device
- **Fixed layout** - looks the same everywhere
- **Print-ready** with proper margins and spacing

**File size**: Typically 50-150 KB
**Compatibility**: All PDF readers

### DOCX Format

- **Editable** - make last-minute changes
- **ATS-friendly** - easily parsed by applicant tracking systems
- **Flexible** - adjust formatting if needed
- **Widely accepted** for online applications

**File size**: Typically 20-50 KB
**Compatibility**: Microsoft Word 2007+, Google Docs, LibreOffice

### File Naming Convention

Generated files follow this pattern:
```
{Your_Name}_Resume_{Company_Name}.{ext}
```

Example:
```
John_Doe_Resume_Acme_Corp.pdf
John_Doe_Resume_Acme_Corp.docx
```

---

## Troubleshooting

### Installation Issues

#### "Python not found"
**Solution**: Install Python 3.11 or higher
```bash
python3 --version  # Should show 3.11 or higher
```

#### "Module not found" errors
**Solution**: Make sure virtual environment is activated and dependencies installed
```bash
source venv/bin/activate  # Activate venv
pip install -e .          # Reinstall dependencies
```

#### spaCy model not found
**Solution**: Install the spaCy language model
```bash
python -m spacy download en_core_web_sm
```

### MCP Server Issues

#### MCP server not connecting in Claude Desktop
**Solutions**:
1. Check Claude Desktop config file location and syntax
2. Verify the `command` path points to correct Python
3. Ensure API key is set correctly in `env`
4. Restart Claude Desktop after config changes
5. Check Claude Desktop logs (Help → View Logs)

#### "API key not found" error
**Solution**: Set `ANTHROPIC_API_KEY` in both:
1. `.env` file in project root
2. Claude Desktop config under `env`

### File Parsing Issues

#### Resume not parsing correctly
**Common causes**:
- Missing required sections (Name, Contact, Experience)
- Incorrect Markdown formatting
- Invalid date formats

**Solution**: Compare with `docs/resume_template.md` and ensure:
- Headers use `#`, `##`, `###` correctly
- Dates are in `YYYY-MM` or `YYYY` format
- Required fields are present

#### Job description parsing fails
**Common causes**:
- Missing company information
- No requirements section
- Malformed Markdown

**Solution**: Check `docs/job_template.md` for correct structure

### Generation Issues

#### PDF generation fails
**Possible causes**:
- WeasyPrint dependencies missing (rare)
- Invalid HTML in template
- Corrupted customized resume data

**Solution**:
```bash
# Reinstall WeasyPrint
pip install --upgrade --force-reinstall weasyprint
```

#### DOCX has formatting issues
**Solution**: DOCX generation is basic by design. For advanced formatting:
1. Generate DOCX
2. Open in Microsoft Word or Google Docs
3. Apply additional formatting as needed

### Performance Issues

#### Slow response times
**Causes**:
- First API call to Claude (cold start)
- Complex resumes with many achievements
- Network latency

**Solutions**:
- Responses are cached - subsequent requests faster
- Consider reducing achievements per role
- Check internet connection

### Data Issues

#### Match score seems wrong
**Check**:
- Are skills listed correctly in resume?
- Did you include all relevant technologies?
- Check job description has requirements section

#### Achievements not appearing
**Possible causes**:
- Achievements have low relevance scores
- `achievements_per_role` set too low
- Achievements lack metrics or keywords

**Solution**: Review achievements to include:
- Relevant technologies
- Measurable impact
- Keywords from job posting

---

## FAQ

### General Questions

**Q: Do I need an Anthropic API key?**
A: Yes, for AI-powered features (summary generation, keyword extraction). The system can work without it using spaCy fallback, but results are better with Claude.

**Q: How much does it cost per customization?**
A: Approximately $0.02-0.05 per customization with prompt caching. Caching saves ~80% on repeated operations.

**Q: Is my data sent to Anthropic?**
A: Yes, but only the specific text being analyzed (achievements, job descriptions). Your full resume is not sent. All data is processed according to Anthropic's privacy policy.

**Q: Can I use this offline?**
A: Partially. File parsing and matching work offline. AI features (summaries, keyword extraction) require internet connection.

### Resume Questions

**Q: Can I have multiple resumes?**
A: Yes! Create separate `.md` files for different career tracks (e.g., `resume-backend.md`, `resume-frontend.md`).

**Q: How do I update my resume?**
A: Edit your `resume.md` file and reload it in Claude.

**Q: Should I include everything in my master resume?**
A: Yes! Include all experience, skills, and achievements. The system will select the most relevant ones for each job.

**Q: How many years of experience should I include?**
A: Generally 10-15 years maximum, unless earlier roles are highly relevant.

### Customization Questions

**Q: Will the system add skills I don't have?**
A: No! The system is designed to be 100% truthful. It only reorders and emphasizes skills/experience you actually have.

**Q: Can I review changes before generating files?**
A: Yes! Ask Claude "Show me what changes were made" after customization.

**Q: How do I undo customization?**
A: Just reload your original resume and start over. Previous customizations don't affect your source file.

**Q: Can I manually edit the customized version?**
A: Generate the DOCX file and edit it in Word/Google Docs for final tweaks.

### Technical Questions

**Q: What Markdown features are supported?**
A: Standard Markdown: headers, lists, bold, italic, links. Complex tables and images are not supported.

**Q: Can I use HTML in my resume?**
A: No, stick to Markdown. HTML will be treated as text.

**Q: Does it work with ATS (Applicant Tracking Systems)?**
A: Yes! Use the `ats_optimized` template for best ATS compatibility. DOCX format is also ATS-friendly.

**Q: Can I customize the templates?**
A: Currently, templates are pre-defined. Future versions may support custom templates.

---

## Best Practices

### Resume Writing

1. **Be Specific**: "Reduced API latency by 40%" > "Improved performance"
2. **Use Metrics**: Numbers make achievements concrete and verifiable
3. **Action Verbs**: Led, Built, Implemented, Optimized, Designed
4. **Technologies**: Mention specific tools/languages used
5. **Impact**: Focus on outcomes, not just activities

### Job Application Strategy

1. **Customize for Each Job**: Don't send the same resume to every company
2. **Target Keywords**: Note the job's key terms and ensure they appear in your resume
3. **Check Match Score**: Aim for 80+ before applying
4. **Address Gaps**: If missing required skills, highlight related experience
5. **Quality Over Quantity**: Better to send fewer, well-targeted applications

### Using the Tool Effectively

1. **Maintain Master Resume**: Keep one comprehensive resume with everything
2. **Save Job Descriptions**: Archive jobs you apply to for future reference
3. **Track Applications**: Note which customization was used for each application
4. **Iterate**: If not getting interviews, try different customization strategies
5. **A/B Test**: Try different templates/preferences and see what works

### Privacy & Security

1. **Protect API Keys**: Never commit `.env` files to version control
2. **Review Output**: Always review generated resumes before sending
3. **Personal Info**: Be cautious about including sensitive information
4. **Local Storage**: Your resume files stay on your computer
5. **Session Data**: Customization history is stored locally only

---

## Getting Help

### Documentation

- **User Guide** (this document): Complete usage instructions
- **[Developer Guide](DEVELOPER_GUIDE.md)**: For contributors and advanced users
- **[API Reference](API_REFERENCE.md)**: MCP tools documentation
- **[Technical Design](TECHNICAL_DESIGN.md)**: System architecture

### Support

- **Issues**: Report bugs on GitHub Issues
- **Questions**: Use GitHub Discussions
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

### Useful Commands

```bash
# Run tests
pytest

# Check code quality
ruff check src/
mypy src/

# Generate coverage report
pytest --cov=src/resume_customizer --cov-report=html
```

---

## What's Next?

After mastering the basics:

1. **Experiment with Templates**: Try all three templates to see which gets best results
2. **Optimize Preferences**: Adjust achievements count and skills based on job level
3. **Track Results**: Note which customizations lead to interviews
4. **Contribute**: Found a bug? Have a feature idea? Contribute to the project!

---

**Happy job hunting! 🎉**

For more information, visit the project repository or check out other documentation files.
