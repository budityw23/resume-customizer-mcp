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
        model: str = "claude-sonnet-4-20250514",
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
                model="claude-sonnet-4-20250514",
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

    def rephrase_achievement(
        self,
        achievement: str,
        job_keywords: list[str] | None = None,
        style: str = "balanced",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Rephrase an achievement to better align with job requirements.

        This function uses Claude to rephrase achievements while:
        - Preserving the original meaning and all metrics
        - Naturally incorporating relevant job keywords
        - Optimizing for ATS (Applicant Tracking Systems)
        - Maintaining truthfulness (no exaggeration or fabrication)
        - Improving clarity and impact

        Args:
            achievement: The original achievement text to rephrase
            job_keywords: Optional list of keywords from job description to incorporate
            style: Rephrasing style - "technical", "results", or "balanced" (default)
            use_cache: Whether to use cached responses (default: True)

        Returns:
            Dictionary with rephrasing results:
            {
                "original": str,
                "rephrased": str,
                "metrics_preserved": bool,
                "keywords_added": [str, ...],
                "improvements": [str, ...],
                "style": str
            }

        Raises:
            AIServiceError: If API call fails
            ValueError: If style is invalid

        Example:
            >>> service = AIService()
            >>> result = service.rephrase_achievement(
            ...     "Built a web app that processed data",
            ...     job_keywords=["Python", "scalable", "microservices"],
            ...     style="technical"
            ... )
            >>> print(result["rephrased"])
            "Developed a scalable Python microservices application..."
        """
        # Validate style
        valid_styles = ["technical", "results", "balanced"]
        if style not in valid_styles:
            raise ValueError(
                f"Invalid style '{style}'. Must be one of: {', '.join(valid_styles)}"
            )

        # Build system prompt based on style
        style_instructions = {
            "technical": "Focus on technical details, technologies, and implementation. "
            "Emphasize the 'how' - architectures, tools, methodologies used.",
            "results": "Focus on business impact, outcomes, and measurable results. "
            "Emphasize the 'what' - metrics, improvements, value delivered.",
            "balanced": "Balance technical details with business results. "
            "Show both the technical approach and the measurable impact.",
        }

        system_prompt = f"""You are an expert resume writer specializing in achievement statements.

Your task is to rephrase achievement statements while maintaining complete truthfulness.

CRITICAL RULES:
1. PRESERVE ALL METRICS: Never change numbers, percentages, or measurements
2. NO FABRICATION: Only state what's in the original - no additions or exaggerations
3. MAINTAIN MEANING: The rephrased version must convey the same accomplishment
4. NATURAL KEYWORDS: If job keywords are provided, incorporate them naturally if relevant
5. ATS OPTIMIZATION: Use clear, scannable language with industry-standard terms
6. IMPROVE CLARITY: Make the achievement more impactful and easier to understand

Style: {style_instructions[style]}

Return your response as a valid JSON object with this exact structure:
{{
  "rephrased": "The improved achievement statement",
  "metrics_preserved": true,
  "keywords_added": ["keyword1", "keyword2"],
  "improvements": ["Clarified impact", "Added technical context"],
  "truthfulness_check": "confirmed"
}}

Only return the JSON object, no other text."""

        # Build prompt with job keywords context
        keywords_context = ""
        if job_keywords:
            keywords_context = f"\n\nJob Keywords to consider (use naturally if relevant):\n{', '.join(job_keywords)}"

        prompt = f"""Rephrase this achievement statement:

Original: {achievement}{keywords_context}

Remember:
- Preserve ALL numbers and metrics exactly
- Do not fabricate or exaggerate
- Maintain the original meaning
- Incorporate keywords naturally (don't force them)
- Optimize for clarity and ATS scanning"""

        try:
            response = self.call_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                temperature=0.5,  # Moderate creativity for rephrasing
                use_cache=use_cache,
            )

            # Parse JSON response
            result = self._parse_rephrase_response(response)

            # Add original achievement and style to result
            result["original"] = achievement
            result["style"] = style

            # Validate metrics preservation
            if not self._validate_metrics_preserved(achievement, result["rephrased"]):
                logger.warning("Metrics may not be preserved correctly in rephrased achievement")
                result["metrics_preserved"] = False

            logger.info(f"Rephrased achievement with {len(result['keywords_added'])} keywords added")

            return result

        except (AIServiceError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Achievement rephrasing failed: {e}")
            raise AIServiceError(f"Failed to rephrase achievement: {e}") from e

    def _parse_rephrase_response(self, response: str) -> dict[str, Any]:
        """
        Parse and validate Claude's JSON response for achievement rephrasing.

        Args:
            response: Raw response text from Claude

        Returns:
            Validated rephrase result dictionary

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If required fields are missing
        """
        # Extract JSON from response
        response = response.strip()
        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            raise json.JSONDecodeError("No JSON object found", response, 0)

        json_str = response[start:end]
        result = json.loads(json_str)

        # Validate required fields
        required_fields = [
            "rephrased",
            "metrics_preserved",
            "keywords_added",
            "improvements",
            "truthfulness_check",
        ]
        for field in required_fields:
            if field not in result:
                raise KeyError(f"Missing required field: {field}")

        # Validate truthfulness check
        if result["truthfulness_check"] != "confirmed":
            logger.warning("Truthfulness check failed - response may contain fabrications")

        # Ensure keywords_added and improvements are lists
        if not isinstance(result["keywords_added"], list):
            result["keywords_added"] = []
        if not isinstance(result["improvements"], list):
            result["improvements"] = []

        return result

    def _validate_metrics_preserved(self, original: str, rephrased: str) -> bool:
        """
        Validate that all metrics from original are preserved in rephrased version.

        This is a basic validation that checks for the presence of numbers
        and percentage values.

        Args:
            original: Original achievement text
            rephrased: Rephrased achievement text

        Returns:
            True if metrics appear to be preserved, False otherwise
        """
        import re

        # Extract numbers (including decimals and percentages)
        number_pattern = r"\d+(?:\.\d+)?%?|\d+[kKmMbB]?"

        original_numbers = set(re.findall(number_pattern, original.lower()))
        rephrased_numbers = set(re.findall(number_pattern, rephrased.lower()))

        # Check if all original numbers are in rephrased
        if original_numbers and not original_numbers.issubset(rephrased_numbers):
            missing = original_numbers - rephrased_numbers
            logger.warning(f"Missing metrics in rephrased version: {missing}")
            return False

        return True

    def generate_custom_summary(
        self,
        profile_context: dict[str, Any],
        job_context: dict[str, Any] | None = None,
        style: str = "balanced",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a customized professional summary for a resume.

        This function creates a compelling 2-3 sentence professional summary
        that highlights the most relevant skills and experience for the target
        job. The summary is tailored to match job requirements while maintaining
        truthfulness.

        Args:
            profile_context: Dictionary with profile information:
                - top_skills: List of most relevant skills
                - experience_years: Total years of experience
                - top_achievements: List of key achievements
                - current_title: Current or most recent job title
                - domain: Primary domain or industry
            job_context: Optional dictionary with job information:
                - title: Target job title
                - company: Target company name
                - key_requirements: List of key job requirements
                - industry: Target industry
            style: Summary style - "technical", "results", or "balanced" (default)
            use_cache: Whether to use cached responses (default: True)

        Returns:
            Dictionary with summary results:
            {
                "summary": str,
                "style": str,
                "keywords_included": [str, ...],
                "word_count": int
            }

        Raises:
            AIServiceError: If API call fails
            ValueError: If style is invalid or required context is missing

        Example:
            >>> service = AIService()
            >>> result = service.generate_custom_summary(
            ...     profile_context={
            ...         "top_skills": ["Python", "AWS", "Docker"],
            ...         "experience_years": 5,
            ...         "top_achievements": ["Built scalable API serving 1M users"],
            ...         "current_title": "Senior Software Engineer",
            ...         "domain": "Backend Development"
            ...     },
            ...     job_context={
            ...         "title": "Lead Backend Engineer",
            ...         "key_requirements": ["Python", "microservices", "cloud"]
            ...     },
            ...     style="technical"
            ... )
            >>> print(result["summary"])
        """
        # Validate style
        valid_styles = ["technical", "results", "balanced"]
        if style not in valid_styles:
            raise ValueError(
                f"Invalid style '{style}'. Must be one of: {', '.join(valid_styles)}"
            )

        # Validate required profile context
        required_fields = ["top_skills", "experience_years", "current_title"]
        for field in required_fields:
            if field not in profile_context:
                raise ValueError(f"Missing required profile_context field: {field}")

        # Build system prompt based on style
        style_instructions = {
            "technical": "Emphasize technical expertise, technologies, and implementation skills. "
            "Highlight specific tools, frameworks, and technical methodologies.",
            "results": "Focus on measurable business impact, achievements, and outcomes. "
            "Emphasize value delivered, improvements made, and quantifiable results.",
            "balanced": "Balance technical expertise with business results. "
            "Show both technical capabilities and the impact they've delivered.",
        }

        system_prompt = f"""You are an expert resume writer specializing in professional summaries.

Your task is to create a compelling 2-3 sentence professional summary.

REQUIREMENTS:
1. LENGTH: Exactly 2-3 complete sentences (aim for 40-60 words total)
2. TRUTHFULNESS: Only use information provided - no fabrication
3. RELEVANCE: Prioritize information relevant to the target job
4. IMPACT: Make it compelling and highlight unique value
5. CLARITY: Use clear, professional language
6. ATS-FRIENDLY: Include relevant keywords naturally

Style: {style_instructions[style]}

Return your response as a valid JSON object with this exact structure:
{{
  "summary": "The professional summary (2-3 sentences)",
  "keywords_included": ["keyword1", "keyword2"],
  "word_count": 45
}}

Only return the JSON object, no other text."""

        # Build prompt with context
        prompt_parts = ["Generate a professional summary with this information:\n"]

        # Add profile context
        prompt_parts.append(f"Title: {profile_context['current_title']}")
        prompt_parts.append(f"Experience: {profile_context['experience_years']} years")
        prompt_parts.append(f"Top Skills: {', '.join(profile_context['top_skills'][:5])}")

        if "domain" in profile_context:
            prompt_parts.append(f"Domain: {profile_context['domain']}")

        if "top_achievements" in profile_context and profile_context["top_achievements"]:
            achievements_text = "; ".join(profile_context["top_achievements"][:2])
            prompt_parts.append(f"Key Achievements: {achievements_text}")

        # Add job context if provided
        if job_context:
            prompt_parts.append("\nTarget Job:")
            if "title" in job_context:
                prompt_parts.append(f"Position: {job_context['title']}")
            if "company" in job_context:
                prompt_parts.append(f"Company: {job_context['company']}")
            if "key_requirements" in job_context:
                prompt_parts.append(
                    f"Key Requirements: {', '.join(job_context['key_requirements'][:5])}"
                )
            if "industry" in job_context:
                prompt_parts.append(f"Industry: {job_context['industry']}")

        prompt_parts.append(
            "\nCreate a summary that positions the candidate as ideal for this role."
        )

        prompt = "\n".join(prompt_parts)

        try:
            response = self.call_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                temperature=0.7,  # Higher creativity for compelling summaries
                use_cache=use_cache,
            )

            # Parse JSON response
            result = self._parse_summary_response(response)

            # Add style to result
            result["style"] = style

            # Validate word count (should be 40-60 words for 2-3 sentences)
            if result["word_count"] < 30 or result["word_count"] > 80:
                logger.warning(
                    f"Summary word count {result['word_count']} outside recommended range (40-60)"
                )

            logger.info(
                f"Generated summary with {result['word_count']} words, "
                f"{len(result['keywords_included'])} keywords"
            )

            return result

        except (AIServiceError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Summary generation failed: {e}")
            raise AIServiceError(f"Failed to generate summary: {e}") from e

    def _parse_summary_response(self, response: str) -> dict[str, Any]:
        """
        Parse and validate Claude's JSON response for summary generation.

        Args:
            response: Raw response text from Claude

        Returns:
            Validated summary result dictionary

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If required fields are missing
        """
        # Extract JSON from response
        response = response.strip()
        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            raise json.JSONDecodeError("No JSON object found", response, 0)

        json_str = response[start:end]
        result = json.loads(json_str)

        # Validate required fields
        required_fields = ["summary", "keywords_included", "word_count"]
        for field in required_fields:
            if field not in result:
                raise KeyError(f"Missing required field: {field}")

        # Ensure keywords_included is a list
        if not isinstance(result["keywords_included"], list):
            result["keywords_included"] = []

        # Ensure word_count is an integer
        if not isinstance(result["word_count"], int):
            # Try to extract from summary if not provided correctly
            result["word_count"] = len(result["summary"].split())

        return result


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
