"""
Data models for Resume Customizer MCP Server.

This module defines all the core data structures used throughout the application.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContactInfo:
    """Contact information for a user."""

    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "github": self.github,
            "portfolio": self.portfolio,
            "other": self.other,
        }


@dataclass
class Achievement:
    """A single achievement or bullet point from work experience."""

    text: str
    technologies: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    relevance_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "technologies": self.technologies,
            "metrics": self.metrics,
            "relevance_score": self.relevance_score,
        }


@dataclass
class Experience:
    """Work experience entry."""

    company: str
    title: str
    start_date: str
    end_date: str
    location: str | None = None
    work_mode: str | None = None  # Remote/Hybrid/Onsite
    description: str | None = None
    achievements: list[Achievement] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "company": self.company,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "location": self.location,
            "work_mode": self.work_mode,
            "description": self.description,
            "achievements": [a.to_dict() for a in self.achievements],
            "technologies": self.technologies,
        }


@dataclass
class Skill:
    """A skill with optional proficiency level and years of experience."""

    name: str
    category: str = "General"
    proficiency: str | None = None  # Expert/Advanced/Intermediate/Basic
    years: int | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "proficiency": self.proficiency,
            "years": self.years,
            "description": self.description,
        }


@dataclass
class Education:
    """Education entry."""

    degree: str
    institution: str
    graduation_year: str | None = None
    gpa: str | None = None
    location: str | None = None
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "degree": self.degree,
            "institution": self.institution,
            "graduation_year": self.graduation_year,
            "gpa": self.gpa,
            "location": self.location,
            "details": self.details,
        }


@dataclass
class Certification:
    """Professional certification."""

    name: str
    issuer: str
    date: str | None = None
    expiry: str | None = None
    credential_id: str | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "issuer": self.issuer,
            "date": self.date,
            "expiry": self.expiry,
            "credential_id": self.credential_id,
            "url": self.url,
        }


@dataclass
class Project:
    """Personal or portfolio project."""

    name: str
    description: str
    technologies: list[str] = field(default_factory=list)
    url: str | None = None
    github: str | None = None
    highlights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "technologies": self.technologies,
            "url": self.url,
            "github": self.github,
            "highlights": self.highlights,
        }


@dataclass
class UserProfile:
    """Complete user profile parsed from resume."""

    name: str
    contact: ContactInfo
    summary: str
    experiences: list[Experience]
    skills: list[Skill]
    education: list[Education]
    certifications: list[Certification] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    profile_id: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "contact": self.contact.to_dict(),
            "summary": self.summary,
            "experiences": [e.to_dict() for e in self.experiences],
            "skills": [s.to_dict() for s in self.skills],
            "education": [e.to_dict() for e in self.education],
            "certifications": [c.to_dict() for c in self.certifications],
            "projects": [p.to_dict() for p in self.projects],
            "preferences": self.preferences,
            "profile_id": self.profile_id,
            "created_at": self.created_at,
        }


@dataclass
class JobRequirements:
    """Job requirements (required and preferred)."""

    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    required_experience_years: int | None = None
    required_education: str | None = None
    other_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "required_experience_years": self.required_experience_years,
            "required_education": self.required_education,
            "other_requirements": self.other_requirements,
        }


@dataclass
class JobKeywords:
    """Keywords extracted from job description."""

    technical: list[str] = field(default_factory=list)
    domain: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    all_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "technical": self.technical,
            "domain": self.domain,
            "soft_skills": self.soft_skills,
            "all_keywords": self.all_keywords,
        }


@dataclass
class JobDescription:
    """Complete job description."""

    title: str
    company: str
    location: str | None = None
    job_type: str | None = None  # Full-time/Part-time/Contract
    experience_level: str | None = None
    salary_range: str | None = None
    description: str = ""
    responsibilities: list[str] = field(default_factory=list)
    requirements: JobRequirements = field(default_factory=JobRequirements)
    technical_stack: list[str] = field(default_factory=list)
    keywords: JobKeywords = field(default_factory=JobKeywords)
    company_description: str | None = None
    apply_url: str | None = None
    posted_date: str | None = None
    job_id: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "salary_range": self.salary_range,
            "description": self.description,
            "responsibilities": self.responsibilities,
            "requirements": self.requirements.to_dict(),
            "technical_stack": self.technical_stack,
            "keywords": self.keywords.to_dict(),
            "company_description": self.company_description,
            "apply_url": self.apply_url,
            "posted_date": self.posted_date,
            "job_id": self.job_id,
            "created_at": self.created_at,
        }


@dataclass
class SkillMatch:
    """Matching information for a single skill."""

    skill: str
    matched: bool
    category: str  # required/preferred
    user_proficiency: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill": self.skill,
            "matched": self.matched,
            "category": self.category,
            "user_proficiency": self.user_proficiency,
        }


@dataclass
class MatchBreakdown:
    """Detailed breakdown of match scores."""

    technical_skills_score: float
    experience_score: float
    domain_score: float
    keyword_coverage_score: float
    total_score: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "technical_skills_score": self.technical_skills_score,
            "experience_score": self.experience_score,
            "domain_score": self.domain_score,
            "keyword_coverage_score": self.keyword_coverage_score,
            "total_score": self.total_score,
        }


@dataclass
class MatchResult:
    """Result of matching a profile against a job."""

    profile_id: str
    job_id: str
    overall_score: int  # 0-100
    breakdown: MatchBreakdown
    matched_skills: list[SkillMatch]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    suggestions: list[str] = field(default_factory=list)
    ranked_achievements: list[tuple[Achievement, float]] = field(default_factory=list)
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "profile_id": self.profile_id,
            "job_id": self.job_id,
            "overall_score": self.overall_score,
            "breakdown": self.breakdown.to_dict(),
            "matched_skills": [s.to_dict() for s in self.matched_skills],
            "missing_required_skills": self.missing_required_skills,
            "missing_preferred_skills": self.missing_preferred_skills,
            "suggestions": self.suggestions,
            "ranked_achievements": [
                (ach.to_dict(), score) for ach, score in self.ranked_achievements
            ],
            "created_at": self.created_at,
        }


@dataclass
class CustomizedResume:
    """A customized version of a resume for a specific job."""

    profile_id: str
    job_id: str
    match_result: MatchResult
    customized_summary: str | None = None
    selected_experiences: list[Experience] = field(default_factory=list)
    reordered_skills: list[Skill] = field(default_factory=list)
    template: str = "modern"
    metadata: dict[str, Any] = field(default_factory=dict)
    customization_id: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "profile_id": self.profile_id,
            "job_id": self.job_id,
            "match_result": self.match_result.to_dict(),
            "customized_summary": self.customized_summary,
            "selected_experiences": [e.to_dict() for e in self.selected_experiences],
            "reordered_skills": [s.to_dict() for s in self.reordered_skills],
            "template": self.template,
            "metadata": self.metadata,
            "customization_id": self.customization_id,
            "created_at": self.created_at,
        }
