"""
Tests for resume customization logic.

Tests Phase 4.1 - Achievement Reordering functionality.
"""


import pytest

from resume_customizer.core.customizer import (
    AchievementSelection,
    CustomizationPreferences,
    SkillsDisplayStrategy,
    _calculate_diversity_score,
    _calculate_skill_relevance_score,
    _generate_changes_log,
    _group_skills_by_category,
    _has_leadership_indicators,
    _validate_achievement_truthfulness,
    _validate_no_data_loss,
    _validate_skill_truthfulness,
    customize_resume,
    get_achievement_statistics,
    get_customization_summary,
    get_skill_statistics,
    optimize_skills,
    reorder_achievements,
)
from resume_customizer.core.models import (
    Achievement,
    ContactInfo,
    CustomizedResume,
    Experience,
    MatchBreakdown,
    MatchResult,
    Skill,
    SkillMatch,
    UserProfile,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_profile() -> UserProfile:
    """Create a sample user profile with multiple experiences."""
    return UserProfile(
        name="Jane Developer",
        contact=ContactInfo(
            email="jane@example.com",
            phone="555-0100",
        ),
        summary="Experienced software engineer with 5 years of experience",
        experiences=[
            Experience(
                company="Tech Corp",
                title="Senior Software Engineer",
                start_date="2022-01",
                end_date="Present",
                achievements=[
                    Achievement(
                        text="Led team of 5 engineers to deliver critical microservices platform",
                        technologies=["Python", "Docker", "Kubernetes"],
                        metrics=["5 engineers", "3 months"],
                    ),
                    Achievement(
                        text="Reduced API latency by 40% through caching optimization",
                        technologies=["Redis", "Python"],
                        metrics=["40%"],
                    ),
                    Achievement(
                        text="Implemented CI/CD pipeline reducing deployment time by 60%",
                        technologies=["GitLab CI", "Docker"],
                        metrics=["60%"],
                    ),
                ],
            ),
            Experience(
                company="StartupXYZ",
                title="Software Engineer",
                start_date="2020-01",
                end_date="2021-12",
                achievements=[
                    Achievement(
                        text="Developed real-time analytics dashboard using React and WebSockets",
                        technologies=["React", "WebSockets", "Node.js"],
                    ),
                    Achievement(
                        text="Mentored 2 junior engineers on best practices",
                        metrics=["2 engineers"],
                    ),
                    Achievement(
                        text="Optimized database queries improving response time by 50%",
                        technologies=["PostgreSQL"],
                        metrics=["50%"],
                    ),
                ],
            ),
            Experience(
                company="Consulting Inc",
                title="Junior Developer",
                start_date="2019-06",
                end_date="2019-12",
                achievements=[
                    Achievement(
                        text="Built client portal using Django and React",
                        technologies=["Django", "React"],
                    ),
                    Achievement(
                        text="Fixed critical security vulnerability in authentication system",
                        technologies=["Django"],
                    ),
                ],
            ),
        ],
        skills=[],
        education=[],
    )


@pytest.fixture
def sample_match_result(sample_profile: UserProfile) -> MatchResult:
    """Create a sample match result with ranked achievements."""
    # Collect all achievements with scores
    ranked = [
        # Tech Corp achievements (high scores)
        (sample_profile.experiences[0].achievements[0], 95.0),  # Leadership
        (sample_profile.experiences[0].achievements[1], 85.0),  # Performance
        (sample_profile.experiences[0].achievements[2], 80.0),  # CI/CD
        # StartupXYZ achievements (medium scores)
        (sample_profile.experiences[1].achievements[0], 75.0),  # Dashboard
        (sample_profile.experiences[1].achievements[1], 70.0),  # Mentoring
        (sample_profile.experiences[1].achievements[2], 65.0),  # Database
        # Consulting Inc achievements (lower scores)
        (sample_profile.experiences[2].achievements[0], 45.0),  # Portal
        (sample_profile.experiences[2].achievements[1], 40.0),  # Security
    ]

    return MatchResult(
        profile_id="profile-1",
        job_id="job-1",
        overall_score=85,
        breakdown=MatchBreakdown(
            technical_skills_score=90.0,
            experience_score=85.0,
            domain_score=80.0,
            keyword_coverage_score=75.0,
            total_score=85.0,
        ),
        matched_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        ranked_achievements=ranked,
    )


# ============================================================================
# Tests for Helper Functions
# ============================================================================


def test_has_leadership_indicators_positive():
    """Test detection of leadership keywords in achievements."""
    leadership_achievements = [
        Achievement(text="Led team of 5 engineers"),
        Achievement(text="Managed cross-functional project"),
        Achievement(text="Mentored junior developers"),
        Achievement(text="Coordinated stakeholder meetings"),
        Achievement(text="Spearheaded migration to microservices"),
        Achievement(text="Established best practices for team"),
    ]

    for ach in leadership_achievements:
        assert _has_leadership_indicators(ach), f"Should detect leadership in: {ach.text}"


def test_has_leadership_indicators_negative():
    """Test that non-leadership achievements are not flagged."""
    non_leadership = [
        Achievement(text="Implemented new feature using React"),
        Achievement(text="Fixed bug in authentication system"),
        Achievement(text="Optimized database queries"),
        Achievement(text="Wrote unit tests for API endpoints"),
    ]

    for ach in non_leadership:
        assert not _has_leadership_indicators(ach), f"Should not detect leadership in: {ach.text}"


def test_calculate_diversity_score_new_company_and_title():
    """Test diversity score for completely new company and title."""
    ach = Achievement(text="Test achievement")
    exp = Experience(
        company="New Corp",
        title="New Role",
        start_date="2020-01",
        end_date="2021-01",
    )

    score = _calculate_diversity_score(ach, exp, set(), set())
    assert score == 1.0, "Should get full bonus for new company and title"


def test_calculate_diversity_score_existing_company():
    """Test diversity score for existing company but new title."""
    ach = Achievement(text="Test achievement")
    exp = Experience(
        company="Tech Corp",
        title="New Role",
        start_date="2020-01",
        end_date="2021-01",
    )

    score = _calculate_diversity_score(ach, exp, {"Tech Corp"}, set())
    assert score == 0.5, "Should get half bonus for new title only"


def test_calculate_diversity_score_existing_both():
    """Test diversity score for existing company and title."""
    ach = Achievement(text="Test achievement")
    exp = Experience(
        company="Tech Corp",
        title="Engineer",
        start_date="2020-01",
        end_date="2021-01",
    )

    score = _calculate_diversity_score(ach, exp, {"Tech Corp"}, {"Engineer"})
    assert score == 0.0, "Should get no bonus for existing company and title"


# ============================================================================
# Tests for Truthfulness Validation
# ============================================================================


def test_validate_truthfulness_valid(sample_profile: UserProfile):
    """Test validation passes for legitimate achievements."""
    # Use subset of original achievements
    customized = [
        Experience(
            company=sample_profile.experiences[0].company,
            title=sample_profile.experiences[0].title,
            start_date=sample_profile.experiences[0].start_date,
            end_date=sample_profile.experiences[0].end_date,
            achievements=sample_profile.experiences[0].achievements[:2],
        )
    ]

    # Should not raise
    _validate_achievement_truthfulness(sample_profile, customized)


def test_validate_truthfulness_fabricated(sample_profile: UserProfile):
    """Test validation fails for fabricated achievements."""
    fabricated = Achievement(text="This achievement was never in the original profile")

    customized = [
        Experience(
            company="Tech Corp",
            title="Engineer",
            start_date="2020-01",
            end_date="2021-01",
            achievements=[fabricated],
        )
    ]

    with pytest.raises(ValueError, match="Fabricated achievement detected"):
        _validate_achievement_truthfulness(sample_profile, customized)


def test_validate_truthfulness_modified_text(sample_profile: UserProfile):
    """Test validation fails for modified achievement text."""
    # Modified version of original achievement
    modified = Achievement(
        text="Led team of 10 engineers to deliver critical microservices platform"  # Changed 5 to 10
    )

    customized = [
        Experience(
            company="Tech Corp",
            title="Engineer",
            start_date="2020-01",
            end_date="2021-01",
            achievements=[modified],
        )
    ]

    with pytest.raises(ValueError, match="Fabricated achievement detected"):
        _validate_achievement_truthfulness(sample_profile, customized)


# ============================================================================
# Tests for Achievement Reordering
# ============================================================================


def test_reorder_achievements_default_strategy(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test achievement reordering with default strategy (top 3 per role)."""
    result = reorder_achievements(sample_profile, sample_match_result)

    assert len(result) == 3, "Should preserve all 3 experiences"

    # Check first experience has top 3 achievements
    assert len(result[0].achievements) <= 3, "Should have at most 3 achievements"

    # Check achievements are ordered by relevance
    if len(result[0].achievements) > 1:
        scores = [ach.relevance_score for ach in result[0].achievements]
        assert scores == sorted(scores, reverse=True), "Should be ordered by score"


def test_reorder_achievements_top_n_strategy(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test achievement reordering with custom top N strategy."""
    strategy = AchievementSelection(top_n=2)
    result = reorder_achievements(sample_profile, sample_match_result, strategy)

    for exp in result:
        if exp.achievements:
            assert len(exp.achievements) <= 2, "Should have at most 2 achievements per role"


def test_reorder_achievements_preserves_experience_metadata(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test that experience metadata is preserved during reordering."""
    result = reorder_achievements(sample_profile, sample_match_result)

    for i, original_exp in enumerate(sample_profile.experiences):
        customized_exp = result[i]
        assert customized_exp.company == original_exp.company
        assert customized_exp.title == original_exp.title
        assert customized_exp.start_date == original_exp.start_date
        assert customized_exp.end_date == original_exp.end_date
        assert customized_exp.location == original_exp.location
        assert customized_exp.work_mode == original_exp.work_mode


def test_reorder_achievements_leadership_bonus(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test that leadership achievements get priority boost."""
    strategy = AchievementSelection(prioritize_leadership=True, top_n=1)
    result = reorder_achievements(sample_profile, sample_match_result, strategy)

    # First experience should select the leadership achievement
    top_achievement = result[0].achievements[0]
    assert "Led team" in top_achievement.text, "Should prioritize leadership achievement"


def test_reorder_achievements_min_relevance_filter(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test filtering by minimum relevance score."""
    strategy = AchievementSelection(min_relevance_score=70.0, top_n=10)
    result = reorder_achievements(sample_profile, sample_match_result, strategy)

    # Should exclude low-scoring achievements from Consulting Inc
    consulting_exp = result[2]  # Third experience
    assert len(consulting_exp.achievements) == 0, "Should filter out low-scoring achievements"


def test_reorder_achievements_no_ranked_achievements(sample_profile: UserProfile):
    """Test handling of match result with no ranked achievements."""
    empty_match = MatchResult(
        profile_id="profile-1",
        job_id="job-1",
        overall_score=50,
        breakdown=MatchBreakdown(
            technical_skills_score=50.0,
            experience_score=50.0,
            domain_score=50.0,
            keyword_coverage_score=50.0,
            total_score=50.0,
        ),
        matched_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        ranked_achievements=[],  # Empty!
    )

    result = reorder_achievements(sample_profile, empty_match)

    # Should return original experiences unchanged
    assert result == sample_profile.experiences


def test_reorder_achievements_relevance_scores_set(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test that relevance scores are properly set on achievements."""
    result = reorder_achievements(sample_profile, sample_match_result)

    for exp in result:
        for ach in exp.achievements:
            assert ach.relevance_score is not None, "Should have relevance score"
            assert ach.relevance_score >= 0, "Score should be non-negative"


def test_reorder_achievements_diversity_ensures_multiple_companies(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test diversity strategy represents multiple companies."""
    strategy = AchievementSelection(ensure_diversity=True, top_n=1)
    result = reorder_achievements(sample_profile, sample_match_result, strategy)

    # Count how many companies are represented
    companies_with_achievements = {
        exp.company for exp in result if exp.achievements
    }

    # Should have achievements from multiple companies due to diversity bonus
    assert len(companies_with_achievements) >= 2, "Should represent multiple companies"


def test_reorder_achievements_metrics_bonus(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test that achievements with metrics get priority boost."""
    strategy = AchievementSelection(include_metrics=True, top_n=3)
    result = reorder_achievements(sample_profile, sample_match_result, strategy)

    # Most selected achievements should have metrics
    achievements_with_metrics = 0
    total_achievements = 0

    for exp in result:
        for ach in exp.achievements:
            total_achievements += 1
            if ach.metrics:
                achievements_with_metrics += 1

    if total_achievements > 0:
        metrics_ratio = achievements_with_metrics / total_achievements
        assert metrics_ratio >= 0.6, "Most achievements should have metrics"


def test_reorder_achievements_empty_experience_list():
    """Test handling of profile with no experiences."""
    empty_profile = UserProfile(
        name="Test User",
        contact=ContactInfo(email="test@example.com"),
        summary="Summary",
        experiences=[],
        skills=[],
        education=[],
    )

    match_result = MatchResult(
        profile_id="profile-1",
        job_id="job-1",
        overall_score=0,
        breakdown=MatchBreakdown(
            technical_skills_score=0.0,
            experience_score=0.0,
            domain_score=0.0,
            keyword_coverage_score=0.0,
            total_score=0.0,
        ),
        matched_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        ranked_achievements=[],
    )

    result = reorder_achievements(empty_profile, match_result)
    assert result == [], "Should return empty list for empty profile"


# ============================================================================
# Tests for Statistics
# ============================================================================


def test_get_achievement_statistics(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test achievement statistics calculation."""
    customized = reorder_achievements(sample_profile, sample_match_result)
    stats = get_achievement_statistics(sample_profile, customized)

    assert "total_original" in stats
    assert "total_selected" in stats
    assert "selection_rate" in stats
    assert "companies_original" in stats
    assert "companies_represented" in stats
    assert "diversity_rate" in stats

    # Verify counts
    assert stats["total_original"] == 8, "Should count all original achievements"
    assert stats["total_selected"] <= stats["total_original"], "Can't select more than original"
    assert 0.0 <= stats["selection_rate"] <= 1.0, "Rate should be between 0 and 1"
    assert 0.0 <= stats["diversity_rate"] <= 1.0, "Diversity rate should be between 0 and 1"


def test_get_achievement_statistics_empty():
    """Test statistics with empty profiles."""
    empty_profile = UserProfile(
        name="Test User",
        contact=ContactInfo(email="test@example.com"),
        summary="Summary",
        experiences=[],
        skills=[],
        education=[],
    )

    stats = get_achievement_statistics(empty_profile, [])

    assert stats["total_original"] == 0
    assert stats["total_selected"] == 0
    assert stats["selection_rate"] == 0.0
    assert stats["diversity_rate"] == 0.0


# ============================================================================
# Integration Tests
# ============================================================================


def test_end_to_end_achievement_reordering(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test complete achievement reordering workflow."""
    # Apply reordering with comprehensive strategy
    strategy = AchievementSelection(
        top_n=2,
        ensure_diversity=True,
        prioritize_leadership=True,
        include_metrics=True,
        min_relevance_score=50.0,
    )

    result = reorder_achievements(sample_profile, sample_match_result, strategy)

    # Validate structure
    assert len(result) == len(sample_profile.experiences)

    # Validate truthfulness (should not raise)
    _validate_achievement_truthfulness(sample_profile, result)

    # Validate statistics
    stats = get_achievement_statistics(sample_profile, result)
    assert stats["total_selected"] <= stats["total_original"]
    assert stats["companies_represented"] >= 1

    # Validate all achievements have scores
    for exp in result:
        for ach in exp.achievements:
            assert ach.relevance_score is not None
            assert ach.relevance_score >= 50.0  # Min threshold


def test_strategy_combinations(
    sample_profile: UserProfile,
    sample_match_result: MatchResult,
):
    """Test various strategy combinations work correctly."""
    strategies = [
        AchievementSelection(top_n=1),
        AchievementSelection(top_n=5, ensure_diversity=False),
        AchievementSelection(prioritize_leadership=False),
        AchievementSelection(include_metrics=False),
        AchievementSelection(min_relevance_score=80.0),
        AchievementSelection(
            top_n=2,
            ensure_diversity=True,
            prioritize_leadership=True,
            include_metrics=True,
        ),
    ]

    for strategy in strategies:
        result = reorder_achievements(sample_profile, sample_match_result, strategy)
        # Should not raise exceptions
        assert isinstance(result, list)
        # Truthfulness should always be preserved
        _validate_achievement_truthfulness(sample_profile, result)


# ============================================================================
# Tests for Skills Optimization (Phase 4.2)
# ============================================================================


@pytest.fixture
def sample_profile_with_skills() -> UserProfile:
    """Create a profile with diverse skills."""
    return UserProfile(
        name="John Developer",
        contact=ContactInfo(email="john@example.com"),
        summary="Full stack developer",
        experiences=[],
        education=[],
        skills=[
            Skill(name="Python", category="Programming", proficiency="Expert", years=5),
            Skill(name="JavaScript", category="Programming", proficiency="Advanced", years=4),
            Skill(name="React", category="Frontend", proficiency="Advanced", years=3),
            Skill(name="Docker", category="DevOps", proficiency="Intermediate", years=2),
            Skill(name="Kubernetes", category="DevOps", proficiency="Basic", years=1),
            Skill(name="PostgreSQL", category="Database", proficiency="Advanced", years=4),
            Skill(name="MongoDB", category="Database", proficiency="Intermediate", years=2),
            Skill(name="AWS", category="Cloud", proficiency="Advanced", years=3),
            Skill(name="Git", category="Tools", proficiency="Expert", years=5),
            Skill(name="Agile", category="Methodology", proficiency="Advanced"),
        ],
    )


@pytest.fixture
def sample_match_with_skills() -> MatchResult:
    """Create a match result with skill matches."""
    return MatchResult(
        profile_id="profile-1",
        job_id="job-1",
        overall_score=80,
        breakdown=MatchBreakdown(
            technical_skills_score=85.0,
            experience_score=80.0,
            domain_score=75.0,
            keyword_coverage_score=70.0,
            total_score=80.0,
        ),
        matched_skills=[
            SkillMatch(skill="Python", matched=True, category="required", user_proficiency="Expert"),
            SkillMatch(skill="JavaScript", matched=True, category="required", user_proficiency="Advanced"),
            SkillMatch(skill="React", matched=True, category="preferred", user_proficiency="Advanced"),
            SkillMatch(skill="Docker", matched=True, category="preferred", user_proficiency="Intermediate"),
            SkillMatch(skill="AWS", matched=True, category="preferred", user_proficiency="Advanced"),
            SkillMatch(skill="TypeScript", matched=False, category="required"),  # Missing
            SkillMatch(skill="GraphQL", matched=False, category="preferred"),  # Missing
        ],
        missing_required_skills=["TypeScript"],
        missing_preferred_skills=["GraphQL"],
        ranked_achievements=[],
    )


# Tests for skill relevance scoring

def test_calculate_skill_relevance_required_match():
    """Test scoring for skills matching required job skills."""
    skill = Skill(name="Python", category="Programming")
    matched = [SkillMatch(skill="Python", matched=True, category="required")]

    score = _calculate_skill_relevance_score(skill, matched, [], [])
    assert score == 100.0, "Required match should get highest score"


def test_calculate_skill_relevance_preferred_match():
    """Test scoring for skills matching preferred job skills."""
    skill = Skill(name="React", category="Frontend")
    matched = [SkillMatch(skill="React", matched=True, category="preferred")]

    score = _calculate_skill_relevance_score(skill, matched, [], [])
    assert score == 80.0, "Preferred match should get high score"


def test_calculate_skill_relevance_general_match():
    """Test scoring for general skill matches."""
    skill = Skill(name="Git", category="Tools")
    matched = [SkillMatch(skill="Git", matched=True, category="general")]

    score = _calculate_skill_relevance_score(skill, matched, [], [])
    assert score == 60.0, "General match should get medium score"


def test_calculate_skill_relevance_no_match():
    """Test scoring for skills not in job description."""
    skill = Skill(name="PHP", category="Programming")
    matched = [SkillMatch(skill="Python", matched=True, category="required")]

    score = _calculate_skill_relevance_score(skill, matched, [], [])
    assert score == 20.0, "Non-matched skill should get low score"


# Tests for skill grouping

def test_group_skills_by_category():
    """Test skills are grouped by category and sorted by relevance."""
    scored_skills = [
        (Skill(name="Python", category="Programming"), 100.0),
        (Skill(name="React", category="Frontend"), 80.0),
        (Skill(name="JavaScript", category="Programming"), 90.0),
        (Skill(name="Docker", category="DevOps"), 70.0),
    ]

    result = _group_skills_by_category(scored_skills)

    # Should group by category, with highest avg category first
    assert result[0].category == "Programming"  # Avg score: 95
    assert result[1].category == "Programming"
    assert result[2].category == "Frontend"  # Score: 80
    assert result[3].category == "DevOps"  # Score: 70


def test_group_skills_maintains_order_within_category():
    """Test skills within same category maintain relevance order."""
    scored_skills = [
        (Skill(name="Python", category="Programming"), 100.0),
        (Skill(name="JavaScript", category="Programming"), 90.0),
        (Skill(name="Ruby", category="Programming"), 80.0),
    ]

    result = _group_skills_by_category(scored_skills)

    assert result[0].name == "Python"
    assert result[1].name == "JavaScript"
    assert result[2].name == "Ruby"


# Tests for skill truthfulness validation

def test_validate_skill_truthfulness_valid(sample_profile_with_skills: UserProfile):
    """Test validation passes for legitimate skills."""
    valid_skills = sample_profile_with_skills.skills[:5]
    _validate_skill_truthfulness(sample_profile_with_skills, valid_skills)


def test_validate_skill_truthfulness_fabricated(sample_profile_with_skills: UserProfile):
    """Test validation fails for fabricated skills."""
    fabricated = Skill(name="Haskell", category="Programming", proficiency="Expert")

    with pytest.raises(ValueError, match="Fabricated skill detected"):
        _validate_skill_truthfulness(sample_profile_with_skills, [fabricated])


def test_validate_skill_truthfulness_modified_proficiency(sample_profile_with_skills: UserProfile):
    """Test validation fails when proficiency is changed."""
    # Python is Expert in original, change to Basic
    modified = Skill(name="Python", category="Programming", proficiency="Basic")

    with pytest.raises(ValueError, match="Skill proficiency modified"):
        _validate_skill_truthfulness(sample_profile_with_skills, [modified])


# Tests for optimize_skills function

def test_optimize_skills_default_strategy(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test skill optimization with default strategy."""
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills)

    # Should return all skills (show_all=False but min_relevance=0)
    assert len(result) > 0
    # Should be reordered with matched skills first
    assert result[0].name in ["Python", "JavaScript", "React", "Docker", "AWS"]


def test_optimize_skills_top_n_limit(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test limiting to top N skills."""
    strategy = SkillsDisplayStrategy(top_n=5)
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)

    assert len(result) <= 5, "Should limit to top 5 skills"


def test_optimize_skills_show_all_false_with_min_relevance(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test filtering by minimum relevance."""
    strategy = SkillsDisplayStrategy(show_all=False, min_relevance_score=50.0)
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)

    # Should only include matched skills (score >= 60)
    assert len(result) < len(sample_profile_with_skills.skills)
    # All should be matched skills
    matched_names = {"Python", "JavaScript", "React", "Docker", "AWS"}
    for skill in result:
        assert skill.name in matched_names or skill.name in matched_names


def test_optimize_skills_group_by_category(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test grouping skills by category."""
    strategy = SkillsDisplayStrategy(group_by_category=True)
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)

    # Check that skills from same category are consecutive
    categories_seen = []
    for skill in result:
        if not categories_seen or categories_seen[-1] != skill.category:
            categories_seen.append(skill.category)

    # Each category should appear only once (consecutive grouping)
    assert len(categories_seen) == len(set(categories_seen))


def test_optimize_skills_no_grouping(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test skills optimization without category grouping."""
    strategy = SkillsDisplayStrategy(group_by_category=False)
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)

    # Should be sorted purely by relevance
    # First few should be required skills
    assert result[0].name in ["Python", "JavaScript"]


def test_optimize_skills_preserves_proficiency(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test that skill proficiency levels are preserved."""
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills)

    # Find Python skill in result
    python_skill = next((s for s in result if s.name == "Python"), None)
    assert python_skill is not None
    assert python_skill.proficiency == "Expert", "Should preserve proficiency"

    # Find React skill
    react_skill = next((s for s in result if s.name == "React"), None)
    assert react_skill is not None
    assert react_skill.proficiency == "Advanced", "Should preserve proficiency"


def test_optimize_skills_empty_skills_list():
    """Test handling of profile with no skills."""
    empty_profile = UserProfile(
        name="Test User",
        contact=ContactInfo(email="test@example.com"),
        summary="Summary",
        experiences=[],
        skills=[],
        education=[],
    )

    match_result = MatchResult(
        profile_id="profile-1",
        job_id="job-1",
        overall_score=50,
        breakdown=MatchBreakdown(
            technical_skills_score=0.0,
            experience_score=0.0,
            domain_score=0.0,
            keyword_coverage_score=0.0,
            total_score=0.0,
        ),
        matched_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        ranked_achievements=[],
    )

    result = optimize_skills(empty_profile, match_result)
    assert result == [], "Should return empty list for empty profile"


def test_optimize_skills_prioritize_matched(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test that matched skills are prioritized."""
    strategy = SkillsDisplayStrategy(prioritize_matched=True)
    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)

    # First skills should be matched ones
    matched_skill_names = {"Python", "JavaScript", "React", "Docker", "AWS"}
    if len(result) >= 3:
        assert result[0].name in matched_skill_names
        assert result[1].name in matched_skill_names


# Tests for skill statistics

def test_get_skill_statistics(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test skill statistics calculation."""
    strategy = SkillsDisplayStrategy(top_n=5)
    optimized = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)
    stats = get_skill_statistics(sample_profile_with_skills, optimized, sample_match_with_skills)

    assert "total_original" in stats
    assert "total_displayed" in stats
    assert "reduction_rate" in stats
    assert "matched_skills_shown" in stats
    assert "required_skills_shown" in stats
    assert "preferred_skills_shown" in stats
    assert "categories_count" in stats

    # Verify values
    assert stats["total_original"] == 10
    assert stats["total_displayed"] == 5  # top_n=5
    assert 0.0 <= stats["reduction_rate"] <= 1.0
    assert stats["matched_skills_shown"] >= 0
    assert stats["required_skills_shown"] >= 0


def test_get_skill_statistics_empty():
    """Test statistics with empty skill lists."""
    empty_profile = UserProfile(
        name="Test User",
        contact=ContactInfo(email="test@example.com"),
        summary="Summary",
        experiences=[],
        skills=[],
        education=[],
    )

    match_result = MatchResult(
        profile_id="profile-1",
        job_id="job-1",
        overall_score=0,
        breakdown=MatchBreakdown(
            technical_skills_score=0.0,
            experience_score=0.0,
            domain_score=0.0,
            keyword_coverage_score=0.0,
            total_score=0.0,
        ),
        matched_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        ranked_achievements=[],
    )

    stats = get_skill_statistics(empty_profile, [], match_result)
    assert stats["total_original"] == 0
    assert stats["total_displayed"] == 0
    assert stats["reduction_rate"] == 0.0


# Integration tests

def test_skills_optimization_end_to_end(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test complete skills optimization workflow."""
    strategy = SkillsDisplayStrategy(
        show_all=False,
        top_n=6,
        group_by_category=True,
        min_relevance_score=50.0,
        prioritize_matched=True,
    )

    result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)

    # Validate structure
    assert len(result) <= 6
    assert len(result) > 0

    # Validate truthfulness (should not raise)
    _validate_skill_truthfulness(sample_profile_with_skills, result)

    # Validate statistics
    stats = get_skill_statistics(sample_profile_with_skills, result, sample_match_with_skills)
    assert stats["total_displayed"] <= stats["total_original"]
    assert stats["matched_skills_shown"] >= 1  # Should show matched skills


def test_skills_strategy_combinations(
    sample_profile_with_skills: UserProfile,
    sample_match_with_skills: MatchResult,
):
    """Test various strategy combinations work correctly."""
    strategies = [
        SkillsDisplayStrategy(show_all=True),
        SkillsDisplayStrategy(top_n=3),
        SkillsDisplayStrategy(group_by_category=False),
        SkillsDisplayStrategy(min_relevance_score=70.0),
        SkillsDisplayStrategy(prioritize_matched=False),
        SkillsDisplayStrategy(
            show_all=False,
            top_n=5,
            group_by_category=True,
            min_relevance_score=60.0,
        ),
    ]

    for strategy in strategies:
        result = optimize_skills(sample_profile_with_skills, sample_match_with_skills, strategy)
        # Should not raise exceptions
        assert isinstance(result, list)
        # Truthfulness should always be preserved
        if result:  # Only validate if not empty
            _validate_skill_truthfulness(sample_profile_with_skills, result)


# ============================================================================
# Tests for Resume Customization (Phase 4.3)
# ============================================================================


@pytest.fixture
def complete_profile() -> UserProfile:
    """Create a complete profile with experiences and skills."""
    return UserProfile(
        name="Jane Developer",
        contact=ContactInfo(email="jane@example.com", phone="555-0100"),
        summary="Experienced software engineer with 5 years of experience",
        experiences=[
            Experience(
                company="Tech Corp",
                title="Senior Software Engineer",
                start_date="2022-01",
                end_date="Present",
                achievements=[
                    Achievement(
                        text="Led team of 5 engineers to deliver critical microservices platform",
                        technologies=["Python", "Docker", "Kubernetes"],
                        metrics=["5 engineers", "3 months"],
                    ),
                    Achievement(
                        text="Reduced API latency by 40% through caching optimization",
                        technologies=["Redis", "Python"],
                        metrics=["40%"],
                    ),
                    Achievement(
                        text="Implemented CI/CD pipeline reducing deployment time by 60%",
                        technologies=["GitLab CI", "Docker"],
                        metrics=["60%"],
                    ),
                ],
            ),
            Experience(
                company="StartupXYZ",
                title="Software Engineer",
                start_date="2020-01",
                end_date="2021-12",
                achievements=[
                    Achievement(
                        text="Developed real-time analytics dashboard using React",
                        technologies=["React", "WebSockets"],
                    ),
                    Achievement(
                        text="Mentored 2 junior engineers on best practices",
                        metrics=["2 engineers"],
                    ),
                ],
            ),
        ],
        skills=[
            Skill(name="Python", category="Programming", proficiency="Expert", years=5),
            Skill(name="JavaScript", category="Programming", proficiency="Advanced", years=4),
            Skill(name="React", category="Frontend", proficiency="Advanced", years=3),
            Skill(name="Docker", category="DevOps", proficiency="Intermediate", years=2),
            Skill(name="Redis", category="Database", proficiency="Intermediate", years=2),
        ],
        education=[],
    )


@pytest.fixture
def complete_match_result(complete_profile: UserProfile) -> MatchResult:
    """Create a complete match result."""
    # Collect all achievements with scores
    ranked = [
        (complete_profile.experiences[0].achievements[0], 95.0),  # Leadership
        (complete_profile.experiences[0].achievements[1], 85.0),  # Performance
        (complete_profile.experiences[0].achievements[2], 80.0),  # CI/CD
        (complete_profile.experiences[1].achievements[0], 75.0),  # Dashboard
        (complete_profile.experiences[1].achievements[1], 70.0),  # Mentoring
    ]

    return MatchResult(
        profile_id="profile-123",
        job_id="job-456",
        overall_score=85,
        breakdown=MatchBreakdown(
            technical_skills_score=90.0,
            experience_score=85.0,
            domain_score=80.0,
            keyword_coverage_score=75.0,
            total_score=85.0,
        ),
        matched_skills=[
            SkillMatch(skill="Python", matched=True, category="required", user_proficiency="Expert"),
            SkillMatch(skill="JavaScript", matched=True, category="required", user_proficiency="Advanced"),
            SkillMatch(skill="React", matched=True, category="preferred", user_proficiency="Advanced"),
            SkillMatch(skill="Docker", matched=True, category="preferred", user_proficiency="Intermediate"),
        ],
        missing_required_skills=["TypeScript"],
        missing_preferred_skills=["GraphQL"],
        ranked_achievements=ranked,
    )


# Tests for customize_resume function

def test_customize_resume_default_preferences(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test resume customization with default preferences."""
    result = customize_resume(complete_profile, complete_match_result)

    # Validate structure
    assert isinstance(result, CustomizedResume)
    assert result.profile_id == "profile-123"
    assert result.job_id == "job-456"
    assert result.customization_id is not None
    assert result.created_at is not None
    assert result.template == "modern"  # Default template

    # Should have customized experiences and skills
    assert len(result.selected_experiences) > 0
    assert len(result.reordered_skills) > 0


def test_customize_resume_with_preferences(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test resume customization with custom preferences."""
    prefs = CustomizationPreferences(
        achievements_per_role=2,
        max_skills=3,
        template="classic",
    )

    result = customize_resume(complete_profile, complete_match_result, prefs)

    # Check preferences applied
    assert result.template == "classic"
    assert len(result.reordered_skills) <= 3

    # Check achievements per role
    for exp in result.selected_experiences:
        if exp.achievements:
            assert len(exp.achievements) <= 2


def test_customize_resume_with_custom_summary(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test resume customization with custom summary."""
    custom_summary = "Expert Python developer with 5+ years of experience in microservices."

    result = customize_resume(
        complete_profile,
        complete_match_result,
        customized_summary=custom_summary,
    )

    assert result.customized_summary == custom_summary


def test_customize_resume_metadata(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test that metadata is correctly generated."""
    result = customize_resume(complete_profile, complete_match_result)

    # Check metadata exists
    assert "changes_log" in result.metadata
    assert "original_achievement_count" in result.metadata
    assert "customized_achievement_count" in result.metadata
    assert "original_skill_count" in result.metadata
    assert "customized_skill_count" in result.metadata
    assert "match_score" in result.metadata
    assert "preferences" in result.metadata

    # Check match score
    assert result.metadata["match_score"] == 85


def test_customize_resume_with_custom_strategies(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test customization with custom achievement and skill strategies."""
    prefs = CustomizationPreferences(
        achievement_strategy=AchievementSelection(
            top_n=1,
            prioritize_leadership=True,
        ),
        skills_strategy=SkillsDisplayStrategy(
            top_n=2,
            group_by_category=False,
        ),
    )

    result = customize_resume(complete_profile, complete_match_result, prefs)

    # Check strategies applied
    assert len(result.reordered_skills) <= 2

    # Achievements should be limited
    for exp in result.selected_experiences:
        if exp.achievements:
            assert len(exp.achievements) <= 1


# Tests for changes log generation

def test_generate_changes_log(complete_profile: UserProfile):
    """Test change log generation."""
    # Create modified experiences with fewer achievements
    customized_experiences = [
        Experience(
            company=complete_profile.experiences[0].company,
            title=complete_profile.experiences[0].title,
            start_date=complete_profile.experiences[0].start_date,
            end_date=complete_profile.experiences[0].end_date,
            achievements=complete_profile.experiences[0].achievements[:2],  # Only 2 achievements
        ),
        Experience(
            company=complete_profile.experiences[1].company,
            title=complete_profile.experiences[1].title,
            start_date=complete_profile.experiences[1].start_date,
            end_date=complete_profile.experiences[1].end_date,
            achievements=complete_profile.experiences[1].achievements[:1],  # Only 1 achievement
        ),
    ]

    customized_skills = complete_profile.skills[:3]  # Only 3 skills

    log = _generate_changes_log(complete_profile, customized_experiences, customized_skills)

    assert "achievements_removed" in log
    assert "achievements_kept" in log
    assert "skills_removed" in log
    assert "skills_kept" in log
    assert "skills_reordered" in log

    # Check counts
    assert log["achievements_removed"] == 2  # 5 original - 3 kept
    assert log["achievements_kept"] == 3
    assert log["skills_removed"] == 2  # 5 original - 3 kept
    assert log["skills_kept"] == 3


def test_generate_changes_log_with_achievement_details(complete_profile: UserProfile):
    """Test that change log includes per-experience details."""
    customized_experiences = [
        Experience(
            company=complete_profile.experiences[0].company,
            title=complete_profile.experiences[0].title,
            start_date=complete_profile.experiences[0].start_date,
            end_date=complete_profile.experiences[0].end_date,
            achievements=complete_profile.experiences[0].achievements[:1],  # Only 1 achievement
        ),
        complete_profile.experiences[1],  # Keep all achievements
    ]

    log = _generate_changes_log(complete_profile, customized_experiences, complete_profile.skills)

    # Should have achievement changes for first experience
    assert "achievement_changes_by_experience" in log
    changes = log["achievement_changes_by_experience"]
    assert len(changes) == 1  # Only first experience changed
    assert changes[0]["company"] == "Tech Corp"
    assert changes[0]["removed_count"] == 2  # 3 original - 1 kept


# Tests for data loss validation

def test_validate_no_data_loss_valid(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test validation passes for valid customization."""
    result = customize_resume(complete_profile, complete_match_result)
    # Should not raise - validation happens inside customize_resume
    _validate_no_data_loss(complete_profile, result)


def test_validate_no_data_loss_profile_id_mismatch(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test validation fails for profile ID mismatch."""
    result = customize_resume(complete_profile, complete_match_result)
    # Manually break the profile_id
    result.profile_id = "wrong-id"

    with pytest.raises(ValueError, match="Profile ID mismatch"):
        _validate_no_data_loss(complete_profile, result)


def test_validate_no_data_loss_job_id_mismatch(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test validation fails for job ID mismatch."""
    result = customize_resume(complete_profile, complete_match_result)
    # Manually break the job_id
    result.job_id = "wrong-job-id"

    with pytest.raises(ValueError, match="Job ID mismatch"):
        _validate_no_data_loss(complete_profile, result)


def test_validate_no_data_loss_experience_count_mismatch(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test validation fails if experience count changes."""
    result = customize_resume(complete_profile, complete_match_result)
    # Remove an experience
    result.selected_experiences = result.selected_experiences[:1]

    with pytest.raises(ValueError, match="Experience count mismatch"):
        _validate_no_data_loss(complete_profile, result)


# Tests for customization summary

def test_get_customization_summary(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test customization summary generation."""
    result = customize_resume(complete_profile, complete_match_result)
    summary = get_customization_summary(result)

    assert "customization_id" in summary
    assert "created_at" in summary
    assert "match_score" in summary
    assert "template" in summary
    assert "has_custom_summary" in summary
    assert "experiences_count" in summary
    assert "achievements_count" in summary
    assert "skills_count" in summary
    assert "changes" in summary
    assert "preferences" in summary

    # Check values
    assert summary["match_score"] == 85
    assert summary["template"] == "modern"
    assert summary["has_custom_summary"] is False  # No custom summary provided
    assert summary["experiences_count"] == 2


def test_get_customization_summary_with_custom_summary(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test summary shows custom summary flag."""
    result = customize_resume(
        complete_profile,
        complete_match_result,
        customized_summary="Custom summary",
    )
    summary = get_customization_summary(result)

    assert summary["has_custom_summary"] is True


# Integration tests

def test_customize_resume_end_to_end(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test complete resume customization workflow."""
    prefs = CustomizationPreferences(
        achievements_per_role=2,
        max_skills=4,
        template="ats",
    )

    result = customize_resume(
        complete_profile,
        complete_match_result,
        prefs,
        customized_summary="Expert Python developer with microservices experience.",
    )

    # Validate complete structure
    assert result.customization_id is not None
    assert result.created_at is not None
    assert result.profile_id == complete_match_result.profile_id
    assert result.job_id == complete_match_result.job_id
    assert result.template == "ats"
    assert result.customized_summary is not None

    # Validate customizations applied
    assert len(result.selected_experiences) == len(complete_profile.experiences)
    assert len(result.reordered_skills) <= 4

    for exp in result.selected_experiences:
        if exp.achievements:
            assert len(exp.achievements) <= 2

    # Validate truthfulness (should not raise)
    _validate_no_data_loss(complete_profile, result)

    # Validate metadata
    assert result.metadata["match_score"] == 85
    assert result.metadata["preferences"]["achievements_per_role"] == 2
    assert result.metadata["preferences"]["max_skills"] == 4

    # Get summary
    summary = get_customization_summary(result)
    assert summary["template"] == "ats"
    assert summary["has_custom_summary"] is True


def test_customize_resume_preserves_original_profile(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test that customization doesn't modify the original profile."""
    # Store original counts
    original_achievement_count = sum(
        len(exp.achievements) for exp in complete_profile.experiences
    )
    original_skill_count = len(complete_profile.skills)

    # Customize with aggressive filtering
    prefs = CustomizationPreferences(achievements_per_role=1, max_skills=2)
    _ = customize_resume(complete_profile, complete_match_result, prefs)

    # Original should be unchanged
    assert sum(len(exp.achievements) for exp in complete_profile.experiences) == original_achievement_count
    assert len(complete_profile.skills) == original_skill_count


def test_customize_resume_multiple_customizations(
    complete_profile: UserProfile,
    complete_match_result: MatchResult,
):
    """Test creating multiple customizations from same profile."""
    prefs1 = CustomizationPreferences(achievements_per_role=1, template="modern")
    prefs2 = CustomizationPreferences(achievements_per_role=3, template="classic")

    result1 = customize_resume(complete_profile, complete_match_result, prefs1)
    result2 = customize_resume(complete_profile, complete_match_result, prefs2)

    # Should have different IDs
    assert result1.customization_id != result2.customization_id

    # Should have different settings
    assert result1.template == "modern"
    assert result2.template == "classic"

    # Both should be valid
    _validate_no_data_loss(complete_profile, result1)
    _validate_no_data_loss(complete_profile, result2)
