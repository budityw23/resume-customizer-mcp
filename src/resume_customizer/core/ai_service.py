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

# Try to import spaCy for fallback keyword extraction
try:
    import spacy
    from spacy.language import Language

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Keyword extraction will only use Claude API.")


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

    def extract_keywords(
        self,
        text: str,
        use_cache: bool = True,
        use_fallback: bool = True,
    ) -> dict[str, Any]:
        """
        Extract keywords from text using Claude API with spaCy fallback.

        This function extracts and categorizes keywords into technical skills,
        domain knowledge, and soft skills. It uses Claude AI for intelligent
        extraction and falls back to spaCy NLP when the API is unavailable.

        Args:
            text: The text to extract keywords from (job description, resume, etc.)
            use_cache: Whether to use cached responses (default: True)
            use_fallback: Whether to use spaCy fallback on API failure (default: True)

        Returns:
            Dictionary with categorized keywords:
            {
                "technical_skills": [{"keyword": str, "weight": float}, ...],
                "domain_knowledge": [{"keyword": str, "weight": float}, ...],
                "soft_skills": [{"keyword": str, "weight": float}, ...],
                "action_verbs": [str, ...],
                "metrics": [str, ...]
            }

        Raises:
            AIServiceError: If both API and fallback fail

        Example:
            >>> service = AIService()
            >>> keywords = service.extract_keywords(
            ...     "Looking for a Python developer with 5 years of experience..."
            ... )
            >>> print(keywords["technical_skills"])
            [{"keyword": "Python", "weight": 0.95}, ...]
        """
        # Try Claude API first
        try:
            system_prompt = """You are an expert at extracting keywords from job descriptions and resumes.
Extract and categorize keywords into:
1. Technical Skills (programming languages, frameworks, tools, technologies)
2. Domain Knowledge (industry terms, business domains, methodologies)
3. Soft Skills (communication, leadership, teamwork, etc.)
4. Action Verbs (delivered, built, led, improved, etc.)
5. Metrics (numbers, percentages, achievements with quantifiable results)

For skills and domain knowledge, assign a weight (0.0-1.0) based on:
- Explicit "required" or "must-have" → 1.0
- Emphasized (repeated, in requirements) → 0.8-0.9
- Mentioned (in nice-to-have, description) → 0.5-0.7
- Implied or context-only → 0.3-0.4

Return your response as a valid JSON object with this exact structure:
{
  "technical_skills": [{"keyword": "Python", "weight": 0.9}, ...],
  "domain_knowledge": [{"keyword": "FinTech", "weight": 0.7}, ...],
  "soft_skills": [{"keyword": "leadership", "weight": 0.6}, ...],
  "action_verbs": ["delivered", "built", "led", ...],
  "metrics": ["5+ years", "100% uptime", "30% improvement", ...]
}

Only return the JSON object, no other text."""

            prompt = f"""Extract keywords from the following text:

{text}"""

            response = self.call_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more consistent extraction
                use_cache=use_cache,
            )

            # Parse JSON response
            keywords = self._parse_keyword_response(response)

            logger.info(
                f"Extracted {len(keywords['technical_skills'])} technical skills, "
                f"{len(keywords['domain_knowledge'])} domain keywords, "
                f"{len(keywords['soft_skills'])} soft skills"
            )

            return keywords

        except (AIServiceError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Claude API keyword extraction failed: {e}")

            if use_fallback and SPACY_AVAILABLE:
                logger.info("Falling back to spaCy extraction")
                return self._extract_keywords_spacy(text)
            else:
                error_msg = "Keyword extraction failed and no fallback available"
                logger.error(error_msg)
                raise AIServiceError(error_msg) from e

    def _parse_keyword_response(self, response: str) -> dict[str, Any]:
        """
        Parse and validate Claude's JSON response for keyword extraction.

        Args:
            response: Raw response text from Claude

        Returns:
            Validated keyword dictionary

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If required fields are missing
        """
        # Try to extract JSON from response (in case there's extra text)
        response = response.strip()

        # Find JSON object boundaries
        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            raise json.JSONDecodeError("No JSON object found", response, 0)

        json_str = response[start:end]
        keywords = json.loads(json_str)

        # Validate required fields
        required_fields = [
            "technical_skills",
            "domain_knowledge",
            "soft_skills",
            "action_verbs",
            "metrics",
        ]
        for field in required_fields:
            if field not in keywords:
                raise KeyError(f"Missing required field: {field}")

        # Validate structure
        for skill_type in ["technical_skills", "domain_knowledge", "soft_skills"]:
            if not isinstance(keywords[skill_type], list):
                keywords[skill_type] = []

            # Ensure each item has keyword and weight
            validated_items = []
            for item in keywords[skill_type]:
                if isinstance(item, dict) and "keyword" in item and "weight" in item:
                    validated_items.append(item)
                elif isinstance(item, str):
                    # Convert string to dict with default weight
                    validated_items.append({"keyword": item, "weight": 0.5})

            keywords[skill_type] = validated_items

        # Validate lists
        for list_type in ["action_verbs", "metrics"]:
            if not isinstance(keywords[list_type], list):
                keywords[list_type] = []

        return keywords

    def _extract_keywords_spacy(self, text: str) -> dict[str, Any]:
        """
        Fallback keyword extraction using spaCy NLP.

        This is a rule-based extraction that's less sophisticated than
        Claude but provides basic functionality when the API is unavailable.

        Args:
            text: Text to extract keywords from

        Returns:
            Dictionary with categorized keywords (same format as extract_keywords)
        """
        if not SPACY_AVAILABLE:
            raise AIServiceError("spaCy not available for fallback extraction")

        try:
            # Load spaCy model
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.error(
                    "spaCy model 'en_core_web_sm' not found. "
                    "Run: python -m spacy download en_core_web_sm"
                )
                raise AIServiceError("spaCy model not installed")

            doc = nlp(text)

            # Extract technical skills (nouns that might be technologies)
            technical_skills = []
            tech_keywords = {
                "python",
                "javascript",
                "java",
                "react",
                "node",
                "docker",
                "kubernetes",
                "aws",
                "azure",
                "gcp",
                "sql",
                "nosql",
                "api",
                "rest",
                "graphql",
                "git",
                "ci/cd",
                "agile",
                "scrum",
            }

            for token in doc:
                if (
                    token.pos_ in ["NOUN", "PROPN"]
                    and token.text.lower() in tech_keywords
                ):
                    technical_skills.append({"keyword": token.text, "weight": 0.6})

            # Extract noun chunks as potential domain knowledge
            domain_knowledge = []
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:  # Multi-word phrases
                    domain_knowledge.append({"keyword": chunk.text, "weight": 0.5})

            # Extract adjectives as potential soft skills
            soft_skills = []
            soft_skill_words = {
                "collaborative",
                "creative",
                "analytical",
                "detail-oriented",
                "team",
                "leadership",
                "communication",
            }

            for token in doc:
                if token.pos_ == "ADJ" and token.text.lower() in soft_skill_words:
                    soft_skills.append({"keyword": token.text, "weight": 0.5})

            # Extract action verbs
            action_verbs = []
            for token in doc:
                if token.pos_ == "VERB" and not token.is_stop:
                    action_verbs.append(token.lemma_)

            # Extract metrics (numbers with context)
            metrics = []
            for ent in doc.ents:
                if ent.label_ in ["PERCENT", "QUANTITY", "CARDINAL"]:
                    # Get surrounding context
                    start = max(0, ent.start - 2)
                    end = min(len(doc), ent.end + 2)
                    context = doc[start:end].text
                    metrics.append(context)

            logger.info(
                f"spaCy fallback extracted {len(technical_skills)} technical skills, "
                f"{len(domain_knowledge)} domain keywords, "
                f"{len(soft_skills)} soft skills"
            )

            return {
                "technical_skills": technical_skills[:20],  # Limit results
                "domain_knowledge": domain_knowledge[:15],
                "soft_skills": soft_skills[:10],
                "action_verbs": list(set(action_verbs))[:20],
                "metrics": list(set(metrics))[:10],
            }

        except Exception as e:
            logger.error(f"spaCy keyword extraction failed: {e}")
            raise AIServiceError(f"Fallback extraction failed: {e}") from e


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
