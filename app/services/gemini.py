"""Google Gemini AI client for text and image generation."""

from pathlib import Path
from typing import Dict

from google import genai
from google.genai import types

from app.logger import get_logger


logger = get_logger(__name__)


class GeminiAPIError(Exception):
    """Exception raised for Gemini API failures."""

    pass


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: str, system_prompts: Dict[str, str]):
        """Initialize the Gemini client.

        Args:
            api_key: Google Gemini API key
            system_prompts: Dictionary containing system prompts for different tasks
                - 'description_generation': Prompt for generating product descriptions
                - 'image_prompt_generation': Prompt for generating image prompts
        """
        self.api_key = api_key
        self.system_prompts = system_prompts
        self.client = genai.Client(api_key=api_key)
        self.text_model = "gemini-2.0-flash-exp"  # Default Gemini model for text
        self.image_model = "gemini-2.5-flash-image"

        logger.info("GeminiClient initialized with text model: %s, image model: %s",
                   self.text_model, self.image_model)

    def generate_description(self, one_line_input: str) -> str:
        """Generate a magical product description from a one-line input.

        Args:
            one_line_input: Brief description of the product

        Returns:
            Generated description (100-200 words)

        Raises:
            GeminiAPIError: If the API call fails
        """
        logger.info("Generating description for input: %s", one_line_input)

        try:
            system_prompt = self.system_prompts.get('description_generation', '')

            # Construct the prompt with system instructions
            full_prompt = f"{system_prompt}\n\nProduct idea: {one_line_input}"

            response = self.client.models.generate_content(
                model=self.text_model,
                contents=full_prompt
            )

            if not response or not response.text:
                raise GeminiAPIError("Empty response from Gemini API for description generation")

            description = response.text.strip()
            logger.info("Generated description: %d characters", len(description))
            return description

        except Exception as e:
            logger.error("Failed to generate description: %s", str(e))
            raise GeminiAPIError(f"Failed to generate description: {str(e)}") from e

    def generate_image_prompt(self, description: str) -> str:
        """Convert a product description into a detailed image generation prompt.

        Args:
            description: Product description

        Returns:
            Detailed image generation prompt

        Raises:
            GeminiAPIError: If the API call fails
        """
        logger.info("Generating image prompt from description")

        try:
            system_prompt = self.system_prompts.get('image_prompt_generation', '')

            # Construct the prompt with system instructions
            full_prompt = f"{system_prompt}\n\nDescription:\n{description}"

            response = self.client.models.generate_content(
                model=self.text_model,
                contents=full_prompt
            )

            if not response or not response.text:
                raise GeminiAPIError("Empty response from Gemini API for image prompt generation")

            image_prompt = response.text.strip()
            logger.info("Generated image prompt: %d characters", len(image_prompt))
            return image_prompt

        except Exception as e:
            logger.error("Failed to generate image prompt: %s", str(e))
            raise GeminiAPIError(f"Failed to generate image prompt: {str(e)}") from e

    def generate_image(self, prompt: str, output_path: Path) -> Path:
        """Generate an image using Gemini API and save it to a file.

        Args:
            prompt: Image generation prompt
            output_path: Path where the image should be saved (should have .png extension)

        Returns:
            Path to the saved image file

        Raises:
            GeminiAPIError: If the API call fails or no image is generated
        """
        logger.info("Generating image with prompt: %s", prompt[:100])
        logger.info("Output path: %s", output_path)

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Construct the content using the pattern from image-example.py
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]

            # Configure for image generation
            generate_content_config = types.GenerateContentConfig(
                response_modalities=[
                    "IMAGE",
                    "TEXT",
                ],
                image_config=types.ImageConfig(
                    image_size="1K",  # 1024x1024
                ),
            )

            # Stream the response
            image_saved = False
            for chunk in self.client.models.generate_content_stream(
                model=self.image_model,
                contents=contents,
                config=generate_content_config,
            ):
                # Check if chunk contains image data
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                # Look for inline image data
                if (chunk.candidates[0].content.parts[0].inline_data and
                    chunk.candidates[0].content.parts[0].inline_data.data):

                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data

                    # Save the image
                    with open(output_path, "wb") as f:
                        f.write(data_buffer)

                    logger.info("Image saved to: %s", output_path)
                    image_saved = True
                    break
                else:
                    # Log any text responses
                    if hasattr(chunk, 'text') and chunk.text:
                        logger.debug("Received text chunk: %s", chunk.text)

            if not image_saved:
                raise GeminiAPIError("No image data received from Gemini API")

            return output_path

        except Exception as e:
            logger.error("Failed to generate image: %s", str(e))
            raise GeminiAPIError(f"Failed to generate image: {str(e)}") from e
