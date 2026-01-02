"""
Resume customization logic.

This module implements Phase 4 of the Resume Customizer MCP Server:
- Achievement reordering based on job relevance
- Skills optimization
- Resume customization combining all AI insights

All operations preserve truthfulness - no fabrication or modification
of original content is allowed.
"""

import logging
from dataclasses import dataclass
from typing import Any

from .models import (
    Achievement,
    CustomizedResume,
    Experience,
    MatchResult,
    Skill,
    SkillMatch,
    UserProfile,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Phase 4.1: Achievement Reordering Implementation
# ============================================================================


@dataclass
class AchievementSelection:
    """Configuration for achievement selection strategy."""

    top_n: int = 3  # Number of achievements per role
    ensure_diversity: bool = True  # Ensure achievements from multiple roles
    prioritize_leadership: bool = True  # Boost leadership achievements
    include_metrics: bool = True  # Prefer achievements with metrics
    min_relevance_score: float = 0.0  # Minimum relevance score to include


def _has_leadership_indicators(achievement: Achievement) -> bool:
    """
    Check if achievement contains leadership indicators.

    Args:
        achievement: Achievement to check

    Returns:
        True if achievement shows leadership

    Examples:
        >>> ach = Achievement(text="Led team of 5 engineers")
        >>> _has_leadership_indicators(ach)
        True
    """
    leadership_keywords = {
        "led", "lead", "managed", "directed", "coordinated",
        "supervised", "mentored", "coached", "guided",
        "spearheaded", "drove", "initiated", "founded",
        "established", "built team", "hired", "onboarded",
        "team of", "cross-functional", "stakeholder",
    }

    text_lower = achievement.text.lower()
    return any(keyword in text_lower for keyword in leadership_keywords)


def _calculate_diversity_score(
    achievement: Achievement,
    experience: Experience,
    selected_companies: set[str],
    selected_titles: set[str],
) -> float:
    """
    Calculate diversity bonus for achievement.

    Rewards achievements from different companies/roles to show breadth.

    Args:
        achievement: Achievement to score
        experience: Experience this achievement belongs to
        selected_companies: Companies already represented
        selected_titles: Job titles already represented

    Returns:
        Diversity bonus (0.0-1.0)

    Examples:
        >>> score = _calculate_diversity_score(ach, exp, {"Google"}, {"SWE"})
        >>> 0.0 <= score <= 1.0
        True
    """
    diversity_bonus = 0.0

    # Bonus for new company
    if experience.company not in selected_companies:
        diversity_bonus += 0.5

    # Bonus for new role type
    if experience.title not in selected_titles:
        diversity_bonus += 0.5

    return diversity_bonus


def reorder_achievements(
    user_profile: UserProfile,
    match_result: MatchResult,
    strategy: AchievementSelection | None = None,
) -> list[Experience]:
    """
    Reorder achievements based on job relevance and selection strategy.

    This function implements Phase 4.1 - Achievement Reordering.
    It creates a new list of Experience objects with achievements reordered
    by relevance to the target job.

    Key features:
    - Uses relevance scores from MatchResult.ranked_achievements
    - Applies selection strategy (top N, diversity, leadership, metrics)
    - Preserves truthfulness (no modification of achievement text)
    - Maintains original Experience metadata (company, title, dates)

    Args:
        user_profile: User's original profile
        match_result: Match analysis with ranked achievements
        strategy: Selection strategy configuration (default: top 3 per role)

    Returns:
        List of Experience objects with achievements reordered and filtered

    Raises:
        ValueError: If match_result doesn't contain ranked achievements

    Examples:
        >>> experiences = reorder_achievements(profile, match_result)
        >>> len(experiences[0].achievements) <= 3  # Top 3 per role
        True
        >>> experiences[0].achievements[0].relevance_score >= 80  # Most relevant first
        True
    """
    if strategy is None:
        strategy = AchievementSelection()

    logger.info(
        f"Reordering achievements with strategy: top_n={strategy.top_n}, "
        f"diversity={strategy.ensure_diversity}, leadership={strategy.prioritize_leadership}"
    )

    # Validate we have ranked achievements
    if not match_result.ranked_achievements:
        logger.warning("No ranked achievements in match result")
        return user_profile.experiences

    # Build lookup: achievement text -> (score, achievement object)
    achievement_scores: dict[str, tuple[float, Achievement]] = {}
    for achievement, score in match_result.ranked_achievements:
        # Store the achievement with its relevance_score set
        achievement_with_score = Achievement(
            text=achievement.text,
            technologies=achievement.technologies,
            metrics=achievement.metrics,
            relevance_score=score,
        )
        achievement_scores[achievement.text] = (score, achievement_with_score)

    # Track diversity
    selected_companies: set[str] = set()
    selected_titles: set[str] = set()

    # Process each experience
    customized_experiences: list[Experience] = []

    for experience in user_profile.experiences:
        if not experience.achievements:
            # Keep experiences with no achievements as-is
            customized_experiences.append(experience)
            continue

        # Score and rank achievements for this experience
        scored_achievements: list[tuple[Achievement, float]] = []

        for achievement in experience.achievements:
            base_score, achievement_obj = achievement_scores.get(
                achievement.text, (0.0, achievement)
            )

            # Skip if below minimum relevance threshold
            if base_score < strategy.min_relevance_score:
                continue

            # Calculate final score with bonuses
            final_score = base_score

            # Leadership bonus
            if strategy.prioritize_leadership and _has_leadership_indicators(achievement_obj):
                final_score += 10.0
                logger.debug(f"Leadership bonus: +10.0 for '{achievement_obj.text[:50]}...'")

            # Metrics bonus
            if strategy.include_metrics and achievement_obj.metrics:
                final_score += 5.0
                logger.debug(f"Metrics bonus: +5.0 for '{achievement_obj.text[:50]}...'")

            # Diversity bonus
            if strategy.ensure_diversity:
                diversity_bonus = _calculate_diversity_score(
                    achievement_obj, experience, selected_companies, selected_titles
                )
                final_score += diversity_bonus * 5.0  # Scale to 0-5 point bonus

            scored_achievements.append((achievement_obj, final_score))

        # Sort by final score (descending)
        scored_achievements.sort(key=lambda x: x[1], reverse=True)

        # Select top N achievements
        selected_achievements = [
            ach for ach, score in scored_achievements[:strategy.top_n]
        ]

        # Update diversity tracking
        if selected_achievements:
            selected_companies.add(experience.company)
            selected_titles.add(experience.title)

        # Create new Experience with reordered achievements
        customized_experience = Experience(
            company=experience.company,
            title=experience.title,
            start_date=experience.start_date,
            end_date=experience.end_date,
            location=experience.location,
            work_mode=experience.work_mode,
            description=experience.description,
            achievements=selected_achievements,
            technologies=experience.technologies,
        )

        customized_experiences.append(customized_experience)

        logger.info(
            f"Selected {len(selected_achievements)}/{len(experience.achievements)} "
            f"achievements for {experience.title} at {experience.company}"
        )

    # Validate truthfulness
    _validate_achievement_truthfulness(user_profile, customized_experiences)

    logger.info(f"Reordered achievements across {len(customized_experiences)} experiences")
    return customized_experiences


def _validate_achievement_truthfulness(
    original_profile: UserProfile,
    customized_experiences: list[Experience],
) -> None:
    """
    Validate that no achievements were fabricated or modified.

    Ensures all achievements in customized experiences exist in original profile
    and have not been altered.

    Args:
        original_profile: Original user profile
        customized_experiences: Customized experiences to validate

    Raises:
        ValueError: If any achievement is fabricated or modified

    Examples:
        >>> _validate_achievement_truthfulness(profile, experiences)
        # Raises ValueError if validation fails
    """
    # Build set of original achievement texts
    original_texts: set[str] = set()
    for exp in original_profile.experiences:
        for ach in exp.achievements:
            original_texts.add(ach.text)

    # Check all customized achievements exist in original
    for exp in customized_experiences:
        for ach in exp.achievements:
            if ach.text not in original_texts:
                raise ValueError(
                    f"Fabricated achievement detected: '{ach.text[:100]}...' "
                    f"not found in original profile"
                )

    logger.debug("Truthfulness validation passed - no fabricated achievements")


# ============================================================================
# Utility Functions
# ============================================================================


def get_achievement_statistics(
    original_profile: UserProfile,
    customized_experiences: list[Experience],
) -> dict[str, Any]:
    """
    Get statistics about achievement selection.

    Args:
        original_profile: Original profile
        customized_experiences: Customized experiences

    Returns:
        Dictionary with selection statistics

    Examples:
        >>> stats = get_achievement_statistics(profile, experiences)
        >>> stats["total_original"]
        25
        >>> stats["total_selected"]
        9
        >>> stats["selection_rate"]
        0.36
    """
    total_original = sum(len(exp.achievements) for exp in original_profile.experiences)
    total_selected = sum(len(exp.achievements) for exp in customized_experiences)

    companies_original = {exp.company for exp in original_profile.experiences}
    companies_selected = {
        exp.company for exp in customized_experiences if exp.achievements
    }

    return {
        "total_original": total_original,
        "total_selected": total_selected,
        "selection_rate": total_selected / total_original if total_original > 0 else 0.0,
        "companies_original": len(companies_original),
        "companies_represented": len(companies_selected),
        "diversity_rate": (
            len(companies_selected) / len(companies_original)
            if companies_original
            else 0.0
        ),
    }


# ============================================================================
# Phase 4.2: Skills Optimization Implementation
# ============================================================================


@dataclass
class SkillsDisplayStrategy:
    """Configuration for skills display strategy."""

    show_all: bool = False  # Show all skills vs relevant only
    top_n: int | None = None  # Limit to top N skills (None = no limit)
    group_by_category: bool = True  # Group skills by category
    min_relevance_score: float = 0.0  # Minimum relevance to include
    prioritize_matched: bool = True  # Prioritize matched skills over unmatched


def _calculate_skill_relevance_score(
    skill: Skill,
    matched_skills: list[SkillMatch],
    missing_required: list[str],
    missing_preferred: list[str],
) -> float:
    """
    Calculate relevance score for a skill based on job match.

    Args:
        skill: Skill to score
        matched_skills: List of matched skills from MatchResult
        missing_required: Required skills user doesn't have
        missing_preferred: Preferred skills user doesn't have

    Returns:
        Relevance score (0-100)

    Examples:
        >>> score = _calculate_skill_relevance_score(skill, matched, [], [])
        >>> 0 <= score <= 100
        True
    """
    skill_name_lower = skill.name.lower()

    # Check if skill matched a required skill
    for match in matched_skills:
        if match.skill.lower() == skill_name_lower and match.category == "required":
            return 100.0  # Required match - highest priority

    # Check if skill matched a preferred skill
    for match in matched_skills:
        if match.skill.lower() == skill_name_lower and match.category == "preferred":
            return 80.0  # Preferred match - high priority

    # Check if skill matched any job skill
    for match in matched_skills:
        if match.skill.lower() == skill_name_lower and match.matched:
            return 60.0  # General match - medium priority

    # Skill not mentioned in job - low relevance
    return 20.0


def optimize_skills(
    user_profile: UserProfile,
    match_result: MatchResult,
    strategy: SkillsDisplayStrategy | None = None,
) -> list[Skill]:
    """
    Optimize skills list based on job relevance.

    This function implements Phase 4.2 - Skills Optimization.
    It reorders and optionally filters skills to emphasize job-relevant skills.

    Key features:
    - Reorders skills by relevance to target job
    - Groups skills by category
    - Supports display strategies (show all vs relevant only)
    - Preserves truthfulness (no skill addition or modification)
    - Maintains original proficiency levels and metadata

    Args:
        user_profile: User's original profile
        match_result: Match analysis with skill matches
        strategy: Display strategy configuration (default: group by category, show all)

    Returns:
        List of Skill objects reordered by relevance

    Raises:
        ValueError: If any skill would be fabricated

    Examples:
        >>> skills = optimize_skills(profile, match_result)
        >>> skills[0].name  # Most relevant skill first
        'Python'
        >>> skills[0].proficiency  # Original proficiency preserved
        'Expert'
    """
    if strategy is None:
        strategy = SkillsDisplayStrategy()

    logger.info(
        f"Optimizing skills with strategy: show_all={strategy.show_all}, "
        f"top_n={strategy.top_n}, group_by_category={strategy.group_by_category}"
    )

    # Score all skills
    scored_skills: list[tuple[Skill, float]] = []

    for skill in user_profile.skills:
        relevance = _calculate_skill_relevance_score(
            skill,
            match_result.matched_skills,
            match_result.missing_required_skills,
            match_result.missing_preferred_skills,
        )

        # Apply filters
        if not strategy.show_all and relevance < strategy.min_relevance_score:
            continue

        scored_skills.append((skill, relevance))

    # Sort by relevance (descending)
    if strategy.prioritize_matched:
        scored_skills.sort(key=lambda x: x[1], reverse=True)

    # Apply top N limit
    if strategy.top_n is not None:
        scored_skills = scored_skills[: strategy.top_n]

    # Group by category if requested
    if strategy.group_by_category:
        optimized_skills = _group_skills_by_category(scored_skills)
    else:
        optimized_skills = [skill for skill, _ in scored_skills]

    # Validate truthfulness
    _validate_skill_truthfulness(user_profile, optimized_skills)

    logger.info(
        f"Optimized {len(optimized_skills)}/{len(user_profile.skills)} skills"
    )
    return optimized_skills


def _group_skills_by_category(
    scored_skills: list[tuple[Skill, float]]
) -> list[Skill]:
    """
    Group skills by category while maintaining relevance order within categories.

    Args:
        scored_skills: List of (skill, score) tuples

    Returns:
        List of skills grouped by category

    Examples:
        >>> skills = _group_skills_by_category(scored)
        >>> [s.category for s in skills]
        ['Programming', 'Programming', 'DevOps', 'DevOps']
    """
    # Group by category
    categories: dict[str, list[tuple[Skill, float]]] = {}
    for skill, score in scored_skills:
        category = skill.category or "General"
        if category not in categories:
            categories[category] = []
        categories[category].append((skill, score))

    # Calculate average score per category for ordering categories
    category_avg_scores: dict[str, float] = {}
    for category, skills_in_category in categories.items():
        avg_score = sum(score for _, score in skills_in_category) / len(
            skills_in_category
        )
        category_avg_scores[category] = avg_score

    # Sort categories by average score
    sorted_categories = sorted(
        categories.keys(), key=lambda c: category_avg_scores[c], reverse=True
    )

    # Build final list: categories in order, skills within category by relevance
    result: list[Skill] = []
    for category in sorted_categories:
        # Already sorted by relevance within category from parent function
        category_skills = [skill for skill, _ in categories[category]]
        result.extend(category_skills)

    return result


def _validate_skill_truthfulness(
    original_profile: UserProfile,
    optimized_skills: list[Skill],
) -> None:
    """
    Validate that no skills were fabricated or modified.

    Ensures all skills in optimized list exist in original profile
    with same name and proficiency.

    Args:
        original_profile: Original user profile
        optimized_skills: Optimized skills to validate

    Raises:
        ValueError: If any skill is fabricated or modified

    Examples:
        >>> _validate_skill_truthfulness(profile, skills)
        # Raises ValueError if validation fails
    """
    # Build lookup of original skills: (name, proficiency) -> skill
    original_skills_map: dict[tuple[str, str | None], Skill] = {}
    for skill in original_profile.skills:
        key = (skill.name.lower(), skill.proficiency)
        original_skills_map[key] = skill

    # Validate each optimized skill
    for skill in optimized_skills:
        key = (skill.name.lower(), skill.proficiency)

        if key not in original_skills_map:
            # Check if skill name exists with different proficiency
            name_exists = any(
                s.name.lower() == skill.name.lower()
                for s in original_profile.skills
            )

            if name_exists:
                raise ValueError(
                    f"Skill proficiency modified: '{skill.name}' "
                    f"proficiency changed from original"
                )
            else:
                raise ValueError(
                    f"Fabricated skill detected: '{skill.name}' "
                    f"not found in original profile"
                )

    logger.debug("Skill truthfulness validation passed")


def get_skill_statistics(
    original_profile: UserProfile,
    optimized_skills: list[Skill],
    match_result: MatchResult,
) -> dict[str, Any]:
    """
    Get statistics about skill optimization.

    Args:
        original_profile: Original profile
        optimized_skills: Optimized skills list
        match_result: Match result with skill matches

    Returns:
        Dictionary with optimization statistics

    Examples:
        >>> stats = get_skill_statistics(profile, skills, match)
        >>> stats["total_original"]
        15
        >>> stats["total_displayed"]
        10
        >>> stats["matched_skills_shown"]
        8
    """
    total_original = len(original_profile.skills)
    total_displayed = len(optimized_skills)

    # Count matched skills in optimized list
    matched_skill_names = {
        match.skill.lower()
        for match in match_result.matched_skills
        if match.matched
    }
    matched_shown = sum(
        1 for skill in optimized_skills if skill.name.lower() in matched_skill_names
    )

    # Count required vs preferred
    required_shown = sum(
        1
        for skill in optimized_skills
        if any(
            match.skill.lower() == skill.name.lower() and match.category == "required"
            for match in match_result.matched_skills
        )
    )

    preferred_shown = sum(
        1
        for skill in optimized_skills
        if any(
            match.skill.lower() == skill.name.lower() and match.category == "preferred"
            for match in match_result.matched_skills
        )
    )

    # Count categories
    categories = {skill.category for skill in optimized_skills}

    return {
        "total_original": total_original,
        "total_displayed": total_displayed,
        "reduction_rate": (
            1.0 - (total_displayed / total_original) if total_original > 0 else 0.0
        ),
        "matched_skills_shown": matched_shown,
        "required_skills_shown": required_shown,
        "preferred_skills_shown": preferred_shown,
        "categories_count": len(categories),
    }


# ============================================================================
# Phase 4.3: Resume Customization Logic
# ============================================================================


@dataclass
class CustomizationPreferences:
    """User preferences for resume customization."""

    achievements_per_role: int = 3  # Number of achievements per experience
    max_skills: int | None = None  # Maximum skills to show (None = all)
    template: str = "modern"  # Template to use (modern, classic, ats)
    include_summary: bool = True  # Include customized summary
    skills_strategy: SkillsDisplayStrategy | None = None  # Custom skills strategy
    achievement_strategy: AchievementSelection | None = None  # Custom achievement strategy


def customize_resume(
    user_profile: UserProfile,
    match_result: MatchResult,
    preferences: CustomizationPreferences | None = None,
    customized_summary: str | None = None,
) -> CustomizedResume:
    """
    Create a customized resume for a specific job.

    This function implements Phase 4.3 - Resume Customization Logic.
    It combines achievement reordering, skills optimization, and summary
    to create a complete customized resume.

    Key features:
    - Combines all customization components (achievements, skills, summary)
    - Applies user preferences
    - Generates metadata and change tracking
    - Preserves truthfulness (no fabrication)
    - Creates unique customization ID

    Args:
        user_profile: User's original profile
        match_result: Match analysis result
        preferences: Customization preferences (default: standard settings)
        customized_summary: Optional pre-generated summary

    Returns:
        CustomizedResume object with all customizations applied

    Raises:
        ValueError: If any customization violates truthfulness

    Examples:
        >>> prefs = CustomizationPreferences(achievements_per_role=2, max_skills=8)
        >>> customized = customize_resume(profile, match_result, prefs)
        >>> len(customized.selected_experiences[0].achievements) <= 2
        True
        >>> len(customized.reordered_skills) <= 8
        True
    """
    import uuid
    from datetime import datetime, timezone

    if preferences is None:
        preferences = CustomizationPreferences()

    logger.info(
        f"Customizing resume for job {match_result.job_id} "
        f"with preferences: achievements_per_role={preferences.achievements_per_role}, "
        f"max_skills={preferences.max_skills}"
    )

    # Phase 4.1: Reorder achievements
    achievement_strategy = preferences.achievement_strategy or AchievementSelection(
        top_n=preferences.achievements_per_role,
        ensure_diversity=True,
        prioritize_leadership=True,
        include_metrics=True,
    )

    selected_experiences = reorder_achievements(
        user_profile, match_result, achievement_strategy
    )

    # Phase 4.2: Optimize skills
    skills_strategy = preferences.skills_strategy or SkillsDisplayStrategy(
        show_all=False if preferences.max_skills else True,
        top_n=preferences.max_skills,
        group_by_category=True,
        min_relevance_score=50.0 if preferences.max_skills else 0.0,
        prioritize_matched=True,
    )

    reordered_skills = optimize_skills(user_profile, match_result, skills_strategy)

    # Generate metadata
    customization_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Track changes
    changes_log = _generate_changes_log(
        user_profile, selected_experiences, reordered_skills
    )

    # Build metadata
    metadata = {
        "changes_log": changes_log,
        "original_achievement_count": sum(
            len(exp.achievements) for exp in user_profile.experiences
        ),
        "customized_achievement_count": sum(
            len(exp.achievements) for exp in selected_experiences
        ),
        "original_skill_count": len(user_profile.skills),
        "customized_skill_count": len(reordered_skills),
        "match_score": match_result.overall_score,
        "preferences": {
            "achievements_per_role": preferences.achievements_per_role,
            "max_skills": preferences.max_skills,
            "template": preferences.template,
        },
    }

    # Create customized resume
    customized_resume = CustomizedResume(
        profile_id=match_result.profile_id,
        job_id=match_result.job_id,
        match_result=match_result,
        customized_summary=customized_summary,
        selected_experiences=selected_experiences,
        reordered_skills=reordered_skills,
        template=preferences.template,
        metadata=metadata,
        customization_id=customization_id,
        created_at=created_at,
    )

    # Validate no data loss
    _validate_no_data_loss(user_profile, customized_resume)

    logger.info(
        f"Resume customized successfully: {customization_id} "
        f"({len(selected_experiences)} experiences, {len(reordered_skills)} skills)"
    )

    return customized_resume


def _generate_changes_log(
    original_profile: UserProfile,
    customized_experiences: list[Experience],
    customized_skills: list[Skill],
) -> dict[str, Any]:
    """
    Generate a log of changes made during customization.

    Args:
        original_profile: Original user profile
        customized_experiences: Customized experiences
        customized_skills: Customized skills

    Returns:
        Dictionary with change tracking information

    Examples:
        >>> log = _generate_changes_log(profile, experiences, skills)
        >>> log["achievements_removed"]
        16
        >>> log["skills_reordered"]
        True
    """
    original_achievement_count = sum(
        len(exp.achievements) for exp in original_profile.experiences
    )
    customized_achievement_count = sum(
        len(exp.achievements) for exp in customized_experiences
    )

    # Track achievement changes per experience
    achievement_changes = []
    for orig_exp, custom_exp in zip(
        original_profile.experiences, customized_experiences, strict=True
    ):
        if len(orig_exp.achievements) != len(custom_exp.achievements):
            achievement_changes.append(
                {
                    "company": orig_exp.company,
                    "title": orig_exp.title,
                    "original_count": len(orig_exp.achievements),
                    "customized_count": len(custom_exp.achievements),
                    "removed_count": len(orig_exp.achievements)
                    - len(custom_exp.achievements),
                }
            )

    # Check if skills were reordered
    skills_reordered = False
    if len(customized_skills) == len(original_profile.skills):
        # Same count - check if order changed
        for orig, custom in zip(
            original_profile.skills, customized_skills, strict=True
        ):
            if orig.name != custom.name:
                skills_reordered = True
                break
    else:
        skills_reordered = True  # Different count means definitely reordered

    return {
        "achievements_removed": original_achievement_count
        - customized_achievement_count,
        "achievements_kept": customized_achievement_count,
        "achievement_changes_by_experience": achievement_changes,
        "skills_removed": len(original_profile.skills) - len(customized_skills),
        "skills_kept": len(customized_skills),
        "skills_reordered": skills_reordered,
        "experiences_count": len(customized_experiences),
    }


def _validate_no_data_loss(
    original_profile: UserProfile, customized_resume: CustomizedResume
) -> None:
    """
    Validate that no critical data was lost during customization.

    Ensures all selected achievements and skills exist in original profile.

    Args:
        original_profile: Original user profile
        customized_resume: Customized resume to validate

    Raises:
        ValueError: If data loss or fabrication detected

    Examples:
        >>> _validate_no_data_loss(profile, customized)
        # Raises ValueError if validation fails
    """
    # Validate achievements truthfulness
    _validate_achievement_truthfulness(
        original_profile, customized_resume.selected_experiences
    )

    # Validate skills truthfulness
    _validate_skill_truthfulness(original_profile, customized_resume.reordered_skills)

    # Validate profile and job IDs match
    if customized_resume.profile_id != customized_resume.match_result.profile_id:
        raise ValueError("Profile ID mismatch in customized resume")

    if customized_resume.job_id != customized_resume.match_result.job_id:
        raise ValueError("Job ID mismatch in customized resume")

    # Validate experiences count matches
    if len(customized_resume.selected_experiences) != len(
        original_profile.experiences
    ):
        raise ValueError(
            f"Experience count mismatch: original has {len(original_profile.experiences)}, "
            f"customized has {len(customized_resume.selected_experiences)}"
        )

    logger.debug("Data integrity validation passed - no data loss detected")


def get_customization_summary(customized_resume: CustomizedResume) -> dict[str, Any]:
    """
    Get a summary of the customization.

    Args:
        customized_resume: Customized resume

    Returns:
        Dictionary with customization summary

    Examples:
        >>> summary = get_customization_summary(customized)
        >>> summary["match_score"]
        85
        >>> summary["template"]
        'modern'
    """
    metadata = customized_resume.metadata
    changes_log = metadata.get("changes_log", {})

    return {
        "customization_id": customized_resume.customization_id,
        "created_at": customized_resume.created_at,
        "match_score": customized_resume.match_result.overall_score,
        "template": customized_resume.template,
        "has_custom_summary": customized_resume.customized_summary is not None,
        "experiences_count": len(customized_resume.selected_experiences),
        "achievements_count": sum(
            len(exp.achievements) for exp in customized_resume.selected_experiences
        ),
        "skills_count": len(customized_resume.reordered_skills),
        "changes": {
            "achievements_removed": changes_log.get("achievements_removed", 0),
            "skills_removed": changes_log.get("skills_removed", 0),
            "skills_reordered": changes_log.get("skills_reordered", False),
        },
        "preferences": metadata.get("preferences", {}),
    }
