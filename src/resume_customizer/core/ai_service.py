"""
AI Service Module for Resume Customizer.

This module provides interfaces to Claude AI for keyword extraction,
achievement rephrasing, and other AI-powered features.
"""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError
from dotenv import load_dotenv

from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


def _get_config_value(key: str, default: Any) -> Any:
    """Get configuration value from environment."""
    return os.getenv(key, default)


# Configuration defaults
DEFAULT_CACHE_DIR = Path(".cache")
DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_RETRY_DELAY = 1.0


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class AIService:
    """Service for interacting with Claude AI API."""

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | None = None,
        cache_ttl_hours: int | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize AI Service.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
            cache_dir: Directory for caching responses
            cache_ttl_hours: Cache time-to-live in hours
            max_retries: Maximum number of retry attempts

        Raises:
            AIServiceError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise AIServiceError(
                "ANTHROPIC_API_KEY not found. Please set it in .env file or pass it to AIService."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.cache_dir = cache_dir or Path(_get_config_value("CACHE_DIR", ".cache"))
        self.cache_ttl_hours = (
            cache_ttl_hours
            if cache_ttl_hours is not None
            else int(_get_config_value("CACHE_TTL_HOURS", str(DEFAULT_CACHE_TTL_HOURS)))
        )
        self.max_retries = (
            max_retries
            if max_retries is not None
            else int(_get_config_value("MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        )

        # Create cache directory if it does not exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"AI Service initialized with cache dir: {self.cache_dir}")

    def call_claude(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        use_cache: bool = True,
    ) -> str:
        """
        Call Claude API with retry logic and caching.

        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt for context
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation (0.0-1.0)
            use_cache: Whether to use cached responses

        Returns:
            Claude response text

        Raises:
            AIServiceError: If API call fails after retries

        Example:
            >>> service = AIService()
            >>> response = service.call_claude(
            ...     "Extract keywords from: Built scalable APIs",
            ...     system_prompt="You are a keyword extraction expert"
            ... )
        """
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(prompt, system_prompt, model, temperature)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Cache hit for prompt: {prompt[:50]}...")
                return cached_response

        # Prepare messages
        messages = [{"role": "user", "content": prompt}]

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Calling Claude API (attempt {attempt + 1}/{self.max_retries}): "
                    f"model={model}, prompt_length={len(prompt)}"
                )

                # Make API call
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else [],
                    messages=messages,
                )

                # Extract text from response
                response_text = response.content[0].text

                # Cache the response
                if use_cache:
                    self._cache_response(cache_key, response_text)

                logger.info(
                    f"API call successful, response length: {len(response_text)} characters"
                )
                return response_text

            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = DEFAULT_INITIAL_RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Rate limit error, retrying in {delay}s (attempt {attempt + 1})"
                    )
                    time.sleep(delay)
                else:
                    logger.error("Rate limit error: Max retries exceeded")

            except APIConnectionError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = DEFAULT_INITIAL_RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Connection error, retrying in {delay}s (attempt {attempt + 1})"
                    )
                    time.sleep(delay)
                else:
                    logger.error("Connection error: Max retries exceeded")

            except APIError as e:
                last_error = e
                logger.error(f"API error: {str(e)}")
                # Do not retry on general API errors
                break

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {str(e)}")
                break

        # All retries failed
        error_msg = f"API call failed after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise AIServiceError(error_msg)

    def _generate_cache_key(
        self, prompt: str, system_prompt: str | None, model: str, temperature: float
    ) -> str:
        """
        Generate a unique cache key for the request.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            model: Model name
            temperature: Temperature setting

        Returns:
            Cache key (MD5 hash)
        """
        # Combine all parameters that affect the response
        cache_input = f"{prompt}|{system_prompt}|{model}|{temperature}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> str | None:
        """
        Get cached response if it exists and has not expired.

        Args:
            cache_key: Cache key to lookup

        Returns:
            Cached response text or None if not found/expired
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check if cache has expired
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            expiry_time = cached_time + timedelta(hours=self.cache_ttl_hours)

            if datetime.now() > expiry_time:
                logger.info(f"Cache expired for key: {cache_key}")
                cache_file.unlink()  # Delete expired cache
                return None

            return cache_data["response"]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Invalid cache file for key {cache_key}: {e}")
            cache_file.unlink()  # Delete corrupted cache
            return None

    def _cache_response(self, cache_key: str, response: str) -> None:
        """
        Cache the API response.

        Args:
            cache_key: Cache key
            response: Response text to cache
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {"timestamp": datetime.now().isoformat(), "response": response}

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Cached response for key: {cache_key}")

        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

    def clear_cache(self) -> int:
        """
        Clear all cached responses.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache files")
        return count

    def clear_expired_cache(self) -> int:
        """
        Clear only expired cache entries.

        Returns:
            Number of expired cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                cached_time = datetime.fromisoformat(cache_data["timestamp"])
                expiry_time = cached_time + timedelta(hours=self.cache_ttl_hours)

                if datetime.now() > expiry_time:
                    cache_file.unlink()
                    count += 1

            except Exception as e:
                logger.warning(f"Error processing cache file {cache_file}: {e}")
                # Delete corrupted files
                try:
                    cache_file.unlink()
                    count += 1
                except Exception:
                    pass

        logger.info(f"Cleared {count} expired cache files")
        return count


# Singleton instance for convenience
_ai_service: AIService | None = None


def get_ai_service() -> AIService:
    """
    Get the singleton AI service instance.

    Returns:
        AIService instance

    Raises:
        AIServiceError: If API key is not configured
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
