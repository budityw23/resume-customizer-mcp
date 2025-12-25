# Technical Design Document: Resume Customizer MCP Server

## Document Information
- **Product**: Resume Customizer MCP Server
- **Version**: 1.0
- **Target**: Claude Code Development
- **Date**: December 21, 2025
- **Architecture**: Model Context Protocol (MCP) Server

---

## 1. Executive Summary

An MCP server that enables Claude to customize resumes by analyzing two markdown documents:
1. **User Profile** (resume.md) - Complete professional profile
2. **Job Description** (job.md) - Target job requirements

Users interact naturally with Claude, which uses MCP tools to load, analyze, customize, and generate professional resume outputs.

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    User Interface                         │
│           (Claude.ai / Claude Desktop / API)              │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ MCP Protocol (stdio/SSE)
                         │
┌────────────────────────▼─────────────────────────────────┐
│              MCP Server: resume_customizer                │
│                                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │              MCP Tools Layer                      │   │
│  │  • load_user_profile                             │   │
│  │  • load_job_description                          │   │
│  │  • analyze_match                                 │   │
│  │  • customize_resume                              │   │
│  │  • generate_resume_files                         │   │
│  │  • list_customizations                           │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                                 │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │           Core Processing Engine                    │ │
│  │  • Markdown Parser                                  │ │
│  │  • Job Analyzer (AI-powered)                       │ │
│  │  • Matching Engine                                  │ │
│  │  • Customization Engine                            │ │
│  │  • Template Renderer                               │ │
│  └──────────────────────────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │              AI Services                            │ │
│  │  • Anthropic Claude API (keyword extraction)       │ │
│  │  • NLP Processing (spaCy)                          │ │
│  │  • Similarity Matching (scikit-learn)              │ │
│  └──────────────────────────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │           Document Generation                       │ │
│  │  • DOCX Generator (python-docx)                    │ │
│  │  • PDF Generator (WeasyPrint)                      │ │
│  │  • Template Engine (Jinja2)                        │ │
│  └──────────────────────────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼─────────────────────────────┐ │
│  │              Storage Layer                          │ │
│  │  • SQLite (session state, history)                 │ │
│  │  • File System (input .md, output files)           │ │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User → Claude → MCP Server → Processing → Output

Example Flow:
1. User: "Customize my resume for this job"
2. Claude calls: load_user_profile("resume.md")
3. Claude calls: load_job_description("job.md")
4. Claude calls: analyze_match()
   ├─→ Parse both markdown files
   ├─→ Extract keywords via Claude API
   ├─→ Calculate match scores
   └─→ Return analysis
5. Claude calls: customize_resume(preferences)
   ├─→ Rank achievements by relevance
   ├─→ Generate optimized summary
   ├─→ Reorder skills
   └─→ Return customized structure
6. Claude calls: generate_resume_files(["pdf", "docx"])
   ├─→ Apply template
   ├─→ Generate PDF
   ├─→ Generate DOCX
   └─→ Return file paths
7. Claude: "✓ Done! Here are your files..."
```

---

## 3. Input Format: Markdown Documents

### 3.1 User Profile (resume.md)

**Structure:**
```markdown
# [Your Name]

## Contact Information
- **Email:** your.email@example.com
- **Phone:** +1-555-123-4567
- **Location:** San Francisco, CA, USA
- **LinkedIn:** linkedin.com/in/yourname
- **GitHub:** github.com/yourname
- **Portfolio:** yourportfolio.com

## Professional Summary
[2-4 sentences describing your experience, specialization, and key achievements]

## Work Experience

### [Job Title] at [Company Name]
**[Start Date] - [End Date or "Present"]** | [Location] | [Remote/Hybrid/Onsite]

[Brief role description - 1-2 sentences]

**Key Achievements:**
- [Achievement with quantifiable impact and technologies used]
- [Achievement with quantifiable impact and technologies used]
- [Achievement with quantifiable impact and technologies used]

**Technologies:** Python, AWS, PostgreSQL, Docker

### [Previous Job Title] at [Previous Company]
**[Start Date] - [End Date]** | [Location]

**Key Achievements:**
- [Achievement]
- [Achievement]

**Technologies:** [Tech stack]

## Skills

### Programming Languages
Python (Expert, 8 years), JavaScript (Advanced, 6 years), Java (Intermediate, 3 years)

### Frameworks & Libraries
Django, React, Node.js, FastAPI, Spring Boot

### Cloud & DevOps
AWS (EC2, S3, Lambda, RDS), Docker, Kubernetes, Terraform, CI/CD

### Databases
PostgreSQL, MongoDB, Redis, Elasticsearch

### Domain Expertise
Healthcare Interoperability, Fintech, Data Engineering, E-commerce

### Soft Skills
Technical Leadership, Mentoring, Agile/Scrum, Cross-functional Collaboration

## Education

### [Degree Name]
**[Institution]** | [Graduation Date]  
GPA: [X.X/4.0] | [Honors if any]

Relevant Coursework: [Course 1], [Course 2], [Course 3]

## Certifications
- **[Certification Name]** - [Issuer] ([Date])
- **[Certification Name]** - [Issuer] ([Date])

## Projects

### [Project Name]
**[Dates]** | [Your Role]

[Brief description of project and your contribution]

**Technologies:** [Tech stack]  
**Impact:** [Quantifiable results]  
**Links:** [GitHub/Demo URL]

## Publications
- [Author names]. "[Title]." [Venue], [Date]. [DOI/URL]

## Awards & Honors
- **[Award Name]** - [Issuer] ([Date])

## Languages
- English (Native)
- Spanish (Professional Working)
- Mandarin (Elementary)

---

## Preferences

### Resume Customization
- **Length:** One page preferred, two if necessary
- **Achievements per role:** 4-5
- **Template:** Modern

### Target Roles
- Senior Software Engineer
- Staff Engineer
- Data Engineer

### Exclude
- **Old Skills:** PHP 5, jQuery
- **Companies:** [Confidential Client under NDA]
```

### 3.2 Job Description (job.md)

**Structure:**
```markdown
# [Job Title] at [Company Name]

## Job Details
- **Company:** [Company Name]
- **Location:** [City, Country / Remote]
- **Job Type:** Full-time / Remote / Hybrid
- **Posted:** [Date]
- **Apply URL:** [URL]

## Job Description

[Full job description text - paste everything from the job posting]

### About the Company
[Company description if available]

### About the Role
[Role description]

### Responsibilities
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

### Required Qualifications
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

### Preferred Qualifications
- [Preference 1]
- [Preference 2]

### Technical Requirements
- [Technical skill 1]
- [Technical skill 2]

### Nice to Have
- [Nice to have 1]
- [Nice to have 2]

### Benefits
- [Benefit 1]
- [Benefit 2]

---

## Notes
[Any personal notes about why you're interested, who referred you, etc.]
```

---

## 4. MCP Server Implementation

### 4.1 Server Configuration

**File:** `mcp_server_config.json`
```json
{
  "name": "resume_customizer",
  "version": "1.0.0",
  "description": "AI-powered resume customizer with intelligent job matching",
  "transport": "stdio",
  "tools": [
    "load_user_profile",
    "load_job_description",
    "analyze_match",
    "customize_resume",
    "generate_resume_files",
    "list_customizations"
  ],
  "prompts": [],
  "resources": []
}
```

### 4.2 MCP Tools Specification

#### Tool 1: load_user_profile

**Purpose:** Load and parse user's resume markdown file

```python
{
    "name": "load_user_profile",
    "description": """
        Load user's professional profile from a markdown file.
        This parses the resume.md file containing personal information,
        work experience, skills, education, certifications, and projects.
        
        Returns parsed profile data with all sections extracted.
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to resume markdown file (e.g., './resume.md')"
            }
        },
        "required": ["file_path"]
    }
}
```

**Return Schema:**
```json
{
  "profile_id": "uuid-string",
  "loaded_at": "2025-12-21T10:30:00Z",
  "file_path": "./resume.md",
  "data": {
    "name": "John Doe",
    "contact": {
      "email": "john@example.com",
      "phone": "+1-555-123-4567",
      "location": "San Francisco, CA",
      "linkedin": "linkedin.com/in/johndoe",
      "github": "github.com/johndoe"
    },
    "summary": "...",
    "experience": [...],
    "skills": {...},
    "education": [...],
    "certifications": [...],
    "projects": [...],
    "preferences": {...}
  },
  "validation": {
    "is_valid": true,
    "warnings": ["No quantifiable metrics in 2 achievements"],
    "errors": []
  }
}
```

#### Tool 2: load_job_description

**Purpose:** Load and parse job description markdown file

```python
{
    "name": "load_job_description",
    "description": """
        Load job description from a markdown file.
        This parses the job.md file and extracts job requirements,
        qualifications, responsibilities, and keywords using AI.
        
        Returns structured job data with extracted requirements.
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to job description markdown file"
            },
            "use_ai_extraction": {
                "type": "boolean",
                "description": "Use Claude API for smart keyword extraction",
                "default": true
            }
        },
        "required": ["file_path"]
    }
}
```

**Return Schema:**
```json
{
  "job_id": "uuid-string",
  "loaded_at": "2025-12-21T10:31:00Z",
  "file_path": "./job.md",
  "data": {
    "title": "Senior Data Engineer",
    "company": "Atlassian",
    "location": "Remote",
    "job_type": "Full-time",
    "url": "https://...",
    "requirements": {
      "required_skills": ["Python", "SQL", "AWS", "Spark"],
      "preferred_skills": ["Kubernetes", "Terraform"],
      "years_experience": 7,
      "education": "Bachelor's in CS or equivalent"
    },
    "responsibilities": [...],
    "keywords": {
      "technical": ["data pipeline", "ETL", "distributed systems"],
      "domain": ["healthcare", "HIPAA", "data governance"],
      "soft_skills": ["leadership", "collaboration"]
    },
    "raw_text": "..."
  }
}
```

#### Tool 3: analyze_match

**Purpose:** Calculate match score between profile and job

```python
{
    "name": "analyze_match",
    "description": """
        Analyze how well the user's profile matches the job requirements.
        Calculates overall match score and provides detailed breakdown
        by category. Identifies gaps and suggests improvements.
        
        Returns comprehensive match analysis.
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "profile_id": {
                "type": "string",
                "description": "ID from load_user_profile result"
            },
            "job_id": {
                "type": "string",
                "description": "ID from load_job_description result"
            }
        },
        "required": ["profile_id", "job_id"]
    }
}
```

**Return Schema:**
```json
{
  "match_id": "uuid-string",
  "analyzed_at": "2025-12-21T10:32:00Z",
  "overall_score": 87,
  "breakdown": {
    "technical_skills": {
      "score": 92,
      "matched": ["Python", "SQL", "AWS", "Docker"],
      "missing_required": ["Kubernetes"],
      "missing_preferred": ["Terraform"]
    },
    "experience_level": {
      "score": 95,
      "user_years": 9,
      "required_years": 7
    },
    "domain_knowledge": {
      "score": 75,
      "matched_domains": ["Healthcare", "Data Engineering"],
      "missing_domains": []
    },
    "keyword_coverage": {
      "score": 82,
      "matched_keywords": 45,
      "total_keywords": 55
    }
  },
  "gaps": {
    "critical": ["Kubernetes (required)"],
    "recommended": ["Terraform", "Airflow experience"]
  },
  "suggestions": [
    "Emphasize your GCP experience (similar to AWS)",
    "Highlight Docker work (shows container knowledge)",
    "Mention willingness to learn Kubernetes quickly"
  ],
  "achievement_rankings": [
    {
      "achievement": "Reduced FHIR processing from 11h to 23min...",
      "relevance_score": 95,
      "matched_keywords": ["optimization", "data processing", "pipeline"]
    },
    {
      "achievement": "Built federated FHIR servers...",
      "relevance_score": 88,
      "matched_keywords": ["distributed systems", "API", "scalability"]
    }
  ]
}
```

#### Tool 4: customize_resume

**Purpose:** Generate customized resume based on match analysis

```python
{
    "name": "customize_resume",
    "description": """
        Customize the resume for the specific job by:
        - Reordering achievements by relevance
        - Generating job-specific summary
        - Optimizing skills section
        - Maintaining truthfulness (no fabrication)
        
        Returns customized resume structure.
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "match_id": {
                "type": "string",
                "description": "ID from analyze_match result"
            },
            "preferences": {
                "type": "object",
                "properties": {
                    "summary_style": {
                        "type": "string",
                        "enum": ["technical", "results", "balanced"],
                        "default": "balanced"
                    },
                    "achievements_per_role": {
                        "type": "integer",
                        "minimum": 2,
                        "maximum": 7,
                        "default": 4
                    },
                    "emphasize": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to emphasize (e.g., ['healthcare', 'leadership'])"
                    },
                    "template": {
                        "type": "string",
                        "enum": ["modern", "classic", "ats_optimized"],
                        "default": "modern"
                    }
                }
            }
        },
        "required": ["match_id"]
    }
}
```

**Return Schema:**
```json
{
  "customization_id": "uuid-string",
  "customized_at": "2025-12-21T10:33:00Z",
  "based_on_match": "match-uuid",
  "customized_resume": {
    "personal": {...},
    "summary": "Customized 2-3 sentence summary with job keywords...",
    "experience": [
      {
        "company": "...",
        "role": "...",
        "achievements": [
          {
            "text": "...",
            "rank": 1,
            "relevance_score": 95
          }
        ]
      }
    ],
    "skills": {
      "reordered": true,
      "displayed": ["Python", "AWS", "SQL", "Docker", "GCP"]
    },
    "education": [...],
    "certifications": [...]
  },
  "changes_made": {
    "achievements_reordered": 12,
    "summary_regenerated": true,
    "skills_reordered": true,
    "keywords_added": ["distributed systems", "data governance"]
  },
  "metadata": {
    "job_title": "Senior Data Engineer",
    "company": "Atlassian",
    "match_score": 87
  }
}
```

#### Tool 5: generate_resume_files

**Purpose:** Export customized resume to PDF/DOCX files

```python
{
    "name": "generate_resume_files",
    "description": """
        Generate PDF and/or DOCX files from customized resume.
        Applies professional template and exports to specified formats.
        
        Returns file paths for generated documents.
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "customization_id": {
                "type": "string",
                "description": "ID from customize_resume result"
            },
            "formats": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["pdf", "docx"]
                },
                "default": ["pdf", "docx"]
            },
            "output_directory": {
                "type": "string",
                "default": "./output"
            },
            "filename_pattern": {
                "type": "string",
                "description": "Pattern: {name}_{company}_{title}_{date}.{ext}",
                "default": "{name}_Resume_{company}_{title}_{date}"
            }
        },
        "required": ["customization_id"]
    }
}
```

**Return Schema:**
```json
{
  "generated_at": "2025-12-21T10:34:00Z",
  "files": [
    {
      "format": "pdf",
      "path": "./output/John_Doe_Resume_Atlassian_DataEngineer_2025-12-21.pdf",
      "size_bytes": 245678,
      "pages": 1
    },
    {
      "format": "docx",
      "path": "./output/John_Doe_Resume_Atlassian_DataEngineer_2025-12-21.docx",
      "size_bytes": 123456,
      "pages": 1
    }
  ],
  "template_used": "modern",
  "success": true
}
```

#### Tool 6: list_customizations

**Purpose:** List all past customizations

```python
{
    "name": "list_customizations",
    "description": """
        List all resume customizations with filter options.
        Shows history of all customizations made.
    """,
    "inputSchema": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "default": 10,
                "maximum": 50
            },
            "sort_by": {
                "type": "string",
                "enum": ["date", "match_score", "company"],
                "default": "date"
            },
            "filter_company": {
                "type": "string",
                "description": "Filter by company name"
            }
        }
    }
}
```

**Return Schema:**
```json
{
  "total_customizations": 23,
  "returned": 10,
  "customizations": [
    {
      "customization_id": "uuid-1",
      "date": "2025-12-21T10:33:00Z",
      "job_title": "Senior Data Engineer",
      "company": "Atlassian",
      "match_score": 87,
      "files_generated": ["pdf", "docx"],
      "status": "completed"
    },
    {
      "customization_id": "uuid-2",
      "date": "2025-12-20T15:20:00Z",
      "job_title": "Staff Engineer",
      "company": "Google",
      "match_score": 82,
      "files_generated": ["pdf"],
      "status": "completed"
    }
  ]
}
```

---

## 5. Project Structure

```
resume-customizer-mcp/
├── pyproject.toml                 # Project dependencies
├── README.md                      # Setup instructions
├── .env.example                   # Environment variables template
│
├── src/
│   └── resume_customizer/
│       ├── __init__.py
│       │
│       ├── server.py              # MCP server entry point
│       ├── config.py              # Configuration management
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── tools.py           # MCP tool definitions
│       │   └── handlers.py        # Tool implementation handlers
│       │
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── markdown_parser.py # Parse resume.md & job.md
│       │   └── validator.py       # Input validation
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py          # Data models (Profile, Job, etc.)
│       │   ├── matcher.py         # Match scoring engine
│       │   ├── customizer.py      # Customization logic
│       │   └── ai_service.py      # Claude API integration
│       │
│       ├── generators/
│       │   ├── __init__.py
│       │   ├── docx_generator.py  # DOCX creation
│       │   ├── pdf_generator.py   # PDF creation
│       │   └── template_engine.py # Jinja2 templating
│       │
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py        # SQLite operations
│       │   └── file_manager.py    # File I/O operations
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logger.py          # Logging setup
│           └── helpers.py         # Utility functions
│
├── templates/
│   ├── modern.html                # Modern template
│   ├── classic.html               # Classic template
│   ├── ats_optimized.html         # ATS-friendly template
│   └── styles/
│       ├── modern.css
│       ├── classic.css
│       └── ats.css
│
├── examples/
│   ├── resume.md                  # Example user profile
│   ├── job.md                     # Example job description
│   └── output/                    # Example outputs
│
├── tests/
│   ├── __init__.py
│   ├── test_parsers.py
│   ├── test_matcher.py
│   ├── test_customizer.py
│   └── test_generators.py
│
└── docs/
    ├── USER_GUIDE.md              # User documentation
    ├── API_REFERENCE.md           # MCP tools reference
    └── DEVELOPER_GUIDE.md         # Development guide
```

---

## 6. Core Data Models

### 6.1 Profile Model

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date

@dataclass
class ContactInfo:
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

@dataclass
class Achievement:
    text: str
    keywords: List[str] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)
    impact_metrics: Optional[str] = None
    relevance_score: float = 0.0  # Set during matching

@dataclass
class Experience:
    company: str
    role: str
    start_date: str  # "YYYY-MM" or "Month YYYY"
    end_date: str    # "YYYY-MM" or "Present"
    location: str
    employment_type: str  # "Full-time", "Contract", etc.
    description: Optional[str] = None
    achievements: List[Achievement] = field(default_factory=list)
    technologies: List[str] = field(default_factory=list)

@dataclass
class Skill:
    name: str
    proficiency: Optional[str] = None  # "Expert", "Advanced", etc.
    years: Optional[int] = None

@dataclass
class Education:
    degree: str
    institution: str
    graduation_date: str
    gpa: Optional[str] = None
    honors: Optional[str] = None
    coursework: List[str] = field(default_factory=list)

@dataclass
class Certification:
    name: str
    issuer: str
    issue_date: str
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None

@dataclass
class Project:
    name: str
    description: str
    role: str
    dates: str
    technologies: List[str]
    achievements: List[str]
    links: Dict[str, str] = field(default_factory=dict)

@dataclass
class UserProfile:
    profile_id: str
    name: str
    contact: ContactInfo
    summary: str
    experience: List[Experience]
    skills: Dict[str, List[Skill]]  # Category -> Skills
    education: List[Education]
    certifications: List[Certification] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    preferences: Dict = field(default_factory=dict)
    loaded_from: str = ""
    loaded_at: str = ""
```

### 6.2 Job Model

```python
@dataclass
class JobRequirements:
    required_skills: List[str]
    preferred_skills: List[str]
    years_experience: Optional[int]
    education: Optional[str]

@dataclass
class JobKeywords:
    technical: List[str]
    domain: List[str]
    soft_skills: List[str]

@dataclass
class JobDescription:
    job_id: str
    title: str
    company: str
    location: str
    job_type: str
    url: Optional[str]
    requirements: JobRequirements
    responsibilities: List[str]
    keywords: JobKeywords
    raw_text: str
    loaded_from: str
    loaded_at: str
```

### 6.3 Match Result Model

```python
@dataclass
class SkillMatch:
    score: float
    matched: List[str]
    missing_required: List[str]
    missing_preferred: List[str]

@dataclass
class MatchBreakdown:
    technical_skills: SkillMatch
    experience_level: Dict[str, any]
    domain_knowledge: Dict[str, any]
    keyword_coverage: Dict[str, any]

@dataclass
class MatchResult:
    match_id: str
    profile_id: str
    job_id: str
    overall_score: float
    breakdown: MatchBreakdown
    gaps: Dict[str, List[str]]
    suggestions: List[str]
    achievement_rankings: List[Dict]
    analyzed_at: str
```

---

## 7. Key Algorithms

### 7.1 Match Scoring Algorithm

```python
def calculate_match_score(profile: UserProfile, job: JobDescription) -> MatchResult:
    """
    Calculate overall match score using weighted components
    
    Weights:
    - Technical Skills: 40%
    - Experience Level: 25%
    - Domain Knowledge: 20%
    - Keyword Coverage: 15%
    """
    
    # 1. Technical Skills Match (40%)
    tech_score = calculate_technical_match(
        profile_skills=extract_all_skills(profile),
        required_skills=job.requirements.required_skills,
        preferred_skills=job.requirements.preferred_skills
    )
    
    # 2. Experience Level Match (25%)
    exp_score = calculate_experience_match(
        profile_years=calculate_years_experience(profile),
        required_years=job.requirements.years_experience
    )
    
    # 3. Domain Knowledge Match (20%)
    domain_score = calculate_domain_match(
        profile_domains=extract_domains(profile),
        job_keywords=job.keywords.domain
    )
    
    # 4. Keyword Coverage (15%)
    keyword_score = calculate_keyword_coverage(
        profile_text=profile_to_text(profile),
        job_keywords=flatten_keywords(job.keywords)
    )
    
    # Calculate weighted overall score
    overall = (
        tech_score * 0.40 +
        exp_score * 0.25 +
        domain_score * 0.20 +
        keyword_score * 0.15
    )
    
    return MatchResult(...)
```

### 7.2 Achievement Ranking Algorithm

```python
def rank_achievements(
    achievements: List[Achievement],
    job: JobDescription
) -> List[Tuple[Achievement, float]]:
    """
    Rank achievements by relevance to job
    
    Scoring factors:
    - Keyword overlap: 40%
    - Technology match: 30%
    - Impact metrics: 20%
    - Recency: 10%
    """
    
    ranked = []
    
    for achievement in achievements:
        # Extract keywords from achievement text
        ach_keywords = extract_keywords(achievement.text)
        
        # Calculate keyword overlap
        keyword_overlap = calculate_overlap(
            ach_keywords,
            job.keywords.technical + job.keywords.domain
        )
        
        # Calculate technology match
        tech_match = calculate_overlap(
            achievement.technologies,
            job.requirements.required_skills + job.requirements.preferred_skills
        )
        
        # Check for impact metrics
        has_metrics = 1.0 if achievement.impact_metrics else 0.5
        
        # Combine scores
        relevance = (
            keyword_overlap * 0.40 +
            tech_match * 0.30 +
            has_metrics * 0.20 +
            0.10  # Recency bonus (handled separately)
        )
        
        ranked.append((achievement, relevance))
    
    # Sort by relevance score (descending)
    ranked.sort(key=lambda x: x[1], reverse=True)
    
    return ranked
```

### 7.3 Summary Generation (AI-Powered)

```python
async def generate_custom_summary(
    profile: UserProfile,
    job: JobDescription,
    style: str = "balanced"
) -> str:
    """
    Generate job-specific professional summary using Claude API
    """
    
    prompt = f"""
    Generate a professional resume summary (2-3 sentences) for this candidate
    applying to the following role.
    
    Candidate Background:
    - Name: {profile.name}
    - Current Summary: {profile.summary}
    - Top Skills: {', '.join(extract_top_skills(profile, n=10))}
    - Years Experience: {calculate_years_experience(profile)}
    - Key Achievements: {format_top_achievements(profile, n=3)}
    
    Target Job:
    - Title: {job.title}
    - Company: {job.company}
    - Required Skills: {', '.join(job.requirements.required_skills)}
    - Key Responsibilities: {format_responsibilities(job, n=3)}
    
    Style: {style}
    - "technical": Emphasize technical skills and technologies
    - "results": Emphasize achievements and impact
    - "balanced": Mix of both
    
    Requirements:
    - 2-3 sentences only
    - Include exact keywords from job requirements naturally
    - Highlight most relevant experience
    - Be truthful (don't fabricate skills)
    - Professional tone
    
    Generate the summary:
    """
    
    response = await call_claude_api(prompt)
    return response.content[0].text
```

---

## 8. Technology Stack

### 8.1 Core Dependencies

```toml
# pyproject.toml

[project]
name = "resume-customizer-mcp"
version = "1.0.0"
description = "MCP server for AI-powered resume customization"
requires-python = ">=3.10"

dependencies = [
    # MCP Server
    "mcp>=0.9.0",
    "pydantic>=2.0.0",
    
    # Markdown Parsing
    "markdown>=3.5.0",
    "markdown-it-py>=3.0.0",
    "python-frontmatter>=1.0.0",
    
    # AI/NLP
    "anthropic>=0.18.0",
    "spacy>=3.7.0",
    "scikit-learn>=1.3.0",
    
    # Document Generation
    "python-docx>=1.1.0",
    "WeasyPrint>=60.0",
    "Jinja2>=3.1.0",
    
    # Storage
    "aiosqlite>=0.19.0",
    
    # Utilities
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[project.scripts]
resume-customizer = "resume_customizer.server:main"
```

### 8.2 Environment Configuration

```bash
# .env.example

# Anthropic API (for AI-powered features)
ANTHROPIC_API_KEY=sk-ant-xxx

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-20250514
MAX_TOKENS=4096

# MCP Server
MCP_SERVER_NAME=resume_customizer
MCP_SERVER_VERSION=1.0.0
LOG_LEVEL=INFO

# Storage
DATABASE_PATH=./data/customizations.db
OUTPUT_DIRECTORY=./output
CACHE_DIRECTORY=./cache

# Features
ENABLE_AI_EXTRACTION=true
ENABLE_CACHE=true
CACHE_TTL_HOURS=24

# Templates
DEFAULT_TEMPLATE=modern
TEMPLATES_DIR=./templates
```

---

## 9. MCP Server Implementation

### 9.1 Server Entry Point

```python
# src/resume_customizer/server.py

import asyncio
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from .mcp.tools import register_tools
from .config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for MCP server"""
    
    # Load configuration
    config = load_config()
    logger.info(f"Starting Resume Customizer MCP Server v{config.version}")
    
    # Create MCP server
    server = Server("resume_customizer")
    
    # Register all tools
    register_tools(server, config)
    
    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Server ready and listening...")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### 9.2 Tool Registration

```python
# src/resume_customizer/mcp/tools.py

from mcp.server import Server
from mcp.types import Tool, TextContent
from .handlers import (
    handle_load_user_profile,
    handle_load_job_description,
    handle_analyze_match,
    handle_customize_resume,
    handle_generate_resume_files,
    handle_list_customizations
)

def register_tools(server: Server, config):
    """Register all MCP tools with the server"""
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="load_user_profile",
                description="Load and parse user's resume from markdown file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to resume.md file"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="load_job_description",
                description="Load and parse job description from markdown file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to job.md file"
                        },
                        "use_ai_extraction": {
                            "type": "boolean",
                            "description": "Use AI for keyword extraction",
                            "default": True
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            # ... other tools
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls"""
        
        if name == "load_user_profile":
            result = await handle_load_user_profile(arguments, config)
            
        elif name == "load_job_description":
            result = await handle_load_job_description(arguments, config)
            
        elif name == "analyze_match":
            result = await handle_analyze_match(arguments, config)
            
        elif name == "customize_resume":
            result = await handle_customize_resume(arguments, config)
            
        elif name == "generate_resume_files":
            result = await handle_generate_resume_files(arguments, config)
            
        elif name == "list_customizations":
            result = await handle_list_customizations(arguments, config)
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
```

---

## 10. Deployment & Usage

### 10.1 Installation for Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// %APPDATA%\Claude\claude_desktop_config.json (Windows)

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

### 10.2 Usage Example

**User workflow:**

1. Create `resume.md` with your profile
2. Create `job.md` with target job description
3. Open Claude Desktop
4. Start conversation:

```
User: I need to customize my resume for a Senior Data Engineer role 
      at Atlassian. My resume is at ./resume.md and the job description 
      is at ./job.md

Claude: I'll help you customize your resume. Let me load your profile 
        and analyze the job requirements.

[Claude calls load_user_profile("./resume.md")]
[Claude calls load_job_description("./job.md")]
[Claude calls analyze_match()]

Claude: Great! I've analyzed your profile against the Atlassian position:

        📊 Overall Match: 87%
        
        ✅ Strong Points:
        - Your Python & GCP experience (required skills)
        - 9 years experience (exceeds 7+ requirement)
        - Healthcare data engineering background
        
        ⚠️ Gaps:
        - Kubernetes (required) - you have Docker experience
        - Terraform (preferred)
        
        I can customize your resume to emphasize your strongest matches.
        Would you like me to proceed?

User: Yes, emphasize my data pipeline work and healthcare experience.

[Claude calls customize_resume(emphasize=["data pipeline", "healthcare"])]
[Claude calls generate_resume_files(formats=["pdf", "docx"])]

Claude: ✓ Resume customized and generated!
        
        📄 Files created:
        - ./output/John_Doe_Resume_Atlassian_DataEngineer_2025-12-21.pdf
        - ./output/John_Doe_Resume_Atlassian_DataEngineer_2025-12-21.docx
        
        Key changes:
        - Moved FHIR data processing achievement to top (95% relevance)
        - Highlighted BigQuery cost optimization (40% reduction)
        - Generated summary emphasizing distributed systems & healthcare
        - Added relevant keywords: "data governance", "ETL pipelines"
        
        Your resume is ready to submit!
```

---

## 11. Development Guide

### 11.1 Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/resume-customizer-mcp
cd resume-customizer-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install spaCy model
python -m spacy download en_core_web_sm

# Copy environment template
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run tests
pytest

# Start server (for testing)
python -m resume_customizer.server
```

### 11.2 Testing Tools

```bash
# Test load_user_profile
mcp-client call resume_customizer load_user_profile \
  '{"file_path": "./examples/resume.md"}'

# Test analyze_match
mcp-client call resume_customizer analyze_match \
  '{"profile_id": "...", "job_id": "..."}'
```

---

## 12. Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Load & parse resume.md | < 2 seconds | Including validation |
| Load & parse job.md | < 3 seconds | Including AI extraction |
| Calculate match score | < 5 seconds | With achievement ranking |
| Customize resume | < 10 seconds | Including AI summary generation |
| Generate PDF | < 8 seconds | Single page |
| Generate DOCX | < 5 seconds | Single page |
| **Total end-to-end** | **< 30 seconds** | Full customization workflow |

---

## 13. Error Handling

### 13.1 Common Errors

```python
class ResumeCustomizerError(Exception):
    """Base exception for all errors"""
    pass

class FileNotFoundError(ResumeCustomizerError):
    """Resume or job file not found"""
    pass

class ParseError(ResumeCustomizerError):
    """Failed to parse markdown file"""
    pass

class ValidationError(ResumeCustomizerError):
    """Invalid data in resume or job file"""
    pass

class AIServiceError(ResumeCustomizerError):
    """Claude API error"""
    pass

class GenerationError(ResumeCustomizerError):
    """Failed to generate PDF/DOCX"""
    pass
```

### 13.2 Error Response Format

```json
{
  "error": {
    "type": "ParseError",
    "message": "Failed to parse resume.md: Missing required field 'name'",
    "details": {
      "file": "./resume.md",
      "line": null,
      "suggestion": "Add a heading with your name at the top"
    }
  }
}
```

---

## 14. Next Steps for Implementation

### Phase 1: Core Foundation (Week 1)
- [ ] Project structure setup
- [ ] Markdown parser for resume.md
- [ ] Markdown parser for job.md
- [ ] Data models (Profile, Job, Match)
- [ ] Basic MCP server scaffold

### Phase 2: Matching Engine (Week 2)
- [ ] Skill matching algorithm
- [ ] Achievement ranking algorithm
- [ ] Match scoring implementation
- [ ] Gap analysis logic

### Phase 3: AI Integration (Week 3)
- [ ] Claude API service
- [ ] Keyword extraction
- [ ] Summary generation
- [ ] Achievement rephrasing (optional)

### Phase 4: Customization (Week 4)
- [ ] Resume customization engine
- [ ] Achievement reordering
- [ ] Skills optimization
- [ ] Truthfulness validation

### Phase 5: Document Generation (Week 5)
- [ ] HTML template system
- [ ] PDF generator
- [ ] DOCX generator
- [ ] Template selection logic

### Phase 6: MCP Tools (Week 6)
- [ ] Implement all 6 MCP tools
- [ ] Tool handlers
- [ ] Error handling
- [ ] Response formatting

### Phase 7: Storage & History (Week 7)
- [ ] SQLite database setup
- [ ] Customization logging
- [ ] History retrieval
- [ ] Session management

### Phase 8: Testing & Polish (Week 8)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation
- [ ] Example files
- [ ] Performance optimization

---

## 15. Success Metrics

- ✅ Successfully parses 95%+ of valid markdown resumes
- ✅ Match scores correlate with human judgment (>80% agreement)
- ✅ Generated resumes pass ATS systems
- ✅ End-to-end workflow < 30 seconds
- ✅ Zero fabricated information in outputs
- ✅ Users can customize without manual editing (80% of cases)

---

**Ready for Claude Code Development!**

This document provides everything needed to implement the Resume Customizer MCP Server. Start with Phase 1 and progress through each phase systematically.
