"""Tests for the configuration system.

These tests verify that the Config class properly loads configuration
from YAML files and environment variables, with appropriate error handling.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from app.config import Config, ConfigurationError


class TestConfig:
    """Test cases for the Config class."""

    @pytest.fixture
    def valid_config_file(self):
        """Create a temporary valid config.yaml file."""
        config_data = {
            'system_prompts': {
                'description_generation': 'Test description prompt',
                'image_prompt_generation': 'Test image prompt'
            },
            'settings': {
                'data_dir': '/test/data',
                'image_size': 512,
                'log_level': 'DEBUG'
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        # Temporarily replace the config file path
        original_path = Config._config_file_path
        Config._config_file_path = Path(temp_path)
        Config._config_data = None  # Reset cached data

        yield temp_path

        # Cleanup
        Config._config_file_path = original_path
        Config._config_data = None
        Path(temp_path).unlink()

    @pytest.fixture
    def env_vars(self):
        """Set up environment variables for testing."""
        os.environ['GEMINI_API_KEY'] = 'test-api-key-123'
        os.environ['ADMIN_PASSWORD'] = 'test-password-456'
        os.environ['DATA_DIR'] = '/test/custom/data'

        yield

        # Cleanup
        os.environ.pop('GEMINI_API_KEY', None)
        os.environ.pop('ADMIN_PASSWORD', None)
        os.environ.pop('DATA_DIR', None)

    def test_load_valid_config(self, valid_config_file):
        """Test loading a valid configuration file."""
        config_data = Config._load_config()

        assert config_data is not None
        assert 'system_prompts' in config_data
        assert 'settings' in config_data

    def test_get_system_prompt(self, valid_config_file):
        """Test retrieving system prompts from config."""
        prompts = Config.get_system_prompt()

        assert isinstance(prompts, dict)
        assert 'description_generation' in prompts
        assert 'image_prompt_generation' in prompts
        assert prompts['description_generation'] == 'Test description prompt'
        assert prompts['image_prompt_generation'] == 'Test image prompt'

    def test_get_gemini_api_key(self, env_vars):
        """Test retrieving Gemini API key from environment."""
        api_key = Config.get_gemini_api_key()
        assert api_key == 'test-api-key-123'

    def test_get_gemini_api_key_missing(self):
        """Test error when GEMINI_API_KEY is not set."""
        # Ensure the env var is not set
        os.environ.pop('GEMINI_API_KEY', None)

        with pytest.raises(ConfigurationError) as exc_info:
            Config.get_gemini_api_key()

        assert 'GEMINI_API_KEY' in str(exc_info.value)

    def test_get_admin_password(self, env_vars):
        """Test retrieving admin password from environment."""
        password = Config.get_admin_password()
        assert password == 'test-password-456'

    def test_get_admin_password_missing(self):
        """Test error when ADMIN_PASSWORD is not set."""
        # Ensure the env var is not set
        os.environ.pop('ADMIN_PASSWORD', None)

        with pytest.raises(ConfigurationError) as exc_info:
            Config.get_admin_password()

        assert 'ADMIN_PASSWORD' in str(exc_info.value)

    def test_get_data_dir_default(self):
        """Test data directory defaults to /data."""
        # Ensure DATA_DIR is not set
        os.environ.pop('DATA_DIR', None)

        data_dir = Config.get_data_dir()
        assert data_dir == Path('/data')

    def test_get_data_dir_custom(self, env_vars):
        """Test custom data directory from environment."""
        data_dir = Config.get_data_dir()
        assert data_dir == Path('/test/custom/data')

    def test_get_image_dir(self, env_vars):
        """Test image directory is subdirectory of data dir."""
        image_dir = Config.get_image_dir()
        assert image_dir == Path('/test/custom/data/images')

    def test_get_image_size(self, valid_config_file):
        """Test retrieving image size from config."""
        image_size = Config.get_image_size()
        assert image_size == 512

    def test_get_log_level(self, valid_config_file):
        """Test retrieving log level from config."""
        log_level = Config.get_log_level()
        assert log_level == 'DEBUG'

    def test_missing_config_file(self):
        """Test error when config file doesn't exist."""
        # Point to a non-existent file
        Config._config_file_path = Path('/nonexistent/config.yaml')
        Config._config_data = None

        with pytest.raises(ConfigurationError) as exc_info:
            Config._load_config()

        assert 'not found' in str(exc_info.value).lower()

    def test_empty_config_file(self):
        """Test error when config file is empty."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')
            temp_path = f.name

        Config._config_file_path = Path(temp_path)
        Config._config_data = None

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                Config._load_config()

            assert 'empty' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_invalid_yaml(self):
        """Test error when config file has invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid: yaml: content: [')
            temp_path = f.name

        Config._config_file_path = Path(temp_path)
        Config._config_data = None

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                Config._load_config()

            assert 'parse' in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_missing_system_prompts_section(self, valid_config_file):
        """Test error when system_prompts section is missing."""
        # Modify the config to remove system_prompts
        with open(valid_config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        del config_data['system_prompts']

        with open(valid_config_file, 'w') as f:
            yaml.dump(config_data, f)

        Config._config_data = None  # Reset cache

        with pytest.raises(ConfigurationError) as exc_info:
            Config.get_system_prompt()

        assert 'system_prompts' in str(exc_info.value)

    def test_missing_prompt_key(self, valid_config_file):
        """Test error when a required prompt is missing."""
        # Modify the config to remove a prompt key
        with open(valid_config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        del config_data['system_prompts']['description_generation']

        with open(valid_config_file, 'w') as f:
            yaml.dump(config_data, f)

        Config._config_data = None  # Reset cache

        with pytest.raises(ConfigurationError) as exc_info:
            Config.get_system_prompt()

        assert 'description_generation' in str(exc_info.value)
