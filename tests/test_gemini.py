"""Tests for the Gemini AI client.

These tests verify that the GeminiClient properly interacts with the Google Gemini API
for text generation and image generation, with appropriate error handling.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.gemini import GeminiAPIError, GeminiClient


class TestGeminiClient:
    """Test cases for the GeminiClient class."""

    @pytest.fixture
    def system_prompts(self):
        """Provide test system prompts."""
        return {
            'description_generation': 'Test prompt for generating descriptions.',
            'image_prompt_generation': 'Test prompt for generating image prompts.'
        }

    @pytest.fixture
    def gemini_client(self, system_prompts):
        """Create a GeminiClient instance for testing."""
        return GeminiClient(api_key='test-api-key', system_prompts=system_prompts)

    def test_client_initialization(self, gemini_client, system_prompts):
        """Test that GeminiClient initializes with correct parameters."""
        assert gemini_client.api_key == 'test-api-key'
        assert gemini_client.system_prompts == system_prompts
        assert gemini_client.text_model == "gemini-2.0-flash-exp"
        assert gemini_client.image_model == "gemini-2.5-flash-image"
        assert gemini_client.client is not None

    @patch('app.services.gemini.genai.Client')
    def test_generate_description_success(self, mock_client_class, system_prompts):
        """Test successful description generation."""
        # Arrange
        mock_response = Mock()
        mock_response.text = "A mystical sword forged in dragon fire."

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act
        result = client.generate_description("magic sword")

        # Assert
        assert result == "A mystical sword forged in dragon fire."
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]['model'] == 'gemini-2.0-flash-exp'
        assert 'magic sword' in call_args[1]['contents']

    @patch('app.services.gemini.genai.Client')
    def test_generate_description_with_system_prompt(self, mock_client_class, system_prompts):
        """Test that system prompt is included in description generation."""
        # Arrange
        mock_response = Mock()
        mock_response.text = "Generated description"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act
        client.generate_description("healing potion")

        # Assert
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]['contents']
        assert 'Test prompt for generating descriptions' in prompt
        assert 'healing potion' in prompt

    @patch('app.services.gemini.genai.Client')
    def test_generate_description_empty_response(self, mock_client_class, system_prompts):
        """Test error handling when API returns empty response."""
        # Arrange
        mock_response = Mock()
        mock_response.text = None

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_description("test input")

        assert "Empty response" in str(exc_info.value)

    @patch('app.services.gemini.genai.Client')
    def test_generate_description_api_error(self, mock_client_class, system_prompts):
        """Test error handling when API call fails."""
        # Arrange
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API connection failed")
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_description("test input")

        assert "Failed to generate description" in str(exc_info.value)
        assert "API connection failed" in str(exc_info.value)

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_prompt_success(self, mock_client_class, system_prompts):
        """Test successful image prompt generation."""
        # Arrange
        mock_response = Mock()
        mock_response.text = "A detailed image showing a glowing magical sword."

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)
        description = "A sword that glows with magical energy"

        # Act
        result = client.generate_image_prompt(description)

        # Assert
        assert result == "A detailed image showing a glowing magical sword."
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]['model'] == 'gemini-2.0-flash-exp'
        assert description in call_args[1]['contents']

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_prompt_with_system_prompt(self, mock_client_class, system_prompts):
        """Test that system prompt is included in image prompt generation."""
        # Arrange
        mock_response = Mock()
        mock_response.text = "Image prompt"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act
        client.generate_image_prompt("A magical item")

        # Assert
        call_args = mock_client.models.generate_content.call_args
        prompt = call_args[1]['contents']
        assert 'Test prompt for generating image prompts' in prompt
        assert 'A magical item' in prompt

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_prompt_empty_response(self, mock_client_class, system_prompts):
        """Test error handling when image prompt API returns empty response."""
        # Arrange
        mock_response = Mock()
        mock_response.text = ""

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_image_prompt("test description")

        assert "Empty response" in str(exc_info.value)

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_prompt_api_error(self, mock_client_class, system_prompts):
        """Test error handling when image prompt API call fails."""
        # Arrange
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_image_prompt("test description")

        assert "Failed to generate image prompt" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_success(self, mock_client_class, system_prompts, tmp_path):
        """Test successful image generation."""
        # Arrange
        output_path = tmp_path / "test_image.png"
        image_data = b"fake_image_binary_data"

        # Create mock inline_data
        mock_inline_data = Mock()
        mock_inline_data.data = image_data
        mock_inline_data.mime_type = "image/png"

        # Create mock part with inline_data
        mock_part = Mock()
        mock_part.inline_data = mock_inline_data

        # Create mock content with parts
        mock_content = Mock()
        mock_content.parts = [mock_part]

        # Create mock candidate
        mock_candidate = Mock()
        mock_candidate.content = mock_content

        # Create mock chunk
        mock_chunk = Mock()
        mock_chunk.candidates = [mock_candidate]

        # Set up mock client to return our chunk
        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = [mock_chunk]
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act
        result = client.generate_image("A magical sword", output_path)

        # Assert
        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == image_data

        # Verify API was called correctly
        mock_client.models.generate_content_stream.assert_called_once()
        call_kwargs = mock_client.models.generate_content_stream.call_args[1]
        assert call_kwargs['model'] == 'gemini-2.5-flash-image'
        assert call_kwargs['config'].response_modalities == ["IMAGE", "TEXT"]
        assert call_kwargs['config'].image_config.image_size == "1K"

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_creates_directory(self, mock_client_class, system_prompts, tmp_path):
        """Test that generate_image creates output directory if it doesn't exist."""
        # Arrange
        output_path = tmp_path / "subdir" / "nested" / "test_image.png"
        image_data = b"image_data"

        # Set up mock similar to previous test
        mock_inline_data = Mock()
        mock_inline_data.data = image_data

        mock_part = Mock()
        mock_part.inline_data = mock_inline_data

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content

        mock_chunk = Mock()
        mock_chunk.candidates = [mock_candidate]

        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = [mock_chunk]
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act
        result = client.generate_image("Test prompt", output_path)

        # Assert
        assert result == output_path
        assert output_path.exists()
        assert output_path.parent.exists()

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_no_image_data(self, mock_client_class, system_prompts, tmp_path):
        """Test error when API doesn't return image data."""
        # Arrange
        output_path = tmp_path / "test_image.png"

        # Create chunk with no inline_data
        mock_part = Mock()
        mock_part.inline_data = None

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content

        mock_chunk = Mock()
        mock_chunk.candidates = [mock_candidate]

        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = [mock_chunk]
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_image("Test prompt", output_path)

        assert "No image data received" in str(exc_info.value)
        assert not output_path.exists()

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_empty_stream(self, mock_client_class, system_prompts, tmp_path):
        """Test error when API returns empty stream."""
        # Arrange
        output_path = tmp_path / "test_image.png"

        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = []
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_image("Test prompt", output_path)

        assert "No image data received" in str(exc_info.value)

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_api_error(self, mock_client_class, system_prompts, tmp_path):
        """Test error handling when image generation API call fails."""
        # Arrange
        output_path = tmp_path / "test_image.png"

        mock_client = Mock()
        mock_client.models.generate_content_stream.side_effect = Exception("API timeout")
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act & Assert
        with pytest.raises(GeminiAPIError) as exc_info:
            client.generate_image("Test prompt", output_path)

        assert "Failed to generate image" in str(exc_info.value)
        assert "API timeout" in str(exc_info.value)

    @patch('app.services.gemini.genai.Client')
    def test_generate_image_uses_correct_config(self, mock_client_class, system_prompts, tmp_path):
        """Test that image generation uses correct model and configuration."""
        # Arrange
        output_path = tmp_path / "test_image.png"

        mock_inline_data = Mock()
        mock_inline_data.data = b"data"

        mock_part = Mock()
        mock_part.inline_data = mock_inline_data

        mock_content = Mock()
        mock_content.parts = [mock_part]

        mock_candidate = Mock()
        mock_candidate.content = mock_content

        mock_chunk = Mock()
        mock_chunk.candidates = [mock_candidate]

        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = [mock_chunk]
        mock_client_class.return_value = mock_client

        client = GeminiClient(api_key='test-key', system_prompts=system_prompts)

        # Act
        client.generate_image("Test prompt", output_path)

        # Assert
        call_kwargs = mock_client.models.generate_content_stream.call_args[1]

        # Verify model
        assert call_kwargs['model'] == 'gemini-2.5-flash-image'

        # Verify config
        config = call_kwargs['config']
        assert config.response_modalities == ["IMAGE", "TEXT"]
        assert config.image_config.image_size == "1K"

        # Verify contents structure
        contents = call_kwargs['contents']
        assert len(contents) == 1
        assert contents[0].role == "user"
        assert len(contents[0].parts) == 1


# Integration tests - only run when GEMINI_API_KEY is set
@pytest.mark.integration
class TestGeminiClientIntegration:
    """Integration tests for GeminiClient that make real API calls.

    These tests are skipped unless GEMINI_API_KEY environment variable is set.
    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_api_key(self):
        """Get real API key from environment or skip test."""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set - skipping integration test")
        return api_key

    @pytest.fixture
    def real_system_prompts(self):
        """Provide realistic system prompts for integration testing."""
        return {
            'description_generation': (
                'You are a creative writer for a magical item shop. '
                'Generate a brief, whimsical description for magical items. '
                'Keep it under 100 words.'
            ),
            'image_prompt_generation': (
                'Create a detailed image generation prompt based on the description. '
                'Be specific about visual elements.'
            )
        }

    def test_real_description_generation(self, real_api_key, real_system_prompts):
        """Test actual description generation with real API."""
        client = GeminiClient(api_key=real_api_key, system_prompts=real_system_prompts)

        result = client.generate_description("magic wand")

        assert isinstance(result, str)
        assert len(result) > 0
        assert len(result) < 1000  # Reasonable upper bound

    def test_real_image_prompt_generation(self, real_api_key, real_system_prompts):
        """Test actual image prompt generation with real API."""
        client = GeminiClient(api_key=real_api_key, system_prompts=real_system_prompts)

        description = "A crystal ball that shows the future"
        result = client.generate_image_prompt(description)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_real_image_generation(self, real_api_key, real_system_prompts, tmp_path):
        """Test actual image generation with real API."""
        client = GeminiClient(api_key=real_api_key, system_prompts=real_system_prompts)

        output_path = tmp_path / "integration_test_image.png"
        result = client.generate_image("A simple magic wand", output_path)

        assert result == output_path
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify it's a valid image file by checking PNG header
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header[:4] == b'\x89PNG'  # PNG file signature
