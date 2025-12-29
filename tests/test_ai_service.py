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
            "Test prompt", "Test system", "claude-3-5-sonnet-20241022", 1.0
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
            "Test prompt", "Test system", "claude-3-5-sonnet-20241022", 1.0
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
