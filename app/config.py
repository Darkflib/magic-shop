"""Configuration management for the Magic Shop application.

This module handles loading configuration from YAML files and environment variables,
providing a centralized interface for accessing all application settings.
"""

import os
from pathlib import Path
from typing import Dict

import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """Configuration manager for the Magic Shop application.

    Loads settings from config.yaml and environment variables.
    All methods are static to provide easy access throughout the application.
    """

    _config_data: Dict = None
    _config_file_path: Path = Path(__file__).parent.parent / "config.yaml"

    @classmethod
    def _load_config(cls) -> Dict:
        """Load configuration from YAML file.

        Returns:
            Dictionary containing the full configuration.

        Raises:
            ConfigurationError: If config file doesn't exist or is invalid.
        """
        if cls._config_data is None:
            if not cls._config_file_path.exists():
                raise ConfigurationError(
                    f"Configuration file not found at {cls._config_file_path}. "
                    f"Please ensure config.yaml exists in the project root."
                )

            try:
                with open(cls._config_file_path, 'r') as f:
                    cls._config_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigurationError(
                    f"Failed to parse config.yaml: {e}"
                )
            except Exception as e:
                raise ConfigurationError(
                    f"Error loading config.yaml: {e}"
                )

            if cls._config_data is None:
                raise ConfigurationError("config.yaml is empty")

        return cls._config_data

    @staticmethod
    def get_system_prompt() -> Dict[str, str]:
        """Get system prompts for AI generation.

        Returns:
            Dictionary with 'description_generation' and 'image_prompt_generation' keys.

        Raises:
            ConfigurationError: If prompts are not configured properly.
        """
        config = Config._load_config()

        if 'system_prompts' not in config:
            raise ConfigurationError(
                "Missing 'system_prompts' section in config.yaml"
            )

        prompts = config['system_prompts']

        required_prompts = ['description_generation', 'image_prompt_generation']
        for prompt_key in required_prompts:
            if prompt_key not in prompts:
                raise ConfigurationError(
                    f"Missing '{prompt_key}' in system_prompts section of config.yaml"
                )

        return {
            'description_generation': prompts['description_generation'],
            'image_prompt_generation': prompts['image_prompt_generation']
        }

    @staticmethod
    def get_gemini_api_key() -> str:
        """Get Gemini API key from environment.

        Returns:
            The Gemini API key.

        Raises:
            ConfigurationError: If GEMINI_API_KEY environment variable is not set.
        """
        api_key = os.environ.get('GEMINI_API_KEY')

        if not api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment."
            )

        return api_key

    @staticmethod
    def get_admin_password() -> str:
        """Get admin password from environment.

        Returns:
            The admin password for HTTP Basic Auth.

        Raises:
            ConfigurationError: If ADMIN_PASSWORD environment variable is not set.
        """
        password = os.environ.get('ADMIN_PASSWORD')

        if not password:
            raise ConfigurationError(
                "ADMIN_PASSWORD environment variable is not set. "
                "Please set it in your .env file or environment."
            )

        return password

    @staticmethod
    def get_data_dir() -> Path:
        """Get data directory path from environment or use default.

        The data directory is where the SQLite database and images are stored.

        Returns:
            Path object pointing to the data directory.
        """
        data_dir_str = os.environ.get('DATA_DIR', '/data')
        return Path(data_dir_str)

    @staticmethod
    def get_image_dir() -> Path:
        """Get images directory path.

        Images are stored in a subdirectory of the data directory.

        Returns:
            Path object pointing to the images directory.
        """
        return Config.get_data_dir() / 'images'

    @staticmethod
    def get_image_size() -> int:
        """Get image generation size from config.

        Returns:
            Image size in pixels (for square images).

        Raises:
            ConfigurationError: If image_size is not configured.
        """
        config = Config._load_config()

        if 'settings' not in config or 'image_size' not in config['settings']:
            raise ConfigurationError(
                "Missing 'image_size' in settings section of config.yaml"
            )

        return config['settings']['image_size']

    @staticmethod
    def get_log_level() -> str:
        """Get log level from config.

        Returns:
            Log level string (e.g., 'INFO', 'DEBUG', 'WARNING').

        Raises:
            ConfigurationError: If log_level is not configured.
        """
        config = Config._load_config()

        if 'settings' not in config or 'log_level' not in config['settings']:
            raise ConfigurationError(
                "Missing 'log_level' in settings section of config.yaml"
            )

        return config['settings']['log_level']
