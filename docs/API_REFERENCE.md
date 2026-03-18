# Resume Customizer MCP Server - API Reference

**Version**: 1.0.0
**Last Updated**: January 5, 2026

## Table of Contents

1. [Overview](#overview)
2. [Tool List](#tool-list)
3. [Tool Details](#tool-details)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## Overview

The Resume Customizer MCP Server exposes 6 tools through the Model Context Protocol (MCP). These tools enable Claude (or other MCP clients) to load resumes and job descriptions, analyze matches, customize resumes, and generate professional documents.

### Protocol

- **Transport**: stdio (Standard Input/Output)
- **Format**: JSON-RPC 2.0
- **Schema**: JSON Schema for tool inputs

### Base Response Format

All tools return responses in the following format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{JSON response data}"
    }
  ]
}
```

The `text` field contains a JSON string with the actual response data.

---

## Tool List

| Tool Name | Purpose | Key Inputs | Key Outputs |
|-----------|---------|------------|-------------|
| [`load_user_profile`](#load_user_profile) | Parse resume from Markdown | `file_path` | User profile with ID |
| [`load_job_description`](#load_job_description) | Parse job description from Markdown | `file_path` | Job description with ID |
| [`analyze_match`](#analyze_match) | Analyze profile-job match | `profile_id`, `job_id` | Match score and analysis |
| [`customize_resume`](#customize_resume) | Customize resume for job | `match_id`, `preferences` | Customized resume with ID |
| [`generate_resume_files`](#generate_resume_files) | Generate PDF/DOCX files | `customization_id`, `output_formats` | File paths |
| [`list_customizations`](#list_customizations) | List customization history | Filters (optional) | List of customizations |

---

## Tool Details

### load_user_profile

Load and parse a user's resume from a Markdown file.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "Path to the markdown resume file (resume.md)"
    }
  },
  "required": ["file_path"]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Absolute or relative path to `.md` file |

#### Response

```json
{
  "status": "success",
  "message": "User profile loaded successfully",
  "profile_id": "profile-abc123",
  "profile": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "location": "San Francisco, CA",
    "summary": "Experienced software engineer...",
    "skills_count": 24,
    "experiences_count": 3,
    "education_count": 1,
    "certifications_count": 2
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `message` | string | Human-readable message |
| `profile_id` | string | Unique ID for this profile (use in subsequent calls) |
| `profile` | object | Summary of parsed profile data |

#### Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `File not found` | `file_path` doesn't exist | Check path and ensure file exists |
| `Parse error` | Invalid Markdown format | Verify file follows resume template |
| `Validation error` | Missing required fields | Ensure name, email, and experience sections present |

#### Example Usage

```
Load my resume from ~/Documents/resume.md
```

---

### load_job_description

Load and parse a job description from a Markdown file.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string",
      "description": "Path to the markdown job description file (job.md)"
    }
  },
  "required": ["file_path"]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Absolute or relative path to `.md` file |

#### Response

```json
{
  "status": "success",
  "message": "Job description loaded successfully",
  "job_id": "job-xyz789",
  "job": {
    "title": "Senior Software Engineer",
    "company": "Acme Corp",
    "location": "San Francisco, CA",
    "job_type": "Full-time",
    "experience_level": "Senior",
    "required_skills_count": 8,
    "preferred_skills_count": 5,
    "responsibilities_count": 6
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `message` | string | Human-readable message |
| `job_id` | string | Unique ID for this job (use in subsequent calls) |
| `job` | object | Summary of parsed job data |

#### Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `File not found` | `file_path` doesn't exist | Check path and ensure file exists |
| `Parse error` | Invalid Markdown format | Verify file follows job template |
| `Validation error` | Missing required fields | Ensure title, company, and requirements present |

#### Example Usage

```
Load the job description from ~/Documents/jobs/acme-senior-swe.md
```

---

### analyze_match

Analyze how well a user profile matches a job description.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "profile_id": {
      "type": "string",
      "description": "ID of the loaded user profile"
    },
    "job_id": {
      "type": "string",
      "description": "ID of the loaded job description"
    }
  },
  "required": ["profile_id", "job_id"]
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | string | Yes | ID from `load_user_profile` response |
| `job_id` | string | Yes | ID from `load_job_description` response |

#### Response

```json
{
  "status": "success",
  "message": "Match analysis completed",
  "match_id": "match-def456",
  "overall_score": 87,
  "match_level": "Excellent",
  "breakdown": {
    "technical_skills": 92,
    "experience_level": 85,
    "domain_knowledge": 88,
    "keyword_coverage": 80
  },
  "skills_match": {
    "matched_required": ["Python", "JavaScript", "Docker", "AWS"],
    "matched_preferred": ["Kubernetes", "React"],
    "missing_required": [],
    "missing_preferred": ["Terraform"]
  },
  "recommendations": [
    "Highlight your Docker and AWS experience prominently",
    "Emphasize container orchestration work (relates to Kubernetes)",
    "Consider mentioning infrastructure-as-code projects"
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `match_id` | string | Unique ID for this match analysis |
| `overall_score` | integer | 0-100 overall match score |
| `match_level` | string | "Excellent" (90-100), "Great" (80-89), "Good" (70-79), "Fair" (60-69), "Weak" (<60) |
| `breakdown` | object | Scores for each component (0-100) |
| `skills_match` | object | Detailed skills matching analysis |
| `recommendations` | array | Suggestions for improving candidacy |

#### Score Components

| Component | Weight | Description |
|-----------|--------|-------------|
| `technical_skills` | 40% | Match between candidate skills and job requirements |
| `experience_level` | 25% | Years of experience vs. required |
| `domain_knowledge` | 20% | Industry/domain expertise alignment |
| `keyword_coverage` | 15% | Coverage of important keywords from job posting |

#### Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `Profile not found` | Invalid `profile_id` | Load profile first with `load_user_profile` |
| `Job not found` | Invalid `job_id` | Load job first with `load_job_description` |
| `Matching error` | Internal error during analysis | Check logs, retry operation |

#### Example Usage

```
Analyze how well I match this job
```

(Assumes profile and job already loaded)

---

### customize_resume

Customize a resume for a specific job based on match analysis.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "match_id": {
      "type": "string",
      "description": "ID of the match analysis result"
    },
    "preferences": {
      "type": "object",
      "properties": {
        "template": {
          "type": "string",
          "enum": ["modern", "classic", "ats_optimized"],
          "description": "Resume template to use"
        },
        "max_achievements_per_role": {
          "type": "integer",
          "description": "Maximum number of achievements per role",
          "default": 4
        },
        "summary_style": {
          "type": "string",
          "enum": ["technical", "results", "balanced"],
          "description": "Style for professional summary",
          "default": "balanced"
        }
      }
    }
  },
  "required": ["match_id"]
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `match_id` | string | Yes | - | ID from `analyze_match` response |
| `preferences` | object | No | {} | Customization options |
| `preferences.template` | string | No | "modern" | Template choice |
| `preferences.max_achievements_per_role` | integer | No | 4 | Achievements to show per job |
| `preferences.summary_style` | string | No | "balanced" | Summary writing style |

#### Template Options

| Template | Description | Best For |
|----------|-------------|----------|
| `modern` | Two-column, accent colors, contemporary | Tech companies, startups, creative roles |
| `classic` | Single-column, serif fonts, traditional | Corporate, finance, legal, academia |
| `ats_optimized` | Plain text, machine-readable | Large companies with automated screening |

#### Summary Styles

| Style | Description | Focus |
|-------|-------------|-------|
| `technical` | Emphasizes technical skills and tools | Technical roles, engineering positions |
| `results` | Highlights quantifiable achievements | Business-focused roles, management |
| `balanced` | Mix of technical skills and results | General purpose, most roles |

#### Response

```json
{
  "status": "success",
  "message": "Resume customized successfully",
  "customization_id": "custom-ghi789",
  "match_id": "match-def456",
  "profile_id": "profile-abc123",
  "job_id": "job-xyz789",
  "template": "modern",
  "created_at": "2026-01-05T10:30:00Z",
  "summary": {
    "experiences_count": 3,
    "skills_count": 18,
    "achievements_selected": 9,
    "achievements_total": 24
  },
  "changes": {
    "achievements_reordered": 9,
    "skills_reordered": 18,
    "summary_generated": true
  },
  "metadata": {
    "changes_count": 3,
    "preview_changes": [
      "Reordered 9 achievements by relevance",
      "Prioritized Python, Docker, AWS skills",
      "Generated custom summary emphasizing infrastructure experience"
    ]
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `customization_id` | string | Unique ID for customized resume (use for generation) |
| `match_id` | string | Original match ID |
| `template` | string | Template that will be used |
| `summary` | object | Summary statistics |
| `changes` | object | What was changed |
| `metadata` | object | Additional information |

#### Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `Match not found` | Invalid `match_id` | Run `analyze_match` first |
| `Invalid template` | Unknown template name | Use "modern", "classic", or "ats_optimized" |
| `Invalid preferences` | Malformed preferences object | Check JSON structure |

#### Example Usage

```
Customize my resume for this job using:
- Template: modern
- Max 3 achievements per role
- Summary style: technical
```

---

### generate_resume_files

Generate PDF and/or DOCX files from a customized resume.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "customization_id": {
      "type": "string",
      "description": "ID of the customized resume"
    },
    "output_formats": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["pdf", "docx"]
      },
      "description": "Output file formats",
      "default": ["pdf"]
    },
    "output_directory": {
      "type": "string",
      "description": "Directory to save files",
      "default": "./output"
    },
    "template": {
      "type": "string",
      "enum": ["modern", "classic", "ats_optimized"],
      "description": "Template override (optional)"
    },
    "filename_prefix": {
      "type": "string",
      "description": "Filename prefix",
      "default": "resume"
    }
  },
  "required": ["customization_id"]
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `customization_id` | string | Yes | - | ID from `customize_resume` response |
| `output_formats` | array | No | ["pdf"] | Formats to generate: "pdf", "docx", or both |
| `output_directory` | string | No | "./output" | Where to save files |
| `template` | string | No | (from customization) | Override template |
| `filename_prefix` | string | No | "resume" | Filename prefix |

#### Response

```json
{
  "status": "success",
  "message": "Resume files generated successfully",
  "files": [
    {
      "format": "pdf",
      "path": "/Users/john/Documents/output/John_Doe_Resume_Acme_Corp.pdf",
      "size": "142 KB"
    },
    {
      "format": "docx",
      "path": "/Users/john/Documents/output/John_Doe_Resume_Acme_Corp.docx",
      "size": "38 KB"
    }
  ],
  "template_used": "modern",
  "customization_id": "custom-ghi789"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `files` | array | Generated file details |
| `files[].format` | string | File format ("pdf" or "docx") |
| `files[].path` | string | Absolute path to generated file |
| `files[].size` | string | Human-readable file size |
| `template_used` | string | Template that was used |

#### File Naming Convention

```
{Name}_{Company_Name}_Resume.{ext}
```

Example:
```
John_Doe_Acme_Corp_Resume.pdf
John_Doe_Acme_Corp_Resume.docx
```

#### Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `Customization not found` | Invalid `customization_id` | Run `customize_resume` first |
| `Invalid output directory` | Directory doesn't exist or not writable | Check permissions, path validity |
| `Generation error` | Error creating PDF/DOCX | Check logs, ensure dependencies installed |

#### Example Usage

```
Generate PDF and DOCX files in ~/Documents/output/acme
```

---

### list_customizations

List all resume customizations with optional filtering.

#### Input Schema

```json
{
  "type": "object",
  "properties": {
    "filter_by_company": {
      "type": "string",
      "description": "Filter by company name"
    },
    "filter_by_date_range": {
      "type": "object",
      "properties": {
        "start_date": {
          "type": "string",
          "description": "Start date (ISO 8601)"
        },
        "end_date": {
          "type": "string",
          "description": "End date (ISO 8601)"
        }
      }
    },
    "limit": {
      "type": "integer",
      "description": "Maximum results",
      "default": 10
    }
  }
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filter_by_company` | string | No | - | Filter by company name (case-insensitive) |
| `filter_by_date_range` | object | No | - | Filter by date range |
| `filter_by_date_range.start_date` | string | No | - | ISO 8601 date (YYYY-MM-DD) |
| `filter_by_date_range.end_date` | string | No | - | ISO 8601 date (YYYY-MM-DD) |
| `limit` | integer | No | 10 | Maximum number of results |

#### Response

```json
{
  "status": "success",
  "message": "Found 3 customizations",
  "count": 3,
  "customizations": [
    {
      "customization_id": "custom-ghi789",
      "profile_name": "John Doe",
      "job_title": "Senior Software Engineer",
      "company": "Acme Corp",
      "match_score": 87,
      "template": "modern",
      "created_at": "2026-01-05T10:30:00Z"
    },
    {
      "customization_id": "custom-jkl012",
      "profile_name": "John Doe",
      "job_title": "Staff Engineer",
      "company": "TechCo",
      "match_score": 82,
      "template": "ats_optimized",
      "created_at": "2026-01-04T15:20:00Z"
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success" or "error" |
| `count` | integer | Number of customizations found |
| `customizations` | array | List of customizations |
| `customizations[].customization_id` | string | Unique ID |
| `customizations[].profile_name` | string | Candidate name |
| `customizations[].job_title` | string | Job title applied for |
| `customizations[].company` | string | Company name |
| `customizations[].match_score` | integer | Match score (0-100) |
| `customizations[].template` | string | Template used |
| `customizations[].created_at` | string | ISO 8601 timestamp |

#### Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `Database error` | Error querying database | Check logs, verify database not corrupted |
| `Invalid date format` | Malformed date string | Use ISO 8601 format (YYYY-MM-DD) |

#### Example Usage

```
List all my resume customizations from the past month
```

```
Show customizations for Acme Corp
```

---

## Data Models

### UserProfile

Structured representation of a resume.

```typescript
interface UserProfile {
  name: string;
  contact: ContactInfo;
  summary: string;
  skills: string[];
  experiences: Experience[];
  education: Education[];
  certifications?: Certification[];
  projects?: Project[];
}
```

### JobDescription

Structured representation of a job posting.

```typescript
interface JobDescription {
  title: string;
  company: string;
  location?: string;
  job_type?: string;
  experience_level?: string;
  salary_range?: string;
  description: string;
  responsibilities: string[];
  requirements: JobRequirements;
  apply_url?: string;
}
```

### MatchResult

Result of profile-job matching analysis.

```typescript
interface MatchResult {
  match_id: string;
  profile_id: string;
  job_id: string;
  overall_score: number;          // 0-100
  breakdown: MatchBreakdown;
  matched_skills: SkillMatch[];
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  achievement_rankings: AchievementRanking[];
  recommendations: string[];
  created_at: string;             // ISO 8601
}
```

### CustomizedResume

Customized resume ready for generation.

```typescript
interface CustomizedResume {
  customization_id: string;
  profile_id: string;
  job_id: string;
  match_id: string;
  name: string;
  contact: ContactInfo;
  summary?: string;
  skills: string[];
  experiences: Experience[];      // Achievements reordered
  education: Education[];
  certifications?: Certification[];
  template: string;
  created_at: string;
  metadata: {
    match_score: number;
    changes_log: object;
  };
}
```

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "status": "error",
  "error": "ValidationError",
  "message": "File path is required",
  "suggestion": "Please provide a valid file path for 'file_path'."
}
```

### Error Types

| Error Type | Description | HTTP Analogy |
|------------|-------------|--------------|
| `ValidationError` | Invalid input parameters | 400 Bad Request |
| `ResourceNotFoundError` | Profile/job/match not found | 404 Not Found |
| `ParseError` | Failed to parse Markdown | 422 Unprocessable Entity |
| `DatabaseError` | Database operation failed | 500 Internal Server Error |
| `AIServiceError` | Claude API error | 503 Service Unavailable |
| `GenerationError` | PDF/DOCX generation failed | 500 Internal Server Error |

### Common Error Scenarios

#### File Not Found

```json
{
  "status": "error",
  "error": "ValidationError",
  "message": "File does not exist: /path/to/resume.md",
  "suggestion": "Please check that the file path is correct and the file exists."
}
```

#### Invalid ID

```json
{
  "status": "error",
  "error": "ResourceNotFoundError",
  "message": "Profile not found: profile-invalid123",
  "suggestion": "Please load the profile first using the load_user_profile tool."
}
```

#### Parse Error

```json
{
  "status": "error",
  "error": "ParseError",
  "message": "Failed to parse resume: Missing required section 'Experience'",
  "suggestion": "Please ensure your resume includes the Experience section with at least one role."
}
```

---

## Examples

### Complete Workflow

#### 1. Load Resume

**Request**:
```json
{
  "name": "load_user_profile",
  "arguments": {
    "file_path": "/Users/john/Documents/resume.md"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "profile_id": "profile-abc123",
  "profile": {
    "name": "John Doe",
    "email": "john@example.com",
    "skills_count": 24
  }
}
```

#### 2. Load Job

**Request**:
```json
{
  "name": "load_job_description",
  "arguments": {
    "file_path": "/Users/john/Documents/jobs/acme-swe.md"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "job_id": "job-xyz789",
  "job": {
    "title": "Senior Software Engineer",
    "company": "Acme Corp",
    "required_skills_count": 8
  }
}
```

#### 3. Analyze Match

**Request**:
```json
{
  "name": "analyze_match",
  "arguments": {
    "profile_id": "profile-abc123",
    "job_id": "job-xyz789"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "match_id": "match-def456",
  "overall_score": 87,
  "match_level": "Excellent",
  "breakdown": {
    "technical_skills": 92,
    "experience_level": 85,
    "domain_knowledge": 88,
    "keyword_coverage": 80
  },
  "skills_match": {
    "matched_required": ["Python", "JavaScript", "Docker"],
    "missing_required": []
  }
}
```

#### 4. Customize Resume

**Request**:
```json
{
  "name": "customize_resume",
  "arguments": {
    "match_id": "match-def456",
    "preferences": {
      "template": "modern",
      "max_achievements_per_role": 3,
      "summary_style": "technical"
    }
  }
}
```

**Response**:
```json
{
  "status": "success",
  "customization_id": "custom-ghi789",
  "template": "modern",
  "summary": {
    "achievements_selected": 9,
    "achievements_total": 24
  },
  "changes": {
    "achievements_reordered": 9,
    "summary_generated": true
  }
}
```

#### 5. Generate Files

**Request**:
```json
{
  "name": "generate_resume_files",
  "arguments": {
    "customization_id": "custom-ghi789",
    "output_formats": ["pdf", "docx"],
    "output_directory": "/Users/john/Documents/output/acme"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "files": [
    {
      "format": "pdf",
      "path": "/Users/john/Documents/output/acme/John_Doe_Acme_Corp_Resume.pdf",
      "size": "142 KB"
    },
    {
      "format": "docx",
      "path": "/Users/john/Documents/output/acme/John_Doe_Acme_Corp_Resume.docx",
      "size": "38 KB"
    }
  ]
}
```

### Query History

**Request**:
```json
{
  "name": "list_customizations",
  "arguments": {
    "filter_by_company": "Acme",
    "limit": 5
  }
}
```

**Response**:
```json
{
  "status": "success",
  "count": 2,
  "customizations": [
    {
      "customization_id": "custom-ghi789",
      "profile_name": "John Doe",
      "job_title": "Senior Software Engineer",
      "company": "Acme Corp",
      "match_score": 87,
      "created_at": "2026-01-05T10:30:00Z"
    },
    {
      "customization_id": "custom-mno345",
      "profile_name": "John Doe",
      "job_title": "Principal Engineer",
      "company": "Acme Labs",
      "match_score": 91,
      "created_at": "2026-01-03T14:15:00Z"
    }
  ]
}
```

---

## Rate Limits

### Claude API

The system uses Claude API which has the following limits (as of 2026):

- **Requests per minute**: 1000 (Claude Sonnet 4.5)
- **Tokens per minute**: 80,000
- **Tokens per day**: 1,000,000

The server implements:
- Prompt caching (~80% cost savings)
- Exponential backoff retry
- Local caching (reduces API calls)

### Local Operations

No rate limits for:
- File parsing
- Matching analysis
- Document generation
- Database queries

---

## Versioning

### API Version

Current version: **1.0.0**

The API follows [Semantic Versioning](https://semver.org/):
- **Major** (1.x.x): Breaking changes
- **Minor** (x.1.x): New features (backward compatible)
- **Patch** (x.x.1): Bug fixes

### Compatibility

- **MCP Protocol**: v1.0
- **Minimum Python**: 3.11
- **Claude API**: v2023-06-01

---

## Support

For questions, issues, or feature requests:

- **GitHub Issues**: Report bugs
- **GitHub Discussions**: Ask questions
- **Documentation**: See [USER_GUIDE.md](USER_GUIDE.md) and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

**Last Updated**: January 5, 2026
**API Version**: 1.0.0
