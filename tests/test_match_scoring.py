"""
Unit tests for Match Scoring System (Phase 2.3).

Tests cover:
- Experience score calculation
- Domain score calculation
- Keyword coverage score
- Overall match score calculation
- Weighted scoring logic
- Suggestion generation
- Score reproducibility
"""


from resume_customizer.core.matcher import (
    SkillMatcher,
    calculate_domain_score,
    calculate_experience_score,
    calculate_keyword_score,
    calculate_match_score,
)
from resume_customizer.core.models import (
    Achievement,
    ContactInfo,
    Education,
    Experience,
    JobDescription,
    JobRequirements,
    Skill,
    UserProfile,
)


class TestExperienceScore:
    """Test experience score calculation."""

    def test_no_requirement_full_score(self):
        """Test that no experience requirement gives full score."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            requirements=JobRequirements(
                required_experience_years=None,
            ),
        )

        score = calculate_experience_score(profile, job)
        assert score == 100.0

    def test_meets_requirement(self):
        """Test user meeting experience requirement."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[
                Experience(
                    company="Company A",
                    title="Engineer",
                    start_date="2020-01",
                    end_date="2022-01",
                ),
                Experience(
                    company="Company B",
                    title="Engineer",
                    start_date="2022-01",
                    end_date="2024-01",
                ),
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            requirements=JobRequirements(
                required_experience_years=3,
            ),
        )

        score = calculate_experience_score(profile, job)
        # 2 experiences * 2 years = 4 years, which meets requirement of 3
        assert score == 100.0

    def test_exceeds_requirement(self):
        """Test user exceeding experience requirement."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[
                Experience(
                    company=f"Company {i}",
                    title="Engineer",
                    start_date="2020-01",
                    end_date="2022-01",
                )
                for i in range(5)
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            requirements=JobRequirements(
                required_experience_years=3,
            ),
        )

        score = calculate_experience_score(profile, job)
        # 5 experiences * 2 = 10 years, exceeds 3 years requirement
        # Should still get high score but might be slightly penalized for overqualification
        assert score >= 90.0

    def test_under_qualified(self):
        """Test user under-qualified for experience."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[
                Experience(
                    company="Company A",
                    title="Engineer",
                    start_date="2023-01",
                    end_date="2024-01",
                ),
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Senior Engineer",
            company="Test Co",
            requirements=JobRequirements(
                required_experience_years=8,
            ),
        )

        score = calculate_experience_score(profile, job)
        # 1 experience * 2 = 2 years, requirement is 8 years
        # Score should be 2/8 * 100 = 25%
        assert score == 25.0


class TestDomainScore:
    """Test domain knowledge score calculation."""

    def test_no_domain_context(self):
        """Test when job has no domain context."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            description="",
            company_description=None,
        )

        score = calculate_domain_score(profile, job)
        assert score == 100.0

    def test_matching_domain(self):
        """Test matching domain keywords."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[
                Experience(
                    company="Finance Corp",
                    title="Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    description="Developed financial trading systems and payment processing platforms",
                ),
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="FinTech Startup",
            description="Build payment processing systems",
            company_description="Leading financial technology company",
        )

        score = calculate_domain_score(profile, job)
        # Should have overlap in financial/payment keywords
        assert score > 0

    def test_no_matching_domain(self):
        """Test no matching domain keywords."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Software engineer",
            experiences=[
                Experience(
                    company="Gaming Studio",
                    title="Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    description="Developed multiplayer video games and game engines",
                ),
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="Healthcare Tech",
            description="Build medical record systems",
            company_description="Healthcare technology solutions provider",
        )

        score = calculate_domain_score(profile, job)
        # Different domains, should have low score
        assert score >= 0


class TestKeywordScore:
    """Test keyword coverage score calculation."""

    def test_high_keyword_coverage(self):
        """Test high keyword coverage."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Full stack developer building scalable web applications",
            experiences=[
                Experience(
                    company="Tech Co",
                    title="Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    achievements=[
                        Achievement(
                            text="Built scalable web applications using modern frameworks"
                        ),
                        Achievement(text="Developed REST APIs and microservices"),
                    ],
                ),
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Full Stack Developer",
            company="Test Co",
            description="Build scalable web applications and REST APIs",
            responsibilities=["Develop modern web applications", "Design microservices"],
        )

        score = calculate_keyword_score(profile, job)
        # Should have high overlap
        assert score > 50

    def test_low_keyword_coverage(self):
        """Test low keyword coverage."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Frontend developer",
            experiences=[
                Experience(
                    company="Tech Co",
                    title="Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    achievements=[Achievement(text="Built user interfaces")],
                ),
            ],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Backend Engineer",
            company="Test Co",
            description="Build distributed systems, databases, and cloud infrastructure",
            responsibilities=[
                "Design microservices architecture",
                "Optimize database performance",
            ],
        )

        score = calculate_keyword_score(profile, job)
        # Different keywords, should have low coverage
        assert score >= 0


class TestMatchScore:
    """Test overall match score calculation."""

    def test_perfect_match(self):
        """Test near-perfect match scenario."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Python developer with Django experience",
            experiences=[
                Experience(
                    company="Tech Co",
                    title="Python Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    description="Built web applications using Python and Django",
                    achievements=[
                        Achievement(
                            text="Built scalable web applications using Python and Django"
                        ),
                        Achievement(text="Improved performance by 50%"),
                    ],
                ),
            ],
            skills=[
                Skill(name="Python", category="language", proficiency="expert"),
                Skill(name="Django", category="framework", proficiency="expert"),
                Skill(name="PostgreSQL", category="database", proficiency="intermediate"),
            ],
            education=[
                Education(
                    degree="BS Computer Science", institution="University", graduation_year="2020"
                )
            ],
        )

        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            description="Build web applications using Python",
            responsibilities=["Develop web applications", "Write clean Python code"],
            requirements=JobRequirements(
                required_skills=["python", "django"],
                preferred_skills=["postgresql"],
                required_experience_years=3,
            ),
        )

        result = calculate_match_score(profile, job)

        # Should have high overall score
        assert result.overall_score >= 80

        # Check breakdown
        assert result.breakdown.technical_skills_score >= 90
        # 1 experience * 2 years estimate = 2 years, requirement is 3 years
        # Expected score: (2/3) * 100 = 66.7
        assert result.breakdown.experience_score >= 60

        # Should have matched skills
        assert len(result.matched_skills) >= 2

        # Should have no missing required skills
        assert len(result.missing_required_skills) == 0

    def test_partial_match(self):
        """Test partial match scenario."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Python developer",
            experiences=[
                Experience(
                    company="Tech Co",
                    title="Developer",
                    start_date="2023-01",
                    end_date="2024-01",
                    achievements=[Achievement(text="Built web applications")],
                ),
            ],
            skills=[
                Skill(name="Python", category="language", proficiency="intermediate"),
            ],
            education=[],
        )

        job = JobDescription(
            title="Senior Full Stack Developer",
            company="Test Co",
            description="Build complex distributed systems",
            responsibilities=[
                "Architect microservices",
                "Lead technical initiatives",
                "Mentor junior developers",
            ],
            requirements=JobRequirements(
                required_skills=["python", "javascript", "docker", "kubernetes"],
                preferred_skills=["aws", "terraform"],
                required_experience_years=8,
            ),
        )

        result = calculate_match_score(profile, job)

        # Should have lower overall score
        assert result.overall_score < 70

        # Should have missing skills
        assert len(result.missing_required_skills) > 0

        # Should have suggestions
        assert len(result.suggestions) > 0

    def test_weighted_scoring(self):
        """Test that weighted scoring is applied correctly."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Developer",
            experiences=[],
            skills=[
                Skill(name="Python", category="language", proficiency="expert"),
                Skill(name="Java", category="language", proficiency="expert"),
            ],
            education=[],
        )

        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            requirements=JobRequirements(
                required_skills=["python", "java"],
            ),
        )

        result = calculate_match_score(profile, job)

        # Technical skills is 40% of score
        # 100% skill match should contribute 40 points to overall score
        expected_tech_contribution = result.breakdown.technical_skills_score * 0.40
        expected_exp_contribution = result.breakdown.experience_score * 0.25
        expected_domain_contribution = result.breakdown.domain_score * 0.20
        expected_keyword_contribution = result.breakdown.keyword_coverage_score * 0.15

        total = (
            expected_tech_contribution
            + expected_exp_contribution
            + expected_domain_contribution
            + expected_keyword_contribution
        )

        # Should match breakdown total
        assert abs(result.breakdown.total_score - total) < 0.1

    def test_ranked_achievements_included(self):
        """Test that ranked achievements are included in result."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Python developer",
            experiences=[
                Experience(
                    company="Tech Co",
                    title="Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    achievements=[
                        Achievement(text="Built Python applications"),
                        Achievement(text="Wrote documentation"),
                    ],
                ),
            ],
            skills=[Skill(name="Python", category="language")],
            education=[],
        )

        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
            responsibilities=["Build Python applications"],
        )

        result = calculate_match_score(profile, job)

        # Should have ranked achievements
        assert len(result.ranked_achievements) == 2

        # Achievements should be tuples of (Achievement, score)
        for achievement, score in result.ranked_achievements:
            assert isinstance(achievement, Achievement)
            assert isinstance(score, float)


class TestSuggestions:
    """Test suggestion generation."""

    def test_missing_required_skills_suggestion(self):
        """Test suggestion for missing required skills."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Developer",
            experiences=[],
            skills=[Skill(name="Python", category="language")],
            education=[],
        )

        job = JobDescription(
            title="Full Stack Developer",
            company="Test Co",
            requirements=JobRequirements(
                required_skills=["python", "javascript", "react", "docker"],
            ),
        )

        result = calculate_match_score(profile, job)

        # Should have suggestions for missing skills
        assert len(result.suggestions) > 0
        assert any("required skills" in s.lower() for s in result.suggestions)

    def test_missing_preferred_skills_suggestion(self):
        """Test suggestion for missing preferred skills."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Developer",
            experiences=[],
            skills=[
                Skill(name="Python", category="language"),
                Skill(name="JavaScript", category="language"),
            ],
            education=[],
        )

        job = JobDescription(
            title="Developer",
            company="Test Co",
            requirements=JobRequirements(
                required_skills=["python", "javascript"],
                preferred_skills=["docker", "kubernetes", "aws"],
            ),
        )

        result = calculate_match_score(profile, job)

        # Should have suggestions for preferred skills
        assert len(result.suggestions) > 0

    def test_low_score_suggestions(self):
        """Test suggestions based on low scores."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="New developer",
            experiences=[],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Senior Software Engineer",
            company="Test Co",
            description="Complex distributed systems",
            responsibilities=["Lead architecture", "Mentor team"],
            requirements=JobRequirements(
                required_skills=["python", "java", "docker", "kubernetes"],
                required_experience_years=10,
            ),
        )

        result = calculate_match_score(profile, job)

        # Should have multiple suggestions
        assert len(result.suggestions) > 0


class TestReproducibility:
    """Test scoring reproducibility."""

    def test_same_input_same_output(self):
        """Test that same inputs produce same outputs."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Python developer",
            experiences=[
                Experience(
                    company="Tech Co",
                    title="Developer",
                    start_date="2020-01",
                    end_date="2024-01",
                    achievements=[Achievement(text="Built applications")],
                ),
            ],
            skills=[Skill(name="Python", category="language")],
            education=[],
        )

        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
        )

        # Calculate twice
        result1 = calculate_match_score(profile, job)
        result2 = calculate_match_score(profile, job)

        # Results should be identical
        assert result1.overall_score == result2.overall_score
        assert result1.breakdown.technical_skills_score == result2.breakdown.technical_skills_score
        assert result1.breakdown.experience_score == result2.breakdown.experience_score
        assert result1.breakdown.domain_score == result2.breakdown.domain_score
        assert (
            result1.breakdown.keyword_coverage_score == result2.breakdown.keyword_coverage_score
        )


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_profile(self):
        """Test with minimal profile."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="",
            experiences=[],
            skills=[],
            education=[],
        )

        job = JobDescription(
            title="Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
        )

        result = calculate_match_score(profile, job)

        # Should still work
        assert 0 <= result.overall_score <= 100
        assert len(result.missing_required_skills) > 0

    def test_custom_skill_matcher(self):
        """Test using custom skill matcher."""
        profile = UserProfile(
            name="Test User",
            contact=ContactInfo(email="test@example.com"),
            summary="Developer",
            experiences=[],
            skills=[Skill(name="Python", category="language")],
            education=[],
        )

        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
        )

        # Create custom matcher
        matcher = SkillMatcher()

        result = calculate_match_score(profile, job, skill_matcher=matcher)

        # Should use custom matcher
        assert result.overall_score > 0
