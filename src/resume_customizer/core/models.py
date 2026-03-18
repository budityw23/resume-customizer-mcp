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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContactInfo":
        """Create a ContactInfo from a dictionary."""
        return cls(
            email=data["email"],
            phone=data.get("phone"),
            location=data.get("location"),
            linkedin=data.get("linkedin"),
            github=data.get("github"),
            portfolio=data.get("portfolio"),
            other=data.get("other", {}),
        )


@dataclass
class Achievement:
    """A single achievement or bullet point from work experience."""

    text: str
    technologies: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    rephrased_text: str | None = None  # AI-rephrased version for display

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "technologies": self.technologies,
            "metrics": self.metrics,
            "relevance_score": self.relevance_score,
            "rephrased_text": self.rephrased_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Achievement":
        """Create an Achievement from a dictionary."""
        return cls(
            text=data["text"],
            technologies=data.get("technologies", []),
            metrics=data.get("metrics", []),
            relevance_score=data.get("relevance_score", 0.0),
            rephrased_text=data.get("rephrased_text"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Experience":
        """Create an Experience from a dictionary."""
        return cls(
            company=data["company"],
            title=data["title"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            location=data.get("location"),
            work_mode=data.get("work_mode"),
            description=data.get("description"),
            achievements=[Achievement.from_dict(a) for a in data.get("achievements", [])],
            technologies=data.get("technologies", []),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Skill":
        """Create a Skill from a dictionary."""
        return cls(
            name=data["name"],
            category=data.get("category", "General"),
            proficiency=data.get("proficiency"),
            years=data.get("years"),
            description=data.get("description"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Education":
        """Create an Education from a dictionary."""
        return cls(
            degree=data["degree"],
            institution=data["institution"],
            graduation_year=data.get("graduation_year"),
            gpa=data.get("gpa"),
            location=data.get("location"),
            details=data.get("details", []),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Certification":
        """Create a Certification from a dictionary."""
        return cls(
            name=data["name"],
            issuer=data["issuer"],
            date=data.get("date"),
            expiry=data.get("expiry"),
            credential_id=data.get("credential_id"),
            url=data.get("url"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Create a Project from a dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            technologies=data.get("technologies", []),
            url=data.get("url"),
            github=data.get("github"),
            highlights=data.get("highlights", []),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserProfile":
        """Create a UserProfile from a dictionary."""
        return cls(
            name=data["name"],
            contact=ContactInfo.from_dict(data["contact"]),
            summary=data["summary"],
            experiences=[Experience.from_dict(e) for e in data.get("experiences", [])],
            skills=[Skill.from_dict(s) for s in data.get("skills", [])],
            education=[Education.from_dict(e) for e in data.get("education", [])],
            certifications=[Certification.from_dict(c) for c in data.get("certifications", [])],
            projects=[Project.from_dict(p) for p in data.get("projects", [])],
            preferences=data.get("preferences", {}),
            profile_id=data.get("profile_id"),
            created_at=data.get("created_at"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobRequirements":
        """Create a JobRequirements from a dictionary."""
        return cls(
            required_skills=data.get("required_skills", []),
            preferred_skills=data.get("preferred_skills", []),
            required_experience_years=data.get("required_experience_years"),
            required_education=data.get("required_education"),
            other_requirements=data.get("other_requirements", []),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobKeywords":
        """Create a JobKeywords from a dictionary."""
        return cls(
            technical=data.get("technical", []),
            domain=data.get("domain", []),
            soft_skills=data.get("soft_skills", []),
            all_keywords=data.get("all_keywords", []),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobDescription":
        """Create a JobDescription from a dictionary."""
        return cls(
            title=data["title"],
            company=data["company"],
            location=data.get("location"),
            job_type=data.get("job_type"),
            experience_level=data.get("experience_level"),
            salary_range=data.get("salary_range"),
            description=data.get("description", ""),
            responsibilities=data.get("responsibilities", []),
            requirements=JobRequirements.from_dict(data.get("requirements", {})),
            technical_stack=data.get("technical_stack", []),
            keywords=JobKeywords.from_dict(data.get("keywords", {})),
            company_description=data.get("company_description"),
            apply_url=data.get("apply_url"),
            posted_date=data.get("posted_date"),
            job_id=data.get("job_id"),
            created_at=data.get("created_at"),
        )


@dataclass
class SkillMatch:
    """Matching information for a single skill."""

    skill: str          # Job's required/preferred skill name
    matched: bool
    category: str       # "required" or "preferred"
    user_proficiency: str | None = None
    user_skill_name: str | None = None  # User's actual skill name (may differ via synonym)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill": self.skill,
            "matched": self.matched,
            "category": self.category,
            "user_proficiency": self.user_proficiency,
            "user_skill_name": self.user_skill_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillMatch":
        """Create a SkillMatch from a dictionary."""
        return cls(
            skill=data["skill"],
            matched=data["matched"],
            category=data["category"],
            user_proficiency=data.get("user_proficiency"),
            user_skill_name=data.get("user_skill_name"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MatchBreakdown":
        """Create a MatchBreakdown from a dictionary."""
        return cls(
            technical_skills_score=data["technical_skills_score"],
            experience_score=data["experience_score"],
            domain_score=data["domain_score"],
            keyword_coverage_score=data["keyword_coverage_score"],
            total_score=data["total_score"],
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MatchResult":
        """Create a MatchResult from a dictionary.

        Note: ranked_achievements stores tuples serialised as [dict, float] pairs.
        """
        ranked: list[tuple[Achievement, float]] = [
            (Achievement.from_dict(ach), float(score))
            for ach, score in data.get("ranked_achievements", [])
        ]
        return cls(
            profile_id=data["profile_id"],
            job_id=data["job_id"],
            overall_score=data["overall_score"],
            breakdown=MatchBreakdown.from_dict(data["breakdown"]),
            matched_skills=[SkillMatch.from_dict(s) for s in data.get("matched_skills", [])],
            missing_required_skills=data.get("missing_required_skills", []),
            missing_preferred_skills=data.get("missing_preferred_skills", []),
            suggestions=data.get("suggestions", []),
            ranked_achievements=ranked,
            created_at=data.get("created_at"),
        )


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomizedResume":
        """Create a CustomizedResume from a dictionary."""
        return cls(
            profile_id=data["profile_id"],
            job_id=data["job_id"],
            match_result=MatchResult.from_dict(data["match_result"]),
            customized_summary=data.get("customized_summary"),
            selected_experiences=[Experience.from_dict(e) for e in data.get("selected_experiences", [])],
            reordered_skills=[Skill.from_dict(s) for s in data.get("reordered_skills", [])],
            template=data.get("template", "modern"),
            metadata=data.get("metadata", {}),
            customization_id=data.get("customization_id"),
            created_at=data.get("created_at"),
        )
