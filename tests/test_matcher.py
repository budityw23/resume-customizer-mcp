"""
Unit tests for SkillMatcher class.

Tests cover:
- Exact matching
- Case insensitive matching
- Synonym matching
- Fuzzy matching
- Skill hierarchy
- Missing skills detection
- Reproducibility
"""


from resume_customizer.core.matcher import SkillMatcher
from resume_customizer.core.models import Skill


class TestSkillNormalization:
    """Test skill normalization functionality."""

    def test_lowercase_conversion(self):
        """Test that skills are converted to lowercase."""
        matcher = SkillMatcher()
        assert matcher._normalize("PYTHON") == "python"
        assert matcher._normalize("JavaScript") == "javascript"
        assert matcher._normalize("React") == "react"

    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is removed."""
        matcher = SkillMatcher()
        assert matcher._normalize("  python  ") == "python"
        assert matcher._normalize("\tjavascript\n") == "javascript"

    def test_whitespace_collapsing(self):
        """Test that multiple spaces are collapsed to single space."""
        matcher = SkillMatcher()
        assert matcher._normalize("machine  learning") == "machine learning"
        assert matcher._normalize("react   native") == "react native"

    def test_extension_removal(self):
        """Test that common file extensions are removed."""
        matcher = SkillMatcher()
        assert matcher._normalize("React.js") == "react"
        assert matcher._normalize("Vue.js") == "vue"
        assert matcher._normalize("script.py") == "script"
        assert matcher._normalize("app.java") == "app"
        assert matcher._normalize("style.css") == "style"


class TestExactMatching:
    """Test exact skill matching."""

    def test_exact_match_same_case(self):
        """Test exact match with same case."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Python", "Python") is True
        assert matcher.match_skill("JavaScript", "JavaScript") is True

    def test_exact_match_different_case(self):
        """Test exact match ignores case."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Python", "python") is True
        assert matcher.match_skill("JAVASCRIPT", "javascript") is True
        assert matcher.match_skill("ReAcT", "react") is True

    def test_exact_match_with_whitespace(self):
        """Test exact match handles whitespace."""
        matcher = SkillMatcher()
        assert matcher.match_skill("  Python  ", "python") is True
        assert matcher.match_skill("JavaScript", "  javascript  ") is True

    def test_no_match_different_skills(self):
        """Test that different skills don't match."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Python", "Java") is False
        assert matcher.match_skill("React", "Angular") is False


class TestSynonymMatching:
    """Test synonym-based matching."""

    def test_python_synonyms(self):
        """Test Python skill synonyms."""
        matcher = SkillMatcher()
        # All these should match "python"
        assert matcher.match_skill("Python", "python") is True
        assert matcher.match_skill("Python3", "python") is True
        assert matcher.match_skill("python", "Python3") is True
        assert matcher.match_skill("py", "python") is True

    def test_javascript_synonyms(self):
        """Test JavaScript skill synonyms."""
        matcher = SkillMatcher()
        assert matcher.match_skill("JavaScript", "js") is True
        assert matcher.match_skill("js", "javascript") is True
        assert matcher.match_skill("ES6", "javascript") is True
        assert matcher.match_skill("ECMAScript", "javascript") is True

    def test_framework_synonyms(self):
        """Test framework synonyms."""
        matcher = SkillMatcher()
        # React synonyms
        assert matcher.match_skill("React", "ReactJS") is True
        assert matcher.match_skill("React.js", "react") is True

        # Node synonyms
        assert matcher.match_skill("Node", "nodejs") is True
        assert matcher.match_skill("Node.js", "node") is True

    def test_database_synonyms(self):
        """Test database synonyms."""
        matcher = SkillMatcher()
        assert matcher.match_skill("PostgreSQL", "postgres") is True
        assert matcher.match_skill("postgres", "psql") is True
        assert matcher.match_skill("MongoDB", "mongo") is True


class TestFuzzyMatching:
    """Test fuzzy matching for typos."""

    def test_typo_matching(self):
        """Test that minor typos are caught."""
        matcher = SkillMatcher()
        # Close enough to match (>= 80% similarity)
        assert matcher.match_skill("Pythom", "Python", threshold=80) is True
        assert matcher.match_skill("Javascrpt", "JavaScript", threshold=80) is True

    def test_fuzzy_threshold(self):
        """Test fuzzy matching threshold."""
        matcher = SkillMatcher()
        # Should match with low threshold (Rust vs Ruby are somewhat similar)
        assert matcher.match_skill("Rust", "Ruby", threshold=50) is True

        # Should not match with high threshold
        assert matcher.match_skill("Rust", "Ruby", threshold=90) is False

    def test_completely_different_words(self):
        """Test that completely different words don't fuzzy match."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Python", "Java", threshold=80) is False
        assert matcher.match_skill("React", "Angular", threshold=80) is False


class TestSkillHierarchy:
    """Test skill hierarchy matching."""

    def test_react_implies_javascript(self):
        """Test that having React implies knowing JavaScript."""
        matcher = SkillMatcher()
        # User has React, job requires JavaScript
        assert matcher.match_skill("React", "JavaScript") is True

    def test_vue_implies_javascript(self):
        """Test that having Vue implies knowing JavaScript."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Vue", "JavaScript") is True

    def test_django_implies_python(self):
        """Test that having Django implies knowing Python."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Django", "Python") is True

    def test_flask_implies_python(self):
        """Test that having Flask implies knowing Python."""
        matcher = SkillMatcher()
        assert matcher.match_skill("Flask", "Python") is True

    def test_hierarchy_not_reverse(self):
        """Test that hierarchy doesn't work in reverse."""
        matcher = SkillMatcher()
        # Knowing JavaScript doesn't mean you know React
        assert matcher.match_skill("JavaScript", "React") is False

    def test_nodejs_implies_javascript(self):
        """Test Node.js hierarchy."""
        matcher = SkillMatcher()
        # Node.js should imply JavaScript knowledge
        assert matcher.match_skill("Node", "JavaScript") is True
        assert matcher.match_skill("Express", "JavaScript") is True


class TestMatchSkills:
    """Test matching multiple skills at once."""

    def test_all_skills_matched(self):
        """Test when all required skills are matched."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="JavaScript", category="language", proficiency="intermediate"),
            Skill(name="SQL", category="database", proficiency="intermediate"),
        ]
        required_skills = ["python", "javascript", "sql"]

        matched, missing = matcher.match_skills(user_skills, required_skills)

        assert len(matched) == 3
        assert len(missing) == 0

    def test_some_skills_matched(self):
        """Test when only some skills are matched."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="JavaScript", category="language", proficiency="intermediate"),
        ]
        required_skills = ["python", "javascript", "java", "go"]

        matched, missing = matcher.match_skills(user_skills, required_skills)

        assert len(matched) == 2
        assert len(missing) == 2
        assert "java" in missing
        assert "go" in missing

    def test_synonym_matching_in_list(self):
        """Test synonym matching works in skill lists."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="React", category="framework", proficiency="expert"),
            Skill(name="Python3", category="language", proficiency="expert"),
        ]
        required_skills = ["javascript", "python"]

        matched, missing = matcher.match_skills(user_skills, required_skills)

        # React should match JavaScript via hierarchy
        # Python3 should match python via synonyms
        assert len(matched) == 2
        assert len(missing) == 0

    def test_match_type_classification(self):
        """Test that matches include proficiency information."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="ReactJS", category="framework", proficiency="intermediate"),
        ]
        required_skills = ["python", "react"]

        matched, _ = matcher.match_skills(user_skills, required_skills)

        # Find matches by skill name
        python_match = next(m for m in matched if m.skill == "python")
        react_match = next(m for m in matched if m.skill == "react")

        assert python_match.matched is True
        assert python_match.user_proficiency == "expert"
        assert react_match.matched is True
        assert react_match.user_proficiency == "intermediate"


class TestMissingSkills:
    """Test missing skills identification."""

    def test_identify_missing_required_skills(self):
        """Test identifying missing required skills."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
        ]

        missing = matcher.identify_missing_skills(
            user_skills,
            required_skills=["python", "java", "go"],
            preferred_skills=None,
        )

        assert len(missing["required"]) == 2
        assert "java" in missing["required"]
        assert "go" in missing["required"]

    def test_identify_missing_preferred_skills(self):
        """Test identifying missing preferred skills."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
        ]

        missing = matcher.identify_missing_skills(
            user_skills,
            required_skills=["python"],
            preferred_skills=["docker", "kubernetes"],
        )

        assert len(missing["required"]) == 0
        assert len(missing["preferred"]) == 2
        assert "docker" in missing["preferred"]
        assert "kubernetes" in missing["preferred"]


class TestCalculateRequiredSkillsMatch:
    """Test required skills match percentage calculation."""

    def test_perfect_match(self):
        """Test 100% match when all skills present."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="Java", category="language", proficiency="intermediate"),
            Skill(name="SQL", category="database", proficiency="intermediate"),
        ]

        percentage = matcher.calculate_required_skills_match(
            user_skills, ["python", "java", "sql"]
        )

        assert percentage == 100

    def test_partial_match(self):
        """Test partial match percentage."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="Java", category="language", proficiency="intermediate"),
        ]

        # 2 out of 4 = 50%
        percentage = matcher.calculate_required_skills_match(
            user_skills, ["python", "java", "go", "rust"]
        )

        assert percentage == 50

    def test_no_match(self):
        """Test 0% when no skills match."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
        ]

        percentage = matcher.calculate_required_skills_match(
            user_skills, ["java", "go", "rust"]
        )

        assert percentage == 0

    def test_empty_required_skills(self):
        """Test that empty required skills returns 100%."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
        ]

        percentage = matcher.calculate_required_skills_match(user_skills, [])

        assert percentage == 100


class TestReproducibility:
    """Test that matching is reproducible."""

    def test_same_input_same_output(self):
        """Test that same inputs always produce same outputs."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="React", category="framework", proficiency="intermediate"),
        ]
        required_skills = ["python", "javascript", "sql"]

        # Run matching twice
        matched1, missing1 = matcher.match_skills(user_skills, required_skills)
        matched2, missing2 = matcher.match_skills(user_skills, required_skills)

        # Results should be identical
        assert len(matched1) == len(matched2)
        assert len(missing1) == len(missing2)
        assert set(missing1) == set(missing2)

        # Match details should be the same
        for m1, m2 in zip(matched1, matched2, strict=True):
            assert m1.skill == m2.skill
            assert m1.matched == m2.matched
            assert m1.category == m2.category
            assert m1.user_proficiency == m2.user_proficiency

    def test_score_reproducibility(self):
        """Test that scores are reproducible."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
            Skill(name="JavaScript", category="language", proficiency="intermediate"),
        ]
        required_skills = ["python", "javascript", "java"]

        # Calculate percentage multiple times
        score1 = matcher.calculate_required_skills_match(user_skills, required_skills)
        score2 = matcher.calculate_required_skills_match(user_skills, required_skills)
        score3 = matcher.calculate_required_skills_match(user_skills, required_skills)

        assert score1 == score2 == score3


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_user_skills(self):
        """Test handling of empty user skills list."""
        matcher = SkillMatcher()
        matched, missing = matcher.match_skills([], ["python", "java"])

        assert len(matched) == 0
        assert len(missing) == 2

    def test_empty_required_skills(self):
        """Test handling of empty required skills list."""
        matcher = SkillMatcher()
        user_skills = [
            Skill(name="Python", category="language", proficiency="expert"),
        ]
        matched, missing = matcher.match_skills(user_skills, [])

        assert len(matched) == 0
        assert len(missing) == 0

    def test_both_empty(self):
        """Test handling when both lists are empty."""
        matcher = SkillMatcher()
        matched, missing = matcher.match_skills([], [])

        assert len(matched) == 0
        assert len(missing) == 0

    def test_special_characters_in_skills(self):
        """Test skills with special characters."""
        matcher = SkillMatcher()
        assert matcher.match_skill("C++", "cpp") is True
        assert matcher.match_skill("C#", "csharp") is True

    def test_very_long_skill_names(self):
        """Test very long skill names."""
        matcher = SkillMatcher()
        long_skill = "A" * 100
        assert matcher.match_skill(long_skill, long_skill) is True


class TestWithoutSynonymFile:
    """Test matcher behavior when synonym file is missing."""

    def test_matcher_works_without_synonyms(self, tmp_path):
        """Test that matcher still works without synonym file."""
        # Create matcher with non-existent file
        non_existent = tmp_path / "nonexistent.yaml"
        matcher = SkillMatcher(synonyms_file=non_existent)

        # Should still do exact matching
        assert matcher.match_skill("Python", "python") is True
        assert matcher.match_skill("Python", "Java") is False

        # But won't do synonym matching
        assert len(matcher.synonyms) == 0
        assert len(matcher.skill_to_canonical) == 0
