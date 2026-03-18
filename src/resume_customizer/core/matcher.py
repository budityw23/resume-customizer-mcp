"""
Matching Engine for Resume Customizer - Phase 2.1, 2.2 & 2.3.

This module implements:
- Phase 2.1: Skill matching with normalization, synonyms, fuzzy matching, hierarchies
- Phase 2.2: Achievement ranking with keyword extraction and scoring
- Phase 2.3: Match scoring with weighted components and gap analysis
"""

import functools
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import spacy
import yaml
from rapidfuzz import fuzz

from resume_customizer.core.models import (
    Achievement,
    Experience,
    JobDescription,
    MatchBreakdown,
    MatchResult,
    Skill,
    SkillMatch,
    UserProfile,
)
from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)

# Load spaCy model (lazy loading)
_nlp = None


def get_nlp() -> spacy.language.Language:
    """Get or load spaCy NLP model."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. "
                "Install with: python -m spacy download en_core_web_sm"
            )
            raise
    return _nlp


def _parse_date(date_str: str) -> date | None:
    """
    Parse a date string into a date object.

    Supports: "Present", "YYYY-MM", "MM/YYYY", "Month YYYY", "YYYY".

    Args:
        date_str: Date string to parse

    Returns:
        date object or None if unparseable
    """
    if not date_str:
        return None
    date_str = date_str.strip()
    if date_str.lower() in ("present", "current", "now"):
        return date.today()
    for fmt in ("%Y-%m", "%m/%Y", "%B %Y", "%b %Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    # Try bare year
    try:
        year = int(date_str[:4])
        if 1950 <= year <= 2100:
            return date(year, 1, 1)
    except (ValueError, TypeError):
        pass
    return None


def calculate_experience_years(experiences: list[Experience]) -> float:
    """
    Calculate total years of experience from actual start/end dates.

    Args:
        experiences: List of Experience objects

    Returns:
        Total years as a float
    """
    total_months = 0
    for exp in experiences:
        start = _parse_date(exp.start_date)
        end = _parse_date(exp.end_date)
        if start and end:
            months = (end.year - start.year) * 12 + (end.month - start.month)
            total_months += max(0, months)
    return total_months / 12.0


@dataclass
class RankedAchievement:
    """Achievement with relevance score and explanation."""

    achievement: Achievement
    score: float
    reasons: list[str]


class SkillMatcher:
    """
    Matches skills between user profile and job requirements.

    Features:
    - Case-insensitive matching
    - Whitespace normalization
    - Synonym matching via YAML configuration
    - Fuzzy matching for typos and variations
    - Skill hierarchy (e.g., React → JavaScript)
    """

    def __init__(self, synonyms_file: Path | None = None):
        """
        Initialize skill matcher.

        Args:
            synonyms_file: Path to YAML file with skill synonyms and hierarchies.
                          Defaults to config/skill_synonyms.yaml
        """
        self.synonyms: dict[str, list[str]] = {}
        self.hierarchies: list[dict[str, Any]] = []
        self.skill_to_canonical: dict[str, str] = {}

        # Default to config/skill_synonyms.yaml (go up from src/resume_customizer/core to project root)
        if synonyms_file is None:
            synonyms_file = Path(__file__).parent.parent.parent.parent / "config" / "skill_synonyms.yaml"

        if synonyms_file.exists():
            self._load_synonyms(synonyms_file)
        else:
            logger.warning(f"Skill synonyms file not found: {synonyms_file}")

    def _load_synonyms(self, file_path: Path) -> None:
        """
        Load skill synonyms and hierarchies from YAML file.

        Args:
            file_path: Path to YAML configuration file
        """
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Load hierarchies first
        self.hierarchies = data.get("hierarchies", [])

        # Flatten all synonym groups from all categories
        for category, skills in data.items():
            if category == "hierarchies":
                continue

            if not isinstance(skills, dict):
                continue

            for canonical_name, synonyms in skills.items():
                if not isinstance(synonyms, list):
                    continue

                # Normalize all synonyms
                normalized_synonyms = [self._normalize(s) for s in synonyms]
                self.synonyms[canonical_name] = normalized_synonyms

                # Build reverse mapping: synonym -> canonical name
                for synonym in synonyms:
                    normalized = self._normalize(synonym)
                    self.skill_to_canonical[normalized] = canonical_name

        logger.info(f"Loaded {len(self.synonyms)} skill groups with synonyms")
        logger.info(f"Loaded {len(self.hierarchies)} skill hierarchies")

    def _normalize(self, skill: str) -> str:
        """
        Normalize skill name for matching.

        Normalization steps:
        1. Convert to lowercase
        2. Strip leading/trailing whitespace
        3. Collapse multiple spaces to single space
        4. Remove common file extensions (.js, .py, etc.)

        Args:
            skill: Skill name to normalize

        Returns:
            Normalized skill name

        Examples:
            >>> matcher._normalize("  Python  ")
            'python'
            >>> matcher._normalize("React.js")
            'react'
            >>> matcher._normalize("Node.JS")
            'node'
        """
        # Convert to lowercase and strip
        normalized = skill.lower().strip()

        # Collapse multiple whitespace to single space
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove common file extensions
        normalized = re.sub(r"\.(js|css|py|rb|java|ts)$", "", normalized)

        return normalized

    def match_skill(self, user_skill: str, required_skill: str, threshold: int = 80) -> bool:
        """
        Check if user skill matches required skill.

        Matching logic (in order of precedence):
        1. Exact match (normalized)
        2. Both map to same canonical skill (synonym match)
        3. One is in the other's synonym list
        4. Fuzzy string match above threshold
        5. Hierarchy match (user has child skill of required parent)

        Args:
            user_skill: Skill from user profile
            required_skill: Skill from job description
            threshold: Fuzzy match threshold (0-100), default 80

        Returns:
            True if skills match, False otherwise

        Examples:
            >>> matcher.match_skill("Python", "python")
            True
            >>> matcher.match_skill("React", "ReactJS")
            True  # Via synonyms
            >>> matcher.match_skill("React", "JavaScript")
            True  # Via hierarchy
        """
        norm_user = self._normalize(user_skill)
        norm_required = self._normalize(required_skill)

        # 1. Exact match
        if norm_user == norm_required:
            logger.debug(f"Exact match: {user_skill} == {required_skill}")
            return True

        # 2. Check if both map to same canonical skill
        user_canonical = self.skill_to_canonical.get(norm_user)
        required_canonical = self.skill_to_canonical.get(norm_required)

        if user_canonical and user_canonical == required_canonical:
            logger.debug(
                f"Canonical match: {user_skill} ~ {required_skill} (both map to {user_canonical})"
            )
            return True

        # 3. Check if user skill is in required skill's synonym list
        if required_canonical and norm_user in self.synonyms.get(required_canonical, []):
            logger.debug(f"Synonym match: {user_skill} in synonyms of {required_skill}")
            return True

        # 4. Check if required skill is in user skill's synonym list
        if user_canonical and norm_required in self.synonyms.get(user_canonical, []):
            logger.debug(f"Synonym match: {required_skill} in synonyms of {user_skill}")
            return True

        # 5. Fuzzy match for typos and variations
        similarity = fuzz.ratio(norm_user, norm_required)
        if similarity >= threshold:
            logger.debug(f"Fuzzy match: {user_skill} ~ {required_skill} ({similarity}%)")
            return True

        # 6. Check skill hierarchy (if user has child skill, they have parent)
        if self._check_hierarchy(norm_user, norm_required):
            return True

        # 7. If required_skill is a full sentence (e.g. "5+ years of Python experience"),
        #    check if the user's skill name appears as a word within it.
        if len(norm_required.split()) > 3:
            pattern = r"\b" + re.escape(norm_user) + r"\b"
            if re.search(pattern, norm_required):
                logger.debug(
                    f"Sentence containment: '{user_skill}' found in requirement '{required_skill[:60]}'"
                )
                return True

        return False

    def _check_hierarchy(self, user_skill: str, required_skill: str) -> bool:
        """
        Check if user skill is a child of required skill in hierarchy.

        If a job requires "JavaScript" and user has "React", this returns True
        because React is a child of JavaScript in the hierarchy.

        Args:
            user_skill: User's skill (normalized)
            required_skill: Required skill (normalized)

        Returns:
            True if user skill implies required skill via hierarchy

        Examples:
            If hierarchy defines: JavaScript -> [React, Vue, Node]
            >>> matcher._check_hierarchy("react", "javascript")
            True
            >>> matcher._check_hierarchy("javascript", "react")
            False
        """
        # Get canonical names
        user_canonical = self.skill_to_canonical.get(user_skill)
        required_canonical = self.skill_to_canonical.get(required_skill)

        if not user_canonical or not required_canonical:
            return False

        # Check if user's skill is a child of required skill
        for hierarchy in self.hierarchies:
            parent = self._normalize(hierarchy.get("parent", ""))

            # If required skill is the parent
            if parent == required_canonical:
                children = [self._normalize(c) for c in hierarchy.get("children", [])]

                # Check if user has one of the child skills
                if user_canonical in children:
                    logger.debug(
                        f"Hierarchy match: {user_skill} is child of {required_skill}"
                    )
                    return True

        return False

    def match_skills(
        self,
        user_skills: list[Skill],
        required_skills: list[str],
        category: str = "required",
    ) -> tuple[list[SkillMatch], list[str]]:
        """
        Match user skills against a list of required or preferred skills.

        Args:
            user_skills: List of user's skills from profile
            required_skills: List of skill names to match against
            category: Label for matched skills — "required" or "preferred"

        Returns:
            Tuple of (matched_skills, missing_skills):
            - matched_skills: List of SkillMatch objects with match details
            - missing_skills: Skills from required_skills not found in user profile

        Examples:
            >>> user_skills = [Skill(name="Python", category="language", proficiency="expert")]
            >>> required_skills = ["python", "java"]
            >>> matched, missing = matcher.match_skills(user_skills, required_skills)
            >>> len(matched)  # Python matched
            1
            >>> missing  # Java not found
            ['java']
        """
        matched: list[SkillMatch] = []
        missing: list[str] = []

        user_skill_names = [s.name for s in user_skills]

        for required in required_skills:
            match_found = False

            for user_skill in user_skill_names:
                if self.match_skill(user_skill, required):
                    user_prof = next(
                        (s.proficiency for s in user_skills if s.name == user_skill),
                        None,
                    )
                    matched.append(
                        SkillMatch(
                            skill=required,
                            matched=True,
                            category=category,
                            user_proficiency=user_prof,
                            user_skill_name=user_skill,
                        )
                    )
                    match_found = True
                    break

            if not match_found:
                missing.append(required)

        logger.info(
            f"Skill matching ({category}): {len(matched)}/{len(required_skills)} matched, "
            f"{len(missing)} missing"
        )

        return matched, missing

    def calculate_required_skills_match(
        self, user_skills: list[Skill], required_skills: list[str]
    ) -> int:
        """
        Calculate percentage of required skills that are matched.

        Args:
            user_skills: List of user's skills
            required_skills: List of required skills

        Returns:
            Match percentage (0-100)

        Examples:
            >>> matcher.calculate_required_skills_match(user_skills, ["python", "java", "sql"])
            66  # If 2 out of 3 matched
        """
        if not required_skills:
            return 100

        matched, _ = self.match_skills(user_skills, required_skills)
        percentage = int((len(matched) / len(required_skills)) * 100)

        return percentage

    def identify_missing_skills(
        self, user_skills: list[Skill], required_skills: list[str], preferred_skills: list[str] | None = None
    ) -> dict[str, list[str]]:
        """
        Identify which required and preferred skills are missing.

        Args:
            user_skills: List of user's skills
            required_skills: List of required skills
            preferred_skills: Optional list of preferred skills

        Returns:
            Dictionary with 'required' and 'preferred' lists of missing skills

        Examples:
            >>> missing = matcher.identify_missing_skills(
            ...     user_skills,
            ...     required_skills=["python", "java"],
            ...     preferred_skills=["kotlin", "scala"]
            ... )
            >>> missing['required']
            ['java']
            >>> missing['preferred']
            ['kotlin', 'scala']
        """
        _, missing_required = self.match_skills(user_skills, required_skills)

        missing_preferred: list[str] = []
        if preferred_skills:
            _, missing_preferred = self.match_skills(user_skills, preferred_skills)

        return {
            "required": missing_required,
            "preferred": missing_preferred,
        }


# ============================================================================
# Phase 2.2: Achievement Ranking System
# ============================================================================


@functools.lru_cache(maxsize=512)
def extract_keywords(
    text: str,
    include_pos: tuple[str, ...] = ("NOUN", "VERB", "PROPN"),
) -> list[str]:
    """
    Extract keywords from text using spaCy NLP.

    Results are cached by text content so the same text is never processed
    twice in the same process (avoids repeated spaCy calls in the achievement loop
    and across multiple score sub-functions that use the same job text).

    Args:
        text: Text to extract keywords from
        include_pos: Part-of-speech tags to include (tuple for hashability)

    Returns:
        List of extracted keywords (lemmatized)

    Examples:
        >>> extract_keywords("Built scalable microservices using Python and Docker")
        ['build', 'scalable', 'microservice', 'python', 'docker']
    """
    nlp = get_nlp()
    doc = nlp(text)

    keywords = []
    for token in doc:
        if token.pos_ in include_pos and not token.is_stop and len(token.text) > 2:
            keywords.append(token.lemma_.lower())

    return keywords


@functools.lru_cache(maxsize=512)
def extract_technical_terms(text: str) -> list[str]:
    """
    Extract technical terms and technologies from text.

    Looks for:
    - Capitalized words (likely tech names)
    - Acronyms (2+ uppercase letters)
    - Common tech patterns (Package.name, file.ext)
    - Version numbers

    Args:
        text: Text to analyze

    Returns:
        List of technical terms found (normalized to lowercase)

    Examples:
        >>> extract_technical_terms("Used React.js v18 and REST API")
        ['react.js', 'v18', 'rest', 'api']
    """
    terms = []

    # Pattern 1: Package names with dots (e.g., React.js, Node.js)
    package_pattern = r"\b[A-Z][a-z]+(?:\.[a-z]+)+\b"
    terms.extend(re.findall(package_pattern, text))

    # Pattern 2: Acronyms (2+ uppercase letters)
    acronym_pattern = r"\b[A-Z]{2,}\b"
    terms.extend(re.findall(acronym_pattern, text))

    # Pattern 3: Version numbers
    version_pattern = r"\bv?\d+\.\d+(?:\.\d+)?\b"
    terms.extend(re.findall(version_pattern, text, re.IGNORECASE))

    # Pattern 4: Capitalized words (likely proper nouns/tech names)
    capitalized_pattern = r"\b[A-Z][a-zA-Z]+\b"
    capitalized = re.findall(capitalized_pattern, text)
    # Filter out common English words that happen to be capitalized
    common_words = {"The", "This", "That", "These", "Those", "As", "In", "On", "At", "To", "For"}
    terms.extend([w for w in capitalized if w not in common_words])

    # Normalize to lowercase and deduplicate
    return list({t.lower() for t in terms if len(t) > 1})


@functools.lru_cache(maxsize=512)
def extract_metrics(text: str) -> list[str]:
    """
    Extract metrics and quantifiable achievements.

    Looks for:
    - Percentages (50%, 100%)
    - Money amounts ($1M, $500K)
    - Multipliers (10x, 5x)
    - Large numbers with commas (1,000,000)
    - Numbers with + suffix (100+)

    Args:
        text: Text to analyze

    Returns:
        List of metrics found

    Examples:
        >>> extract_metrics("Improved performance by 50% and reduced costs by $100K")
        ['50%', '$100K']
    """
    metrics = []

    patterns = [
        r"\d+%",  # Percentages: 50%
        r"\$\d+(?:[,.]\d+)?[KMB]?",  # Money: $100K, $1.5M
        r"\d+x",  # Multipliers: 10x, 5x
        r"\d+(?:,\d{3})+",  # Large numbers: 1,000,000
        r"\d+\+",  # Plus suffix: 100+
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        metrics.extend(matches)

    return metrics


def rank_achievements(
    achievements: list[Achievement],
    job_description: JobDescription,
    achievement_dates: dict[str, str] | None = None,
) -> list[RankedAchievement]:
    """
    Rank achievements by relevance to job description.

    Scoring breakdown:
    - Keyword overlap with job (40%)
    - Technology/skill match (30%)
    - Presence of metrics (20%)
    - Recency (10%)

    Args:
        achievements: List of achievements to rank
        job_description: Target job description
        achievement_dates: Optional mapping of achievement text -> experience start_date string

    Returns:
        List of ranked achievements with scores and reasons, sorted by score descending

    Examples:
        >>> ranked = rank_achievements(user_achievements, job_desc)
        >>> ranked[0].score
        85.5
        >>> ranked[0].reasons
        ['5 matching keywords', '3 matching technologies', 'Contains 2 metrics', 'Recent (2024)']
    """
    # Extract job keywords
    job_text = " ".join(
        [
            job_description.description or "",
            " ".join(job_description.responsibilities),
            " ".join(job_description.requirements.required_skills),
        ]
    )

    job_keywords = set(extract_keywords(job_text))
    job_tech = set(extract_technical_terms(job_text))
    job_skills = {s.lower() for s in job_description.requirements.required_skills}

    ranked: list[RankedAchievement] = []

    for achievement in achievements:
        score = 0.0
        reasons = []

        # Extract achievement features
        achievement_keywords = set(extract_keywords(achievement.text))
        achievement_tech = set(extract_technical_terms(achievement.text))
        achievement_metrics = extract_metrics(achievement.text)

        # 1. Keyword overlap score (40%)
        keyword_overlap = len(achievement_keywords & job_keywords)
        if keyword_overlap > 0:
            keyword_score = min(keyword_overlap / max(len(job_keywords), 1), 1.0) * 40
            score += keyword_score
            reasons.append(f"{keyword_overlap} matching keywords")

        # 2. Technology match score (30%)
        tech_overlap = len(achievement_tech & job_tech) + len(achievement_tech & job_skills)
        if tech_overlap > 0:
            tech_score = min(tech_overlap / max(len(job_tech | job_skills), 1), 1.0) * 30
            score += tech_score
            reasons.append(f"{tech_overlap} matching technologies")

        # 3. Metrics presence bonus (20%)
        if achievement_metrics:
            score += 20
            reasons.append(f"Contains {len(achievement_metrics)} metrics")

        # 4. Recency bonus (10%) — based on parent experience start date
        if achievement_dates:
            start_date_str = achievement_dates.get(achievement.text, "")
            exp_date = _parse_date(start_date_str)
            if exp_date:
                years_ago = (date.today() - exp_date).days / 365.25
                if years_ago <= 2:
                    recency_score = 10.0
                elif years_ago <= 5:
                    recency_score = 7.0
                elif years_ago <= 10:
                    recency_score = 4.0
                else:
                    recency_score = 1.0
                score += recency_score
                reasons.append(f"Recent ({exp_date.year})")

        ranked.append(
            RankedAchievement(achievement=achievement, score=score, reasons=reasons)
        )

    # Sort by score descending
    ranked.sort(key=lambda x: x.score, reverse=True)

    logger.info(f"Ranked {len(ranked)} achievements")
    if ranked:
        logger.debug(f"Top score: {ranked[0].score:.1f}, Bottom score: {ranked[-1].score:.1f}")

    return ranked


# ============================================================================
# Phase 2.3: Match Scoring Implementation
# ============================================================================


def calculate_experience_score(
    user_profile: UserProfile, job_description: JobDescription
) -> float:
    """
    Calculate experience level match score (0-100).

    Compares user's actual years of experience (from date ranges) with job requirements.

    Args:
        user_profile: User's profile
        job_description: Job description

    Returns:
        Score from 0-100 based on experience match

    Examples:
        >>> calculate_experience_score(profile, job)
        85.0  # User has 5 years, job requires 3-5 years
    """
    required_years = job_description.requirements.required_experience_years

    # If no requirement specified, give full score
    if required_years is None:
        return 100.0

    actual_years = calculate_experience_years(user_profile.experiences)

    if actual_years >= required_years:
        # Has required experience or more - slight penalty for gross overqualification
        if actual_years > required_years * 2.5:
            return 90.0
        return 100.0
    else:
        return min((actual_years / required_years) * 100, 100.0)


def calculate_domain_score(
    user_profile: UserProfile, job_description: JobDescription
) -> float:
    """
    Calculate domain knowledge match score (0-100).

    Compares user's work experience in similar domains/industries with job.

    Args:
        user_profile: User's profile
        job_description: Job description

    Returns:
        Score from 0-100 based on domain match

    Examples:
        >>> calculate_domain_score(profile, job)
        75.0  # User has relevant industry experience
    """
    # Extract domain keywords from job
    job_domain_text = " ".join(
        [
            job_description.company_description or "",
            job_description.description or "",
        ]
    )

    if not job_domain_text.strip():
        return 100.0  # No domain context to match against

    job_domain_keywords = set(extract_keywords(job_domain_text))

    # Extract keywords from user's experience descriptions
    user_domain_keywords = set()
    for exp in user_profile.experiences:
        if exp.description:
            user_domain_keywords.update(extract_keywords(exp.description))

    # Calculate overlap
    if not job_domain_keywords:
        return 100.0

    overlap = len(job_domain_keywords & user_domain_keywords)
    score = min((overlap / len(job_domain_keywords)) * 100, 100.0)

    return score


def calculate_keyword_score(
    user_profile: UserProfile, job_description: JobDescription
) -> float:
    """
    Calculate keyword coverage score (0-100).

    Measures how many important keywords from the job description
    appear in the user's profile.

    Args:
        user_profile: User's profile
        job_description: Job description

    Returns:
        Score from 0-100 based on keyword coverage

    Examples:
        >>> calculate_keyword_score(profile, job)
        80.0  # 80% of job keywords found in profile
    """
    # Extract job keywords
    job_text = " ".join(
        [
            job_description.title,
            job_description.description or "",
            " ".join(job_description.responsibilities),
        ]
    )
    job_keywords = set(extract_keywords(job_text))

    # Extract user keywords from summary and achievements
    user_text_parts = [user_profile.summary]
    for exp in user_profile.experiences:
        for achievement in exp.achievements:
            user_text_parts.append(achievement.text)

    user_keywords = set(extract_keywords(" ".join(user_text_parts)))

    # Calculate coverage
    if not job_keywords:
        return 100.0

    overlap = len(job_keywords & user_keywords)
    coverage = (overlap / len(job_keywords)) * 100

    return min(coverage, 100.0)


def calculate_match_score(
    user_profile: UserProfile,
    job_description: JobDescription,
    skill_matcher: SkillMatcher | None = None,
) -> MatchResult:
    """
    Calculate overall match score between user profile and job description.

    Scoring breakdown:
    - Technical Skills (40%): Match of required/preferred skills
    - Experience Level (25%): Years of experience vs requirement
    - Domain Knowledge (20%): Industry/domain experience
    - Keyword Coverage (15%): Presence of job keywords in profile

    Args:
        user_profile: User's profile
        job_description: Target job description
        skill_matcher: Optional SkillMatcher instance (creates new if None)

    Returns:
        MatchResult with overall score, breakdown, and suggestions

    Examples:
        >>> result = calculate_match_score(profile, job)
        >>> result.overall_score
        85
        >>> result.breakdown.technical_skills_score
        90.0
    """
    # Initialize skill matcher if not provided
    if skill_matcher is None:
        skill_matcher = SkillMatcher()

    # ----------------------------------------------------------------
    # 1. Technical Skills Score (40% weight)
    # Run match_skills ONCE per skill set and derive both the percentage
    # and the detailed match objects from that single result.
    # ----------------------------------------------------------------
    matched_required, missing_required = skill_matcher.match_skills(
        user_profile.skills,
        job_description.requirements.required_skills,
        category="required",
    )
    total_required = len(job_description.requirements.required_skills)
    required_skills_percentage = (
        int((len(matched_required) / total_required) * 100) if total_required else 100
    )

    matched_preferred: list[SkillMatch] = []
    missing_preferred: list[str] = []
    preferred_skills_percentage = 100.0
    if job_description.requirements.preferred_skills:
        matched_preferred, missing_preferred = skill_matcher.match_skills(
            user_profile.skills,
            job_description.requirements.preferred_skills,
            category="preferred",
        )
        total_preferred = len(job_description.requirements.preferred_skills)
        preferred_skills_percentage = (
            int((len(matched_preferred) / total_preferred) * 100) if total_preferred else 100
        )

    # Combined matched skills with correct categories
    matched_skills: list[SkillMatch] = matched_required + matched_preferred

    # Weighted average: required skills carry more weight (70/30)
    technical_skills_score = (required_skills_percentage * 0.7) + (preferred_skills_percentage * 0.3)

    # 2. Calculate Experience Score (25% weight)
    experience_score = calculate_experience_score(user_profile, job_description)

    # 3. Calculate Domain Score (20% weight)
    domain_score = calculate_domain_score(user_profile, job_description)

    # 4. Calculate Keyword Coverage Score (15% weight)
    keyword_score = calculate_keyword_score(user_profile, job_description)

    # Calculate weighted total
    total_score = (
        (technical_skills_score * 0.40) +
        (experience_score * 0.25) +
        (domain_score * 0.20) +
        (keyword_score * 0.15)
    )

    # Generate suggestions based on gaps
    suggestions = _generate_suggestions(
        missing_required=missing_required,
        missing_preferred=missing_preferred,
        technical_score=technical_skills_score,
        experience_score=experience_score,
        domain_score=domain_score,
        keyword_score=keyword_score,
    )

    # Rank achievements — build date lookup so recency scoring works
    all_achievements = []
    achievement_dates: dict[str, str] = {}
    for exp in user_profile.experiences:
        for ach in exp.achievements:
            all_achievements.append(ach)
            achievement_dates[ach.text] = exp.start_date

    ranked_achievements_list = rank_achievements(all_achievements, job_description, achievement_dates)
    ranked_achievements_tuples = [
        (ra.achievement, ra.score) for ra in ranked_achievements_list
    ]

    # Create result
    breakdown = MatchBreakdown(
        technical_skills_score=round(technical_skills_score, 1),
        experience_score=round(experience_score, 1),
        domain_score=round(domain_score, 1),
        keyword_coverage_score=round(keyword_score, 1),
        total_score=round(total_score, 1),
    )

    result = MatchResult(
        profile_id=user_profile.profile_id or "unknown",
        job_id=job_description.job_id or "unknown",
        overall_score=int(round(total_score)),
        breakdown=breakdown,
        matched_skills=matched_skills,
        missing_required_skills=missing_required,
        missing_preferred_skills=missing_preferred,
        suggestions=suggestions,
        ranked_achievements=ranked_achievements_tuples,
    )

    logger.info(
        f"Match calculated: {result.overall_score}% "
        f"(tech:{technical_skills_score:.1f}, exp:{experience_score:.1f}, "
        f"domain:{domain_score:.1f}, keywords:{keyword_score:.1f})"
    )

    return result


def _generate_suggestions(
    missing_required: list[str],
    missing_preferred: list[str],
    technical_score: float,
    experience_score: float,
    domain_score: float,
    keyword_score: float,
) -> list[str]:
    """
    Generate suggestions for improving match score.

    Args:
        missing_required: List of missing required skills
        missing_preferred: List of missing preferred skills
        technical_score: Technical skills score
        experience_score: Experience score
        domain_score: Domain score
        keyword_score: Keyword score

    Returns:
        List of actionable suggestions
    """
    suggestions = []

    # Suggest missing required skills (high priority)
    if missing_required:
        suggestions.append(
            f"Add these required skills to your profile: {', '.join(missing_required[:5])}"
        )

    # Suggest missing preferred skills
    if missing_preferred and len(suggestions) < 3:
        suggestions.append(
            f"Consider adding preferred skills: {', '.join(missing_preferred[:3])}"
        )

    # Score-based suggestions
    if technical_score < 60:
        suggestions.append(
            "Focus on developing the technical skills mentioned in the job description"
        )

    if experience_score < 70:
        suggestions.append(
            "Highlight relevant project experience to demonstrate skills in practice"
        )

    if domain_score < 60:
        suggestions.append(
            "Emphasize any domain knowledge or industry experience related to this role"
        )

    if keyword_score < 60:
        suggestions.append(
            "Update your summary and achievements to include more keywords from the job posting"
        )

    # Limit to top 5 suggestions
    return suggestions[:5]
