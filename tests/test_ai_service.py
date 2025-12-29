"""
Unit tests for AI Service module.

Tests cover API calling, caching, retry logic, and error handling.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from anthropic import APIError, RateLimitError, APIConnectionError

from resume_customizer.core.ai_service import AIService, AIServiceError, get_ai_service


class TestAIServiceInitialization:
    """Test AI Service initialization."""

    def test_init_with_api_key(self, tmp_path):
        """Test initialization with explicit API key."""
        service = AIService(api_key="test-key", cache_dir=tmp_path)
        assert service.api_key == "test-key"
        assert service.cache_dir == tmp_path
        assert service.cache_dir.exists()

    def test_init_without_api_key_raises_error(self, tmp_path):
        """Test initialization without API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AIServiceError, match="ANTHROPIC_API_KEY not found"):
                AIService(cache_dir=tmp_path)

    def test_init_creates_cache_directory(self, tmp_path):
        """Test that cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "test_cache"
        assert not cache_dir.exists()

        service = AIService(api_key="test-key", cache_dir=cache_dir)

        assert cache_dir.exists()
        assert service.cache_dir == cache_dir

    def test_init_with_env_var(self, tmp_path):
        """Test initialization with API key from environment variable."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"}):
            service = AIService(cache_dir=tmp_path)
            assert service.api_key == "env-key"


class TestCallClaude:
    """Test Claude API calling functionality."""

    @pytest.fixture
    def mock_client(self):
        """Mock Anthropic client."""
        with patch("resume_customizer.core.ai_service.Anthropic") as mock:
            yield mock

    @pytest.fixture
    def service(self, tmp_path, mock_client):
        """Create AI service with mocked client."""
        return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_successful_api_call(self, service, mock_client):
        """Test successful API call returns response."""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="This is Claude's response")]
        mock_client.return_value.messages.create.return_value = mock_response

        response = service.call_claude(
            prompt="Test prompt", system_prompt="Test system", use_cache=False
        )

        assert response == "This is Claude's response"
        mock_client.return_value.messages.create.assert_called_once()

    def test_api_call_with_cache_hit(self, service, tmp_path, mock_client):
        """Test that cached responses are returned without API call."""
        # Create a cache entry
        cache_key = service._generate_cache_key(
            "Test prompt", "Test system", "claude-sonnet-4-20250514", 1.0
        )
        cache_file = tmp_path / f"{cache_key}.json"
        cache_data = {"timestamp": datetime.now().isoformat(), "response": "Cached response"}

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # Make API call
        response = service.call_claude(
            prompt="Test prompt", system_prompt="Test system", use_cache=True
        )

        assert response == "Cached response"
        # API should not be called
        mock_client.return_value.messages.create.assert_not_called()

    def test_api_call_with_expired_cache(self, service, tmp_path, mock_client):
        """Test that expired cache is ignored and API is called."""
        # Create an expired cache entry
        cache_key = service._generate_cache_key(
            "Test prompt", "Test system", "claude-sonnet-4-20250514", 1.0
        )
        cache_file = tmp_path / f"{cache_key}.json"
        expired_time = datetime.now() - timedelta(hours=25)
        cache_data = {"timestamp": expired_time.isoformat(), "response": "Expired response"}

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # Mock new response
        mock_response = Mock()
        mock_response.content = [Mock(text="Fresh response")]
        mock_client.return_value.messages.create.return_value = mock_response

        # Make API call
        response = service.call_claude(
            prompt="Test prompt", system_prompt="Test system", use_cache=True
        )

        assert response == "Fresh response"
        # API should be called
        mock_client.return_value.messages.create.assert_called_once()
        # Cache file should exist with new response (expired cache deleted, new one created)
        assert cache_file.exists()
        # Verify it contains the new response
        with open(cache_file) as f:
            data = json.load(f)
        assert data["response"] == "Fresh response"

    def test_api_call_parameters(self, service, mock_client):
        """Test that API call uses correct parameters."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_client.return_value.messages.create.return_value = mock_response

        service.call_claude(
            prompt="Test prompt",
            system_prompt="System prompt",
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.5,
            use_cache=False,
        )

        call_args = mock_client.return_value.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-opus-20240229"
        assert call_args.kwargs["max_tokens"] == 2000
        assert call_args.kwargs["temperature"] == 0.5
        assert call_args.kwargs["system"] == "System prompt"
        assert call_args.kwargs["messages"] == [{"role": "user", "content": "Test prompt"}]


class TestRetryLogic:
    """Test retry logic and error handling."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service with 2 retries for faster testing."""
        return AIService(api_key="test-key", cache_dir=tmp_path, max_retries=2)

    def test_retry_on_rate_limit_error(self, service):
        """Test that rate limit errors trigger retries."""
        with patch.object(service.client.messages, "create") as mock_create:
            # First call raises rate limit error, second succeeds
            mock_response = Mock()
            mock_response.content = [Mock(text="Success")]

            # Create proper RateLimitError with required parameters
            rate_error = RateLimitError(
                "Rate limited",
                response=Mock(status_code=429),
                body={"error": "rate_limit"}
            )
            mock_create.side_effect = [rate_error, mock_response]

            with patch("time.sleep"):  # Don't actually sleep in tests
                response = service.call_claude("Test", use_cache=False)

            assert response == "Success"
            assert mock_create.call_count == 2

    def test_retry_on_connection_error(self, service):
        """Test that connection errors trigger retries."""
        with patch.object(service.client.messages, "create") as mock_create:
            # First call raises connection error, second succeeds
            mock_response = Mock()
            mock_response.content = [Mock(text="Success")]

            # APIConnectionError needs message and request
            conn_error = APIConnectionError(message="Connection failed", request=Mock())
            mock_create.side_effect = [
                conn_error,
                mock_response,
            ]

            with patch("time.sleep"):
                response = service.call_claude("Test", use_cache=False)

            assert response == "Success"
            assert mock_create.call_count == 2

    def test_max_retries_exceeded(self, service):
        """Test that AIServiceError is raised after max retries."""
        with patch.object(service.client.messages, "create") as mock_create:
            # All calls raise rate limit error
            rate_error = RateLimitError(
                "Rate limited",
                response=Mock(status_code=429),
                body={"error": "rate_limit"}
            )
            mock_create.side_effect = rate_error

            with patch("time.sleep"):
                with pytest.raises(AIServiceError, match="API call failed after 2 attempts"):
                    service.call_claude("Test", use_cache=False)

            assert mock_create.call_count == 2

    def test_no_retry_on_api_error(self, service):
        """Test that general API errors don't trigger retries."""
        with patch.object(service.client.messages, "create") as mock_create:
            api_error = APIError(
                "Bad request",
                request=Mock(),
                body={"error": "bad_request"}
            )
            mock_create.side_effect = api_error

            with pytest.raises(AIServiceError):
                service.call_claude("Test", use_cache=False)

            # Should only be called once (no retries)
            assert mock_create.call_count == 1

    def test_exponential_backoff(self, service):
        """Test that retry delays follow exponential backoff."""
        with patch.object(service.client.messages, "create") as mock_create:
            rate_error = RateLimitError(
                "Rate limited",
                response=Mock(status_code=429),
                body={"error": "rate_limit"}
            )
            mock_create.side_effect = rate_error

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(AIServiceError):
                    service.call_claude("Test", use_cache=False)

            # Check that sleep was called with exponential backoff
            # First retry: 1.0s, second retry not reached (max retries = 2)
            assert mock_sleep.call_count == 1
            assert mock_sleep.call_args_list[0][0][0] == 1.0


class TestCaching:
    """Test caching functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service with short cache TTL for testing."""
        return AIService(api_key="test-key", cache_dir=tmp_path, cache_ttl_hours=1)

    def test_cache_key_generation(self, service):
        """Test that cache keys are generated consistently."""
        key1 = service._generate_cache_key("prompt", "system", "model", 0.5)
        key2 = service._generate_cache_key("prompt", "system", "model", 0.5)
        key3 = service._generate_cache_key("different", "system", "model", 0.5)

        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different key
        assert len(key1) == 32  # MD5 hash length

    def test_cache_response(self, service, tmp_path):
        """Test caching a response."""
        cache_key = "test_key_123"
        service._cache_response(cache_key, "Test response")

        cache_file = tmp_path / f"{cache_key}.json"
        assert cache_file.exists()

        with open(cache_file) as f:
            data = json.load(f)

        assert data["response"] == "Test response"
        assert "timestamp" in data

    def test_get_cached_response(self, service, tmp_path):
        """Test retrieving a cached response."""
        cache_key = "test_key_456"
        cache_file = tmp_path / f"{cache_key}.json"

        cache_data = {"timestamp": datetime.now().isoformat(), "response": "Cached value"}

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        response = service._get_cached_response(cache_key)
        assert response == "Cached value"

    def test_get_cached_response_not_found(self, service):
        """Test getting cached response when cache doesn't exist."""
        response = service._get_cached_response("nonexistent_key")
        assert response is None

    def test_get_cached_response_corrupted(self, service, tmp_path):
        """Test getting cached response with corrupted cache file."""
        cache_key = "corrupted_key"
        cache_file = tmp_path / f"{cache_key}.json"

        # Write invalid JSON
        with open(cache_file, "w") as f:
            f.write("not valid json")

        response = service._get_cached_response(cache_key)
        assert response is None
        # Corrupted cache should be deleted
        assert not cache_file.exists()

    def test_clear_cache(self, service, tmp_path):
        """Test clearing all cache files."""
        # Create some cache files
        for i in range(5):
            cache_file = tmp_path / f"cache_{i}.json"
            with open(cache_file, "w") as f:
                json.dump({"response": f"data{i}", "timestamp": datetime.now().isoformat()}, f)

        count = service.clear_cache()

        assert count == 5
        assert len(list(tmp_path.glob("*.json"))) == 0

    def test_clear_expired_cache(self, service, tmp_path):
        """Test clearing only expired cache entries."""
        # Create fresh cache
        fresh_cache = tmp_path / "fresh.json"
        with open(fresh_cache, "w") as f:
            json.dump({"response": "fresh", "timestamp": datetime.now().isoformat()}, f)

        # Create expired cache
        expired_time = datetime.now() - timedelta(hours=2)
        expired_cache = tmp_path / "expired.json"
        with open(expired_cache, "w") as f:
            json.dump({"response": "expired", "timestamp": expired_time.isoformat()}, f)

        count = service.clear_expired_cache()

        assert count == 1
        assert fresh_cache.exists()
        assert not expired_cache.exists()


class TestKeywordExtraction:
    """Test keyword extraction functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service with mocked client."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_extract_keywords_success(self, service):
        """Test successful keyword extraction from Claude API."""
        # Mock Claude response with valid JSON
        mock_json_response = json.dumps({
            "technical_skills": [
                {"keyword": "Python", "weight": 0.9},
                {"keyword": "Docker", "weight": 0.8}
            ],
            "domain_knowledge": [
                {"keyword": "Machine Learning", "weight": 0.7}
            ],
            "soft_skills": [
                {"keyword": "leadership", "weight": 0.6}
            ],
            "action_verbs": ["delivered", "built", "led"],
            "metrics": ["5+ years", "100% uptime"]
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            keywords = service.extract_keywords("Test job description with Python")

            assert len(keywords["technical_skills"]) == 2
            assert keywords["technical_skills"][0]["keyword"] == "Python"
            assert keywords["technical_skills"][0]["weight"] == 0.9
            assert len(keywords["action_verbs"]) == 3
            assert "delivered" in keywords["action_verbs"]

    def test_extract_keywords_with_extra_text(self, service):
        """Test keyword extraction when Claude includes extra text around JSON."""
        # Mock response with text before/after JSON
        mock_response = """Here are the extracted keywords:

{
  "technical_skills": [{"keyword": "JavaScript", "weight": 0.85}],
  "domain_knowledge": [],
  "soft_skills": [],
  "action_verbs": ["developed"],
  "metrics": []
}

Hope this helps!"""

        with patch.object(service, "call_claude", return_value=mock_response):
            keywords = service.extract_keywords("Test text")

            assert len(keywords["technical_skills"]) == 1
            assert keywords["technical_skills"][0]["keyword"] == "JavaScript"

    def test_extract_keywords_string_format_conversion(self, service):
        """Test that string keywords are converted to dict format."""
        # Mock response with string keywords instead of dicts
        mock_json_response = json.dumps({
            "technical_skills": ["Python", "Docker"],  # Strings instead of dicts
            "domain_knowledge": [{"keyword": "FinTech", "weight": 0.7}],
            "soft_skills": [],
            "action_verbs": [],
            "metrics": []
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            keywords = service.extract_keywords("Test text")

            # Should convert strings to dicts with default weight
            assert keywords["technical_skills"][0]["keyword"] == "Python"
            assert keywords["technical_skills"][0]["weight"] == 0.5

    def test_extract_keywords_missing_fields(self, service):
        """Test handling of incomplete JSON response."""
        # Mock response missing some fields
        mock_json_response = json.dumps({
            "technical_skills": [{"keyword": "Python", "weight": 0.9}],
            # Missing other required fields
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            with pytest.raises(AIServiceError):
                service.extract_keywords("Test text", use_fallback=False)

    def test_extract_keywords_invalid_json(self, service):
        """Test handling of invalid JSON response."""
        with patch.object(service, "call_claude", return_value="Not valid JSON"):
            with pytest.raises(AIServiceError):
                service.extract_keywords("Test text", use_fallback=False)

    def test_extract_keywords_caching(self, service):
        """Test that keyword extraction uses caching."""
        mock_json_response = json.dumps({
            "technical_skills": [],
            "domain_knowledge": [],
            "soft_skills": [],
            "action_verbs": [],
            "metrics": []
        })

        with patch.object(service, "call_claude", return_value=mock_json_response) as mock_call:
            # First call
            service.extract_keywords("Test text", use_cache=True)
            # Second call with same text
            service.extract_keywords("Test text", use_cache=True)

            # call_claude should be called twice (it handles its own caching)
            assert mock_call.call_count == 2
            # Verify use_cache parameter is passed
            assert mock_call.call_args.kwargs["use_cache"] is True

    @patch("resume_customizer.core.ai_service.SPACY_AVAILABLE", True)
    def test_extract_keywords_fallback_to_spacy(self, service):
        """Test fallback to spaCy when Claude API fails."""
        # Mock Claude API to fail
        with patch.object(
            service, "call_claude", side_effect=AIServiceError("API failed")
        ):
            # Mock spaCy extraction
            with patch.object(
                service,
                "_extract_keywords_spacy",
                return_value={
                    "technical_skills": [{"keyword": "Python", "weight": 0.6}],
                    "domain_knowledge": [],
                    "soft_skills": [],
                    "action_verbs": ["develop"],
                    "metrics": []
                }
            ) as mock_spacy:
                keywords = service.extract_keywords("Test text", use_fallback=True)

                # Should call spaCy fallback
                mock_spacy.assert_called_once()
                assert len(keywords["technical_skills"]) == 1

    def test_extract_keywords_no_fallback(self, service):
        """Test that extraction fails without fallback when API fails."""
        with patch.object(
            service, "call_claude", side_effect=AIServiceError("API failed")
        ):
            with pytest.raises(AIServiceError, match="Keyword extraction failed"):
                service.extract_keywords("Test text", use_fallback=False)


class TestSpacyFallback:
    """Test spaCy fallback functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    @patch("resume_customizer.core.ai_service.SPACY_AVAILABLE", True)
    @patch("resume_customizer.core.ai_service.spacy")
    def test_spacy_extraction_basic(self, mock_spacy_module, service):
        """Test basic spaCy extraction functionality."""
        # Mock spaCy model and document
        mock_nlp = Mock()
        mock_doc = Mock()

        # Mock tokens
        mock_token = Mock()
        mock_token.pos_ = "NOUN"
        mock_token.text = "Python"
        mock_token.is_stop = False
        mock_token.lemma_ = "develop"

        mock_doc.__iter__ = Mock(return_value=iter([mock_token]))
        mock_doc.noun_chunks = []
        mock_doc.ents = []

        mock_nlp.return_value = mock_doc
        mock_spacy_module.load.return_value = mock_nlp

        keywords = service._extract_keywords_spacy("Test text with Python")

        assert "technical_skills" in keywords
        assert "domain_knowledge" in keywords
        assert "soft_skills" in keywords
        assert "action_verbs" in keywords
        assert "metrics" in keywords

    @patch("resume_customizer.core.ai_service.SPACY_AVAILABLE", False)
    def test_spacy_not_available(self, service):
        """Test error when spaCy is not available."""
        with pytest.raises(AIServiceError, match="spaCy not available"):
            service._extract_keywords_spacy("Test text")

    @patch("resume_customizer.core.ai_service.SPACY_AVAILABLE", True)
    @patch("resume_customizer.core.ai_service.spacy")
    def test_spacy_model_not_installed(self, mock_spacy_module, service):
        """Test error when spaCy model is not installed."""
        mock_spacy_module.load.side_effect = OSError("Model not found")

        with pytest.raises(AIServiceError, match="spaCy model not installed"):
            service._extract_keywords_spacy("Test text")


class TestParseKeywordResponse:
    """Test keyword response parsing."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_parse_valid_json(self, service):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "technical_skills": [{"keyword": "Python", "weight": 0.9}],
            "domain_knowledge": [],
            "soft_skills": [],
            "action_verbs": [],
            "metrics": []
        })

        keywords = service._parse_keyword_response(response)

        assert keywords["technical_skills"][0]["keyword"] == "Python"
        assert keywords["technical_skills"][0]["weight"] == 0.9

    def test_parse_json_with_surrounding_text(self, service):
        """Test parsing JSON with extra text."""
        response = """Here's the result:

{"technical_skills": [], "domain_knowledge": [], "soft_skills": [], "action_verbs": [], "metrics": []}

Done!"""

        keywords = service._parse_keyword_response(response)

        assert isinstance(keywords, dict)
        assert "technical_skills" in keywords

    def test_parse_missing_json(self, service):
        """Test error when JSON is not found."""
        with pytest.raises(json.JSONDecodeError, match="No JSON object found"):
            service._parse_keyword_response("No JSON here")

    def test_parse_invalid_json(self, service):
        """Test error with invalid JSON syntax."""
        with pytest.raises(json.JSONDecodeError):
            service._parse_keyword_response("{invalid json}")

    def test_parse_missing_required_field(self, service):
        """Test error when required field is missing."""
        response = json.dumps({
            "technical_skills": []
            # Missing other required fields
        })

        with pytest.raises(KeyError, match="Missing required field"):
            service._parse_keyword_response(response)

    def test_parse_validates_structure(self, service):
        """Test that parser validates and fixes structure."""
        # Non-list values should be converted to empty lists
        response = json.dumps({
            "technical_skills": "not a list",
            "domain_knowledge": None,
            "soft_skills": [],
            "action_verbs": "also not a list",
            "metrics": []
        })

        keywords = service._parse_keyword_response(response)

        # Should convert invalid values to empty lists
        assert keywords["technical_skills"] == []
        assert keywords["domain_knowledge"] == []
        assert keywords["action_verbs"] == []


class TestAchievementRephrasing:
    """Test achievement rephrasing functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service with mocked client."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_rephrase_achievement_success(self, service):
        """Test successful achievement rephrasing."""
        mock_json_response = json.dumps({
            "rephrased": "Developed a scalable Python microservices platform that improved system performance by 40%",
            "metrics_preserved": True,
            "keywords_added": ["Python", "scalable", "microservices"],
            "improvements": ["Added technical context", "Clarified impact"],
            "truthfulness_check": "confirmed"
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.rephrase_achievement(
                "Built a web app that improved performance by 40%",
                job_keywords=["Python", "scalable", "microservices"],
                style="technical"
            )

            assert result["original"] == "Built a web app that improved performance by 40%"
            assert "40%" in result["rephrased"]
            assert result["metrics_preserved"] is True
            assert len(result["keywords_added"]) == 3
            assert result["style"] == "technical"

    def test_rephrase_achievement_balanced_style(self, service):
        """Test rephrasing with balanced style."""
        mock_json_response = json.dumps({
            "rephrased": "Led development of authentication system reducing login failures by 95%",
            "metrics_preserved": True,
            "keywords_added": ["authentication"],
            "improvements": ["Improved clarity"],
            "truthfulness_check": "confirmed"
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.rephrase_achievement(
                "Made login better, reduced failures by 95%",
                style="balanced"
            )

            assert result["style"] == "balanced"
            assert "95%" in result["rephrased"]

    def test_rephrase_achievement_results_style(self, service):
        """Test rephrasing with results-focused style."""
        mock_json_response = json.dumps({
            "rephrased": "Delivered 30% cost reduction through infrastructure optimization",
            "metrics_preserved": True,
            "keywords_added": ["cost reduction"],
            "improvements": ["Emphasized business impact"],
            "truthfulness_check": "confirmed"
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.rephrase_achievement(
                "Optimized infrastructure saving 30% costs",
                style="results"
            )

            assert result["style"] == "results"
            assert "30%" in result["rephrased"]

    def test_rephrase_achievement_invalid_style(self, service):
        """Test that invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Invalid style"):
            service.rephrase_achievement(
                "Some achievement",
                style="invalid_style"
            )

    def test_rephrase_achievement_without_keywords(self, service):
        """Test rephrasing without job keywords."""
        mock_json_response = json.dumps({
            "rephrased": "Improved system throughput by 50%",
            "metrics_preserved": True,
            "keywords_added": [],
            "improvements": ["Better clarity"],
            "truthfulness_check": "confirmed"
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.rephrase_achievement(
                "Made system faster by 50%"
            )

            assert len(result["keywords_added"]) == 0
            assert "50%" in result["rephrased"]

    def test_rephrase_achievement_metrics_validation_failure(self, service):
        """Test that metrics validation detects missing numbers."""
        # Mock response that loses metrics
        mock_json_response = json.dumps({
            "rephrased": "Built a web application that improved performance",
            "metrics_preserved": True,
            "keywords_added": [],
            "improvements": ["Simplified"],
            "truthfulness_check": "confirmed"
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.rephrase_achievement(
                "Built a web app that improved performance by 40%"
            )

            # Metrics validation should detect missing 40%
            assert result["metrics_preserved"] is False

    def test_rephrase_achievement_truthfulness_warning(self, service):
        """Test warning when truthfulness check fails."""
        mock_json_response = json.dumps({
            "rephrased": "Some rephrased text",
            "metrics_preserved": True,
            "keywords_added": [],
            "improvements": [],
            "truthfulness_check": "not_confirmed"  # Failed check
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            # Should still return but log warning
            result = service.rephrase_achievement("Original text")
            assert "rephrased" in result

    def test_rephrase_achievement_api_failure(self, service):
        """Test handling of API failures."""
        with patch.object(service, "call_claude", side_effect=AIServiceError("API failed")):
            with pytest.raises(AIServiceError, match="Failed to rephrase achievement"):
                service.rephrase_achievement("Some achievement")

    def test_rephrase_achievement_invalid_json(self, service):
        """Test handling of invalid JSON response."""
        with patch.object(service, "call_claude", return_value="Not valid JSON"):
            with pytest.raises(AIServiceError, match="Failed to rephrase achievement"):
                service.rephrase_achievement("Some achievement")

    def test_rephrase_achievement_missing_fields(self, service):
        """Test handling of incomplete JSON response."""
        mock_json_response = json.dumps({
            "rephrased": "Some text",
            # Missing required fields
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            with pytest.raises(AIServiceError):
                service.rephrase_achievement("Some achievement")


class TestParseRephraseResponse:
    """Test rephrase response parsing."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_parse_valid_rephrase_response(self, service):
        """Test parsing valid rephrase response."""
        response = json.dumps({
            "rephrased": "Improved text",
            "metrics_preserved": True,
            "keywords_added": ["keyword1"],
            "improvements": ["improvement1"],
            "truthfulness_check": "confirmed"
        })

        result = service._parse_rephrase_response(response)

        assert result["rephrased"] == "Improved text"
        assert result["metrics_preserved"] is True
        assert len(result["keywords_added"]) == 1

    def test_parse_rephrase_with_extra_text(self, service):
        """Test parsing response with extra text."""
        response = """Here's the rephrased version:

{
  "rephrased": "Better text",
  "metrics_preserved": true,
  "keywords_added": [],
  "improvements": [],
  "truthfulness_check": "confirmed"
}

Hope this helps!"""

        result = service._parse_rephrase_response(response)
        assert result["rephrased"] == "Better text"

    def test_parse_rephrase_missing_json(self, service):
        """Test error when JSON not found."""
        with pytest.raises(json.JSONDecodeError, match="No JSON object found"):
            service._parse_rephrase_response("No JSON here")

    def test_parse_rephrase_missing_field(self, service):
        """Test error when required field missing."""
        response = json.dumps({
            "rephrased": "Text",
            # Missing other required fields
        })

        with pytest.raises(KeyError, match="Missing required field"):
            service._parse_rephrase_response(response)

    def test_parse_rephrase_invalid_lists(self, service):
        """Test that invalid list values are converted."""
        response = json.dumps({
            "rephrased": "Text",
            "metrics_preserved": True,
            "keywords_added": "not a list",  # Invalid
            "improvements": None,  # Invalid
            "truthfulness_check": "confirmed"
        })

        result = service._parse_rephrase_response(response)
        assert result["keywords_added"] == []
        assert result["improvements"] == []


class TestValidateMetricsPreserved:
    """Test metrics validation functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_validate_metrics_all_preserved(self, service):
        """Test validation when all metrics are preserved."""
        original = "Improved performance by 40% and reduced costs by $50K"
        rephrased = "Enhanced system performance by 40% while decreasing costs by $50K"

        assert service._validate_metrics_preserved(original, rephrased) is True

    def test_validate_metrics_missing_percentage(self, service):
        """Test validation detects missing percentage."""
        original = "Improved performance by 40%"
        rephrased = "Improved performance significantly"

        assert service._validate_metrics_preserved(original, rephrased) is False

    def test_validate_metrics_missing_number(self, service):
        """Test validation detects missing number."""
        original = "Reduced latency by 500ms"
        rephrased = "Reduced latency significantly"

        assert service._validate_metrics_preserved(original, rephrased) is False

    def test_validate_metrics_with_k_suffix(self, service):
        """Test validation with K/M/B suffixes."""
        original = "Saved $50K annually"
        rephrased = "Achieved $50K in annual savings"

        assert service._validate_metrics_preserved(original, rephrased) is True

    def test_validate_metrics_decimal_numbers(self, service):
        """Test validation with decimal numbers."""
        original = "Improved accuracy by 99.9%"
        rephrased = "Increased accuracy to 99.9%"

        assert service._validate_metrics_preserved(original, rephrased) is True

    def test_validate_metrics_no_metrics(self, service):
        """Test validation when no metrics present."""
        original = "Built a web application"
        rephrased = "Developed a web application"

        # No metrics to preserve, should pass
        assert service._validate_metrics_preserved(original, rephrased) is True

    def test_validate_metrics_case_insensitive(self, service):
        """Test validation is case insensitive."""
        original = "Reduced costs by 25%"
        rephrased = "REDUCED COSTS BY 25%"

        assert service._validate_metrics_preserved(original, rephrased) is True


class TestSummaryGeneration:
    """Test summary generation functionality."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service with mocked client."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    @pytest.fixture
    def profile_context(self):
        """Sample profile context."""
        return {
            "top_skills": ["Python", "AWS", "Docker", "Kubernetes"],
            "experience_years": 5,
            "current_title": "Senior Software Engineer",
            "domain": "Backend Development",
            "top_achievements": [
                "Built scalable API serving 1M users",
                "Reduced infrastructure costs by 40%"
            ]
        }

    @pytest.fixture
    def job_context(self):
        """Sample job context."""
        return {
            "title": "Lead Backend Engineer",
            "company": "TechCorp",
            "key_requirements": ["Python", "microservices", "cloud", "team leadership"],
            "industry": "SaaS"
        }

    def test_generate_summary_success(self, service, profile_context, job_context):
        """Test successful summary generation."""
        mock_json_response = json.dumps({
            "summary": "Senior Software Engineer with 5 years of experience in Backend Development, "
                      "specializing in Python, AWS, and Docker. Built scalable API serving 1M users "
                      "and reduced infrastructure costs by 40%.",
            "keywords_included": ["Python", "AWS", "Docker", "scalable", "Backend Development"],
            "word_count": 42
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.generate_custom_summary(
                profile_context=profile_context,
                job_context=job_context,
                style="technical"
            )

            assert "summary" in result
            assert result["word_count"] == 42
            assert len(result["keywords_included"]) == 5
            assert result["style"] == "technical"

    def test_generate_summary_balanced_style(self, service, profile_context):
        """Test summary generation with balanced style."""
        mock_json_response = json.dumps({
            "summary": "Experienced Senior Software Engineer with 5 years in Backend Development. "
                      "Combines technical expertise in Python and AWS with proven results.",
            "keywords_included": ["Python", "AWS", "Backend Development"],
            "word_count": 28
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.generate_custom_summary(
                profile_context=profile_context,
                style="balanced"
            )

            assert result["style"] == "balanced"
            assert "summary" in result

    def test_generate_summary_results_style(self, service, profile_context, job_context):
        """Test summary generation with results-focused style."""
        mock_json_response = json.dumps({
            "summary": "Results-driven Senior Software Engineer who built scalable API serving 1M users "
                      "and reduced infrastructure costs by 40%. Proven track record of delivering impact.",
            "keywords_included": ["scalable", "1M users", "40%", "impact"],
            "word_count": 35
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.generate_custom_summary(
                profile_context=profile_context,
                job_context=job_context,
                style="results"
            )

            assert result["style"] == "results"
            assert "40%" in result["summary"]

    def test_generate_summary_without_job_context(self, service, profile_context):
        """Test summary generation without job context."""
        mock_json_response = json.dumps({
            "summary": "Senior Software Engineer with 5 years of Backend Development experience.",
            "keywords_included": ["Backend Development"],
            "word_count": 12
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.generate_custom_summary(
                profile_context=profile_context
            )

            assert "summary" in result
            assert result["style"] == "balanced"  # Default style

    def test_generate_summary_invalid_style(self, service, profile_context):
        """Test that invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Invalid style"):
            service.generate_custom_summary(
                profile_context=profile_context,
                style="invalid_style"
            )

    def test_generate_summary_missing_required_field(self, service):
        """Test that missing required field raises ValueError."""
        incomplete_context = {
            "top_skills": ["Python"],
            # Missing experience_years and current_title
        }

        with pytest.raises(ValueError, match="Missing required profile_context field"):
            service.generate_custom_summary(profile_context=incomplete_context)

    def test_generate_summary_word_count_warning(self, service, profile_context):
        """Test warning when word count is outside recommended range."""
        # Very short summary
        mock_json_response = json.dumps({
            "summary": "Short summary.",
            "keywords_included": [],
            "word_count": 2
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.generate_custom_summary(profile_context=profile_context)
            # Should still return but log warning
            assert result["word_count"] == 2

    def test_generate_summary_api_failure(self, service, profile_context):
        """Test handling of API failures."""
        with patch.object(service, "call_claude", side_effect=AIServiceError("API failed")):
            with pytest.raises(AIServiceError, match="Failed to generate summary"):
                service.generate_custom_summary(profile_context=profile_context)

    def test_generate_summary_invalid_json(self, service, profile_context):
        """Test handling of invalid JSON response."""
        with patch.object(service, "call_claude", return_value="Not valid JSON"):
            with pytest.raises(AIServiceError, match="Failed to generate summary"):
                service.generate_custom_summary(profile_context=profile_context)

    def test_generate_summary_with_optional_fields(self, service):
        """Test summary generation with minimal required fields."""
        minimal_context = {
            "top_skills": ["Python", "JavaScript"],
            "experience_years": 3,
            "current_title": "Software Engineer"
            # No domain or achievements
        }

        mock_json_response = json.dumps({
            "summary": "Software Engineer with 3 years of experience in Python and JavaScript.",
            "keywords_included": ["Python", "JavaScript"],
            "word_count": 12
        })

        with patch.object(service, "call_claude", return_value=mock_json_response):
            result = service.generate_custom_summary(profile_context=minimal_context)
            assert "summary" in result


class TestParseSummaryResponse:
    """Test summary response parsing."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create AI service."""
        with patch("resume_customizer.core.ai_service.Anthropic"):
            return AIService(api_key="test-key", cache_dir=tmp_path)

    def test_parse_valid_summary_response(self, service):
        """Test parsing valid summary response."""
        response = json.dumps({
            "summary": "Great professional summary here.",
            "keywords_included": ["keyword1", "keyword2"],
            "word_count": 5
        })

        result = service._parse_summary_response(response)

        assert result["summary"] == "Great professional summary here."
        assert len(result["keywords_included"]) == 2
        assert result["word_count"] == 5

    def test_parse_summary_with_extra_text(self, service):
        """Test parsing response with extra text."""
        response = """Here's your summary:

{
  "summary": "Professional summary text.",
  "keywords_included": ["skill1"],
  "word_count": 3
}

Hope this helps!"""

        result = service._parse_summary_response(response)
        assert result["summary"] == "Professional summary text."

    def test_parse_summary_missing_json(self, service):
        """Test error when JSON not found."""
        with pytest.raises(json.JSONDecodeError, match="No JSON object found"):
            service._parse_summary_response("No JSON here")

    def test_parse_summary_missing_field(self, service):
        """Test error when required field missing."""
        response = json.dumps({
            "summary": "Text",
            # Missing other required fields
        })

        with pytest.raises(KeyError, match="Missing required field"):
            service._parse_summary_response(response)

    def test_parse_summary_invalid_keywords_type(self, service):
        """Test that invalid keywords type is converted."""
        response = json.dumps({
            "summary": "Text",
            "keywords_included": "not a list",  # Invalid
            "word_count": 5
        })

        result = service._parse_summary_response(response)
        assert result["keywords_included"] == []

    def test_parse_summary_invalid_word_count(self, service):
        """Test that invalid word count is calculated from summary."""
        response = json.dumps({
            "summary": "This is a test summary with words",
            "keywords_included": [],
            "word_count": "not an integer"  # Invalid
        })

        result = service._parse_summary_response(response)
        # Should calculate from summary
        assert result["word_count"] == 7


class TestGetAIService:
    """Test singleton service getter."""

    def test_get_ai_service_creates_singleton(self):
        """Test that get_ai_service returns singleton instance."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            # Reset singleton
            import resume_customizer.core.ai_service

            resume_customizer.core.ai_service._ai_service = None

            service1 = get_ai_service()
            service2 = get_ai_service()

            assert service1 is service2

    def test_get_ai_service_without_api_key(self):
        """Test that get_ai_service raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            # Reset singleton
            import resume_customizer.core.ai_service

            resume_customizer.core.ai_service._ai_service = None

            with pytest.raises(AIServiceError):
                get_ai_service()
