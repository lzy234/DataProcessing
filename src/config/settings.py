"""Configuration management for the data processing pipeline."""
import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


# Load environment variables from config/.env
_config_dir = Path(__file__).parent.parent.parent / "config"
_env_file = _config_dir / ".env"
load_dotenv(_env_file, override=True)  # Override system env vars with .env file


class Settings:
    """Application settings loaded from environment variables and config files."""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    CONFIG_DIR = PROJECT_ROOT / "config"

    # Input/Output paths
    INPUT_DIR = DATA_DIR / "input"
    INTERMEDIATE_DIR = DATA_DIR / "intermediate"
    OUTPUT_DIR = DATA_DIR / "output"

    # Claude API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", None)

    # Rate limits
    MAX_CLAUDE_REQUESTS_PER_MINUTE = int(os.getenv("MAX_CLAUDE_REQUESTS_PER_MINUTE", "50"))
    MAX_WIKIPEDIA_REQUESTS_PER_MINUTE = int(os.getenv("MAX_WIKIPEDIA_REQUESTS_PER_MINUTE", "100"))

    # Processing options
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    ENABLE_WIKIPEDIA = os.getenv("ENABLE_WIKIPEDIA", "true").lower() == "true"
    ENABLE_GOVERNMENT_SCRAPING = os.getenv("ENABLE_GOVERNMENT_SCRAPING", "false").lower() == "true"

    # Output options
    OUTPUT_ENCODING = os.getenv("OUTPUT_ENCODING", "utf-8-sig")

    # Cache settings
    WIKIPEDIA_CACHE_FILE = INTERMEDIATE_DIR / "wikipedia_cache.json"
    AI_RESPONSES_CACHE_FILE = INTERMEDIATE_DIR / "ai_responses.json"
    EXTRACTED_ENTITIES_FILE = INTERMEDIATE_DIR / "extracted_entities.json"

    @classmethod
    def load_json_config(cls, filename: str) -> Dict[str, Any]:
        """
        Load a JSON configuration file.

        Args:
            filename: Config filename (e.g., 'sector_mappings.json')

        Returns:
            Parsed JSON data
        """
        config_path = cls.CONFIG_DIR / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def get_sector_mappings(cls) -> Dict[str, Any]:
        """Load sector mappings configuration."""
        return cls.load_json_config('sector_mappings.json')

    @classmethod
    def get_party_colors(cls) -> Dict[str, Any]:
        """Load party colors configuration."""
        return cls.load_json_config('party_colors.json')

    @classmethod
    def validate(cls) -> bool:
        """
        Validate required settings.

        Returns:
            True if all required settings are valid

        Raises:
            ValueError: If required settings are missing
        """
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required. Please set it in your .env file."
            )

        # Ensure directories exist
        cls.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        return True


# Validate settings on import
try:
    Settings.validate()
except ValueError as e:
    print(f"Warning: {e}")
