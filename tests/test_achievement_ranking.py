"""
Unit tests for Achievement Ranking System (Phase 2.2).

Tests cover:
- Keyword extraction
- Technical term extraction
- Metrics extraction
- Achievement ranking logic
- Scoring consistency
"""


from resume_customizer.core.matcher import (
    extract_keywords,
    extract_metrics,
    extract_technical_terms,
    rank_achievements,
)
from resume_customizer.core.models import Achievement, JobDescription, JobRequirements


class TestKeywordExtraction:
    """Test keyword extraction from text."""

    def test_extract_basic_keywords(self):
        """Test extracting nouns and verbs."""
        text = "Built scalable microservices using Python and Docker"
        keywords = extract_keywords(text)

        # Should extract key nouns and verbs
        assert "build" in keywords or "built" in keywords
        assert any(k in ["microservice", "microservices"] for k in keywords)
        assert "python" in keywords
        assert "docker" in keywords

    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered out."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = extract_keywords(text)

        # Stop words should be excluded
        assert "the" not in keywords
        assert "over" not in keywords

        # Content words should be included
        assert any(k in ["fox", "dog", "jump"] for k in keywords)

    def test_extract_keywords_short_words_excluded(self):
        """Test that words with 2 or fewer characters are excluded."""
        text = "I go to the AI ML conference"
        keywords = extract_keywords(text)

        # Short words excluded
        assert "i" not in keywords
        assert "go" not in keywords
        assert "to" not in keywords

    def test_extract_keywords_lemmatization(self):
        """Test that words are lemmatized."""
        text = "Running tests, building applications, deploying services"
        keywords = extract_keywords(text)

        # Should be lemmatized
        assert "run" in keywords or "running" in keywords
        assert "build" in keywords or "building" in keywords
        assert "deploy" in keywords or "deploying" in keywords

    def test_extract_keywords_empty_text(self):
        """Test handling of empty text."""
        keywords = extract_keywords("")
        assert keywords == []


class TestTechnicalTermExtraction:
    """Test technical term extraction."""

    def test_extract_acronyms(self):
        """Test extracting acronyms."""
        text = "Used REST API and implemented CI/CD pipeline"
        terms = extract_technical_terms(text)

        assert "rest" in terms
        assert "api" in terms
        assert "ci" in terms or "cd" in terms

    def test_extract_package_names(self):
        """Test extracting package names with dots."""
        text = "Developed with React.js and Node.js frameworks"
        terms = extract_technical_terms(text)

        assert "react.js" in terms
        assert "node.js" in terms

    def test_extract_version_numbers(self):
        """Test extracting version numbers."""
        text = "Upgraded to Python 3.11 and Django v4.2"
        terms = extract_technical_terms(text)

        # Should capture version numbers
        assert any("3.11" in t for t in terms)
        assert any("4.2" in t or "v4.2" in t for t in terms)

    def test_extract_capitalized_tech_names(self):
        """Test extracting capitalized technology names."""
        text = "Built with Python, Docker, and Kubernetes"
        terms = extract_technical_terms(text)

        assert "python" in terms
        assert "docker" in terms
        assert "kubernetes" in terms

    def test_filters_common_words(self):
        """Test that common English words are filtered."""
        text = "This is a test with Docker and Python"
        terms = extract_technical_terms(text)

        # Common words should be excluded
        assert "this" not in terms
        assert "test" not in terms  # "Test" would be filtered

        # Tech terms should be included
        assert "docker" in terms
        assert "python" in terms

    def test_extract_technical_terms_empty(self):
        """Test handling of empty text."""
        terms = extract_technical_terms("")
        assert terms == []


class TestMetricsExtraction:
    """Test metrics extraction."""

    def test_extract_percentages(self):
        """Test extracting percentages."""
        text = "Improved performance by 50% and reduced latency by 30%"
        metrics = extract_metrics(text)

        assert "50%" in metrics
        assert "30%" in metrics

    def test_extract_money_amounts(self):
        """Test extracting money amounts."""
        text = "Reduced costs by $100K and saved $1.5M annually"
        metrics = extract_metrics(text)

        assert "$100K" in metrics or "$100k" in metrics
        assert "$1.5M" in metrics or "$1.5m" in metrics

    def test_extract_multipliers(self):
        """Test extracting multipliers."""
        text = "Increased speed 10x and improved efficiency 5x"
        metrics = extract_metrics(text)

        assert "10x" in metrics
        assert "5x" in metrics

    def test_extract_large_numbers(self):
        """Test extracting large numbers with commas."""
        text = "Processed 1,000,000 requests per day"
        metrics = extract_metrics(text)

        assert "1,000,000" in metrics

    def test_extract_plus_suffix(self):
        """Test extracting numbers with + suffix."""
        text = "Served 100+ customers and handled 1000+ requests"
        metrics = extract_metrics(text)

        assert "100+" in metrics
        assert "1000+" in metrics

    def test_extract_multiple_metric_types(self):
        """Test extracting multiple types of metrics."""
        text = "Improved by 50%, saved $100K, achieved 10x speed, handled 1,000+ users"
        metrics = extract_metrics(text)

        assert len(metrics) >= 4

    def test_extract_metrics_empty(self):
        """Test handling of empty text."""
        metrics = extract_metrics("")
        assert metrics == []


class TestAchievementRanking:
    """Test achievement ranking logic."""

    def test_rank_achievements_with_keyword_match(self):
        """Test that achievements with matching keywords score higher."""
        # Create job with specific keywords
        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(
                required_skills=["python", "django", "postgresql"],
            ),
            responsibilities=["Build web applications", "Write clean code"],
        )

        # Achievement with matching keywords
        achievement1 = Achievement(
            text="Built web applications using Python and Django with clean code practices",
        )

        # Achievement without matching keywords
        achievement2 = Achievement(
            text="Organized team building events and managed schedules",
        )

        ranked = rank_achievements([achievement1, achievement2], job)

        # First achievement should score higher
        assert ranked[0].achievement == achievement1
        assert ranked[0].score > ranked[1].score

    def test_rank_achievements_with_tech_match(self):
        """Test that achievements with matching tech score higher."""
        job = JobDescription(
            title="DevOps Engineer",
            company="Test Co",
            requirements=JobRequirements(
                required_skills=["docker", "kubernetes", "aws"],
            ),
            responsibilities=["Deploy containerized applications"],
        )

        achievement_with_tech = Achievement(
            text="Deployed microservices using Docker and Kubernetes on AWS",
        )

        achievement_without_tech = Achievement(
            text="Wrote documentation and conducted training sessions",
        )

        ranked = rank_achievements([achievement_with_tech, achievement_without_tech], job)

        assert ranked[0].achievement == achievement_with_tech
        assert any("matching technologies" in r for r in ranked[0].reasons)

    def test_rank_achievements_metrics_bonus(self):
        """Test that achievements with metrics get bonus points."""
        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
            responsibilities=["Improve performance"],
        )

        achievement_with_metrics = Achievement(
            text="Improved performance by 50% and reduced costs by $100K",
        )

        achievement_without_metrics = Achievement(
            text="Improved overall system performance and reduced operational costs",
        )

        ranked = rank_achievements([achievement_with_metrics, achievement_without_metrics], job)

        assert ranked[0].achievement == achievement_with_metrics
        assert any("metrics" in r.lower() for r in ranked[0].reasons)

    # Recency bonus test removed - Achievement model doesn't have year field
    # Year information would come from the parent Experience object

    def test_rank_achievements_sorting(self):
        """Test that achievements are sorted by score descending."""
        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python", "django"]),
            responsibilities=["Build web applications"],
        )

        achievements = [
            Achievement(text="Wrote documentation"),  # Low score
            Achievement(
                text="Built web applications using Python and Django"
            ),  # High score
            Achievement(text="Organized meetings"),  # Low score
        ]

        ranked = rank_achievements(achievements, job)

        # Scores should be descending
        for i in range(len(ranked) - 1):
            assert ranked[i].score >= ranked[i + 1].score

    def test_rank_achievements_reasons_provided(self):
        """Test that ranking reasons are provided."""
        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
            responsibilities=["Develop software"],
        )

        achievement = Achievement(
            text="Developed Python software with 50% improvement"
        )

        ranked = rank_achievements([achievement], job)

        # Should have reasons
        assert len(ranked[0].reasons) > 0

    def test_rank_achievements_empty_list(self):
        """Test handling of empty achievement list."""
        job = JobDescription(
            title="Software Engineer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
            responsibilities=["Develop software"],
        )

        ranked = rank_achievements([], job)

        assert ranked == []

    def test_rank_achievements_score_range(self):
        """Test that scores are within expected range (0-100)."""
        job = JobDescription(
            title="Full Stack Developer",
            company="Test Co",
            requirements=JobRequirements(
                required_skills=["python", "react", "postgresql", "docker"]
            ),
            responsibilities=["Build full stack applications", "Deploy services"],
        )

        achievement = Achievement(
            text="Built full stack application using Python, React, PostgreSQL, and Docker. "
            "Improved performance by 50% and reduced costs by $100K. "
            "Deployed containerized services with 99.9% uptime."
        )

        ranked = rank_achievements([achievement], job)

        # Score should be between 0 and 100
        assert 0 <= ranked[0].score <= 100


class TestAchievementRankingConsistency:
    """Test ranking consistency and reproducibility."""

    def test_same_input_same_output(self):
        """Test that same inputs produce same outputs."""
        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python", "django"]),
            responsibilities=["Build applications"],
        )

        achievements = [
            Achievement(text="Built Python application"),
            Achievement(text="Wrote Django code"),
        ]

        ranked1 = rank_achievements(achievements, job)
        ranked2 = rank_achievements(achievements, job)

        # Results should be identical
        assert len(ranked1) == len(ranked2)
        for r1, r2 in zip(ranked1, ranked2, strict=True):
            assert r1.score == r2.score
            assert r1.achievement == r2.achievement

    def test_order_independence(self):
        """Test that input order doesn't affect scoring."""
        job = JobDescription(
            title="Python Developer",
            company="Test Co",
            requirements=JobRequirements(required_skills=["python"]),
            responsibilities=["Develop software"],
        )

        ach1 = Achievement(text="Built Python application")
        ach2 = Achievement(text="Wrote Python tests")

        ranked_forward = rank_achievements([ach1, ach2], job)
        ranked_reverse = rank_achievements([ach2, ach1], job)

        # Scores should be the same regardless of input order
        scores_forward = sorted([r.score for r in ranked_forward], reverse=True)
        scores_reverse = sorted([r.score for r in ranked_reverse], reverse=True)

        assert scores_forward == scores_reverse
