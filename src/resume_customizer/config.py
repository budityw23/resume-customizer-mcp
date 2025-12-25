"""
Configuration management for Resume Customizer MCP Server.

This module handles loading and validating configuration from environment variables
and provides a centralized configuration object for the application.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Anthropic API Configuration
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    # MCP Server Configuration
    mcp_server_name: str = "resume_customizer"
    mcp_server_version: str = "1.0.0"
    log_level: str = "INFO"

    # Storage Configuration
    database_path: Path = field(default_factory=lambda: Path("./data/customizations.db"))
    output_directory: Path = field(default_factory=lambda: Path("./output"))
    cache_directory: Path = field(default_factory=lambda: Path("./cache"))

    # Feature Flags
    enable_ai_extraction: bool = True
    enable_cache: bool = True
    cache_ttl_hours: int = 24

    # Templates
    default_template: str = "modern"
    templates_dir: Path = field(default_factory=lambda: Path("./templates"))

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.anthropic_api_key or self.anthropic_api_key == "sk-ant-your-api-key-here":
            raise ValueError(
                "ANTHROPIC_API_KEY must be set. "
                "Get your API key from https://console.anthropic.com/"
            )

        # Ensure directories exist
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)


def load_config(env_file: str | None = None) -> Config:
    """
    Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file. If not provided, looks for .env in current directory.

    Returns:
        Config object with loaded configuration

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    # Load environment variables from .env file
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    # Helper function to get boolean from env
    def get_bool(key: str, default: bool) -> bool:
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    # Helper function to get int from env
    def get_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    # Helper function to get path from env
    def get_path(key: str, default: str) -> Path:
        return Path(os.getenv(key, default))

    # Create config object
    config = Config(
        # Anthropic API
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=get_int("MAX_TOKENS", 4096),
        # MCP Server
        mcp_server_name=os.getenv("MCP_SERVER_NAME", "resume_customizer"),
        mcp_server_version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        # Storage
        database_path=get_path("DATABASE_PATH", "./data/customizations.db"),
        output_directory=get_path("OUTPUT_DIRECTORY", "./output"),
        cache_directory=get_path("CACHE_DIRECTORY", "./cache"),
        # Features
        enable_ai_extraction=get_bool("ENABLE_AI_EXTRACTION", True),
        enable_cache=get_bool("ENABLE_CACHE", True),
        cache_ttl_hours=get_int("CACHE_TTL_HOURS", 24),
        # Templates
        default_template=os.getenv("DEFAULT_TEMPLATE", "modern"),
        templates_dir=get_path("TEMPLATES_DIR", "./templates"),
    )

    return config


# Global config instance (loaded on first import)
_config: Config | None = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        The global Config object

    Note:
        Configuration is loaded once and cached. Call load_config() to reload.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
