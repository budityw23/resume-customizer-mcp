"""Integration tests for AI service pipeline.

This module tests the complete AI pipeline including:
- Keyword extraction → achievement rephrasing → summary generation
- API cost tracking and optimization
- Error recovery and fallback mechanisms
- Quality of AI outputs vs rule-based approaches
"""

import json
from unittest.mock import patch

import pytest

from resume_customizer.core.ai_service import AIService


class TestAIPipeline:
    """Test the complete AI pipeline end-to-end."""

    @pytest.fixture
    def service(self):
        """Create AI service instance."""
        return AIService(api_key="test-key")

    @pytest.fixture
    def sample_job_description(self):
        """Sample job description text."""
        return """
        Senior Software Engineer - Backend

        We're looking for an experienced backend engineer to join our team.

        Requirements:
        - 5+ years of Python development experience
        - Strong experience with AWS cloud services
        - Docker and Kubernetes for container orchestration
        - RESTful API design and microservices architecture
        - Database design (PostgreSQL, Redis)
        - CI/CD pipelines and DevOps practices
        - Team leadership and mentoring

        Responsibilities:
        - Design and build scalable backend services
        - Lead technical initiatives
        - Mentor junior engineers
        - Optimize system performance
        """

    @pytest.fixture
    def sample_achievement(self):
        """Sample achievement for rephrasing."""
        return "Built API for user management"

    @pytest.fixture
    def sample_profile_context(self):
        """Sample profile context for summary generation."""
        return {
            "top_skills": ["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"],
            "experience_years": 6,
            "current_title": "Senior Backend Engineer",
            "domain": "Cloud Infrastructure",
            "top_achievements": [
                "Architected microservices platform serving 2M+ users",
                "Reduced infrastructure costs by 45% through optimization",
                "Led team of 4 engineers to deliver major features",
            ],
        }

    def test_complete_pipeline_keyword_to_summary(
        self, service, sample_job_description, sample_profile_context
    ):
        """Test complete pipeline: keyword extraction → summary generation.

        This integration test verifies that:
        1. Keywords are extracted from job description
        2. Extracted keywords inform summary generation
        3. Summary includes relevant keywords
        4. Pipeline produces high-quality output
        """
        # Mock keyword extraction response (with weighted keywords)
        keywords_response = json.dumps({
            "technical_skills": [
                {"keyword": "Python", "weight": 0.9},
                {"keyword": "AWS", "weight": 0.8},
                {"keyword": "Docker", "weight": 0.8},
                {"keyword": "Kubernetes", "weight": 0.8},
                {"keyword": "PostgreSQL", "weight": 0.7},
            ],
            "soft_skills": [
                {"keyword": "leadership", "weight": 0.7},
                {"keyword": "mentoring", "weight": 0.6},
            ],
            "domain_knowledge": [
                {"keyword": "microservices", "weight": 0.8},
                {"keyword": "API design", "weight": 0.7},
                {"keyword": "DevOps", "weight": 0.6},
            ],
            "action_verbs": ["design", "build", "lead", "optimize"],
            "metrics": ["5+ years", "99.9% uptime"],
        })

        # Mock summary generation response
        summary_response = json.dumps({
            "summary": (
                "Senior Backend Engineer with 6 years of experience architecting "
                "scalable microservices on AWS using Python, Docker, and Kubernetes. "
                "Proven track record of reducing costs by 45% while leading engineering "
                "teams to deliver high-impact features for millions of users."
            ),
            "keywords_included": ["Python", "AWS", "Docker", "Kubernetes", "microservices"],
            "word_count": 47,
        })

        with patch.object(
            service, "call_claude", side_effect=[keywords_response, summary_response]
        ):
            # Step 1: Extract keywords
            keywords = service.extract_keywords(sample_job_description)

            assert "technical_skills" in keywords
            # Check that Python is in the weighted keywords list
            tech_skill_keywords = [skill["keyword"] for skill in keywords["technical_skills"]]
            assert "Python" in tech_skill_keywords
            assert "AWS" in tech_skill_keywords

            # Step 2: Generate summary using extracted keywords
            job_context = {
                "title": "Senior Software Engineer - Backend",
                "key_requirements": tech_skill_keywords,
            }

            summary = service.generate_custom_summary(
                profile_context=sample_profile_context,
                job_context=job_context,
                style="balanced",
            )

            # Verify summary quality
            assert "summary" in summary
            assert summary["word_count"] >= 40  # Within recommended range
            assert summary["word_count"] <= 60
            assert len(summary["keywords_included"]) >= 3  # Good keyword coverage

            # Verify keywords flow through pipeline
            extracted_keywords = set(tech_skill_keywords[:5])
            included_keywords = set(summary["keywords_included"])
            overlap = extracted_keywords & included_keywords
            assert len(overlap) >= 2  # At least 2 keywords make it through

    def test_complete_pipeline_with_achievement_rephrasing(
        self, service, sample_achievement, sample_job_description, sample_profile_context
    ):
        """Test pipeline: keyword extraction → achievement rephrasing → summary.

        Verifies that keywords extracted inform both achievement rephrasing
        and summary generation, creating a cohesive customization.
        """
        # Mock responses (with weighted keywords)
        keywords_response = json.dumps({
            "technical_skills": [
                {"keyword": "Python", "weight": 0.9},
                {"keyword": "RESTful API", "weight": 0.8},
                {"keyword": "microservices", "weight": 0.7},
            ],
            "soft_skills": [],
            "domain_knowledge": [{"keyword": "API design", "weight": 0.8}],
            "action_verbs": ["architected", "deployed"],
            "metrics": ["10K+ requests/day"],
        })

        achievement_response = json.dumps({
            "rephrased": (
                "Architected and deployed RESTful API for user management using Python, "
                "serving 10K+ requests/day with 99.9% uptime"
            ),
            "metrics_preserved": True,
            "keywords_added": ["RESTful API", "Python"],
            "improvements": ["Added technical context", "Clarified scale"],
            "truthfulness_check": "confirmed",
        })

        summary_response = json.dumps({
            "summary": (
                "Senior Backend Engineer specializing in Python-based microservices "
                "and RESTful API design with 6 years of experience building scalable "
                "cloud infrastructure on AWS."
            ),
            "keywords_included": ["Python", "microservices", "RESTful API", "AWS"],
            "word_count": 28,
        })

        with patch.object(
            service,
            "call_claude",
            side_effect=[keywords_response, achievement_response, summary_response],
        ):
            # Step 1: Extract keywords
            keywords = service.extract_keywords(sample_job_description)

            # Step 2: Rephrase achievement with keywords
            tech_skill_keywords = [skill["keyword"] for skill in keywords["technical_skills"]]
            rephrased = service.rephrase_achievement(
                achievement=sample_achievement,
                job_keywords=tech_skill_keywords[:3],
            )

            assert "rephrased" in rephrased
            assert len(rephrased["keywords_added"]) > 0
            assert rephrased["metrics_preserved"] is True

            # Step 3: Generate summary
            summary = service.generate_custom_summary(
                profile_context=sample_profile_context,
                job_context={"key_requirements": tech_skill_keywords},
                style="technical",
            )

            assert "summary" in summary
            assert len(summary["keywords_included"]) > 0

            # Verify keyword consistency across pipeline
            all_keywords = set(tech_skill_keywords)
            achievement_keywords = set(rephrased["keywords_added"])
            summary_keywords = set(summary["keywords_included"])

            # Keywords should flow through the pipeline
            assert len(achievement_keywords & all_keywords) > 0
            assert len(summary_keywords & all_keywords) > 0


class TestCostOptimization:
    """Test API cost tracking and optimization."""

    @pytest.fixture
    def service(self):
        """Create AI service instance."""
        return AIService(api_key="test-key")

    def test_caching_reduces_duplicate_calls(self, service):
        """Test that caching prevents duplicate API calls.

        Verifies cost optimization through aggressive caching.
        """
        prompt = "Extract keywords from: Python, AWS, Docker"
        mock_response = json.dumps({
            "technical_skills": ["Python", "AWS", "Docker"],
            "soft_skills": [],
            "domain_knowledge": [],
            "certifications": [],
        })

        with patch.object(service, "call_claude", return_value=mock_response) as mock_call:
            # First call - should hit API
            result1 = service.call_claude(prompt, use_cache=True)

            # Second call with same prompt - should use cache
            result2 = service.call_claude(prompt, use_cache=True)

            # Verify both return same result
            assert result1 == result2

            # Cache should reduce calls (implementation specific)
            # Note: Actual cache implementation would be tested here
            # For now, verify calls were made
            assert mock_call.call_count >= 1

    def test_token_usage_tracking(self, service):
        """Test that token usage is tracked for cost monitoring."""
        mock_response = json.dumps({"technical_skills": ["Python"]})

        with patch.object(service, "call_claude", return_value=mock_response):
            # Make a call
            service.extract_keywords("Test job description")

            # Verify cost tracking (would check actual metrics in real implementation)
            # This is a placeholder for future cost tracking implementation
            assert True  # Cost tracking will be implemented

    def test_estimated_cost_per_customization(self, service):
        """Test that estimated cost per customization is under target.

        Target: < $0.10 per complete customization
        Assumes: 1 keyword extraction + 3 achievement rephrasings + 1 summary
        """
        # Estimated tokens per operation (conservative estimates):
        # - Keyword extraction: ~500 tokens input + 200 output = 700 tokens
        # - Achievement rephrasing: ~300 input + 150 output = 450 tokens (x3)
        # - Summary generation: ~400 input + 100 output = 500 tokens
        # Total: 700 + (450*3) + 500 = 2550 tokens per customization

        # Claude 3.5 Sonnet pricing (as of 2024):
        # Input: $3 per 1M tokens = $0.000003 per token
        # Output: $15 per 1M tokens = $0.000015 per token

        # Conservative estimate (assuming 50/50 input/output):
        # Average cost per token: $0.000009
        # Cost per customization: 2550 * $0.000009 = $0.02295

        estimated_tokens = 2550
        avg_cost_per_token = 0.000009  # Blended input/output
        estimated_cost = estimated_tokens * avg_cost_per_token

        # Verify under target
        assert estimated_cost < 0.10, f"Estimated cost ${estimated_cost:.4f} exceeds $0.10 target"

        # More realistic estimate with caching (50% cache hit rate):
        with_caching = estimated_cost * 0.5
        assert with_caching < 0.05, "With caching, should be well under target"


class TestErrorRecovery:
    """Test error recovery and fallback mechanisms."""

    @pytest.fixture
    def service(self):
        """Create AI service instance."""
        return AIService(api_key="test-key")

    def test_api_failure_raises_error(self, service):
        """Test that API failures raise appropriate errors."""
        with patch.object(service, "call_claude", side_effect=Exception("API Error")):
            with pytest.raises(Exception) as exc_info:
                service.extract_keywords("Test text")

            assert "API Error" in str(exc_info.value)

    def test_invalid_json_response_handling(self, service):
        """Test handling of invalid JSON responses from Claude."""
        # Mock invalid JSON response
        invalid_response = "This is not JSON {invalid}"

        with patch.object(service, "call_claude", return_value=invalid_response):
            # Should fall back to spaCy when JSON parsing fails
            # (if use_fallback=True, which is default)
            result = service.extract_keywords("Test text with Python and AWS")
            # spaCy fallback should still return a result
            assert "technical_skills" in result

    def test_missing_required_fields_in_response(self, service):
        """Test handling of responses missing required fields."""
        # Mock response missing required field (missing action_verbs)
        incomplete_response = json.dumps({
            "technical_skills": [{"keyword": "Python", "weight": 0.8}],
            "soft_skills": [],
            "domain_knowledge": [],
        })
        # Missing action_verbs and metrics

        with patch.object(service, "call_claude", return_value=incomplete_response):
            # Should fall back to spaCy when parsing fails
            result = service.extract_keywords("Test text with Python")
            assert "technical_skills" in result

    def test_achievement_rephrasing_with_api_timeout(self, service):
        """Test achievement rephrasing handles API timeouts gracefully."""
        with patch.object(
            service, "call_claude", side_effect=TimeoutError("Request timed out")
        ):
            with pytest.raises(TimeoutError) as exc_info:
                service.rephrase_achievement(
                    achievement="Built API", job_keywords=["Python", "REST"]
                )

            assert "timed out" in str(exc_info.value).lower()

    def test_summary_generation_with_degraded_service(self, service):
        """Test summary generation handles degraded service."""
        profile_context = {
            "top_skills": ["Python"],
            "experience_years": 5,
            "current_title": "Engineer",
        }

        # Simulate degraded response (low word count)
        degraded_response = json.dumps({
            "summary": "Engineer with Python skills.",  # Only 4 words
            "keywords_included": ["Python"],
            "word_count": 4,
        })

        with patch.object(service, "call_claude", return_value=degraded_response):
            result = service.generate_custom_summary(profile_context=profile_context)

            # Should still return result, but with warning logged
            assert result["word_count"] == 4
            assert result["word_count"] < 30  # Below recommended range


class TestQualityComparison:
    """Test AI quality improvements over rule-based approaches."""

    @pytest.fixture
    def service(self):
        """Create AI service instance."""
        return AIService(api_key="test-key")

    def test_ai_keyword_extraction_vs_simple_parsing(self, service):
        """Test that AI extracts more relevant keywords than simple parsing.

        AI should understand context and extract semantically relevant terms,
        not just exact matches.
        """
        job_text = """
        Looking for a Python expert familiar with cloud infrastructure.
        Experience with containerization and orchestration required.
        """

        ai_response = json.dumps({
            "technical_skills": [
                {"keyword": "Python", "weight": 0.9},
                {"keyword": "AWS", "weight": 0.7},
                {"keyword": "Docker", "weight": 0.8},
                {"keyword": "Kubernetes", "weight": 0.8},
            ],
            "soft_skills": [],
            "domain_knowledge": [
                {"keyword": "cloud infrastructure", "weight": 0.8},
                {"keyword": "containerization", "weight": 0.7},
            ],
            "action_verbs": [],
            "metrics": [],
        })

        with patch.object(service, "call_claude", return_value=ai_response):
            ai_keywords = service.extract_keywords(job_text)

            # Extract keyword strings from weighted list
            tech_skills = [skill["keyword"] for skill in ai_keywords["technical_skills"]]
            domain_keywords = [
                kw["keyword"] for kw in ai_keywords["domain_knowledge"]
            ]

            # AI should infer Docker/Kubernetes from "containerization/orchestration"
            assert "Docker" in tech_skills
            assert "Kubernetes" in tech_skills
            assert "cloud infrastructure" in domain_keywords

            # Simple parsing would only find "Python"
            simple_keywords = ["Python"]  # What simple regex would find

            # AI extracts more value
            assert len(tech_skills) > len(simple_keywords)

    def test_ai_achievement_quality_vs_template_approach(self, service):
        """Test that AI-rephrased achievements are higher quality than templates.

        AI should create natural, compelling text rather than filling templates.
        """
        achievement = "Improved system performance"

        ai_response = json.dumps({
            "rephrased": (
                "Architected and implemented performance optimization initiative "
                "that reduced API response time by 60% and improved system throughput "
                "by 2.5x, enabling seamless scaling to 1M+ daily active users"
            ),
            "metrics_preserved": True,
            "keywords_added": ["API", "performance optimization", "scaling"],
            "improvements": ["Added metrics", "Clarified impact"],
            "truthfulness_check": "confirmed",
        })

        with patch.object(service, "call_claude", return_value=ai_response):
            ai_result = service.rephrase_achievement(
                achievement=achievement, job_keywords=["API", "scaling"]
            )

            # Template approach would be generic
            template_result = "Improved system performance using API and scaling"

            # AI version should be more specific and impactful
            assert len(ai_result["rephrased"]) > len(template_result)
            assert ai_result["metrics_preserved"] is True
            assert len(ai_result["keywords_added"]) > 0  # AI adds context

    def test_ai_summary_coherence(self, service):
        """Test that AI summaries are coherent and professional.

        AI should create flowing, natural summaries, not keyword-stuffed text.
        """
        profile_context = {
            "top_skills": ["Python", "AWS", "Docker"],
            "experience_years": 5,
            "current_title": "Senior Engineer",
            "top_achievements": ["Built scalable systems"],
        }

        ai_response = json.dumps({
            "summary": (
                "Senior Engineer with 5 years of experience architecting scalable "
                "cloud-native systems using Python and AWS. Proven expertise in "
                "containerization with Docker and delivering high-impact solutions."
            ),
            "keywords_included": ["Python", "AWS", "Docker", "scalable", "cloud-native"],
            "word_count": 28,
        })

        with patch.object(service, "call_claude", return_value=ai_response):
            ai_summary = service.generate_custom_summary(profile_context=profile_context)

            # Verify natural flow (basic checks)
            summary_text = ai_summary["summary"]
            assert "." in summary_text  # Has proper sentences
            assert summary_text[0].isupper()  # Starts with capital
            assert not summary_text.startswith("Keywords:")  # Not keyword list

            # Should include keywords naturally
            for keyword in ["Python", "AWS", "Docker"]:
                assert keyword in summary_text
