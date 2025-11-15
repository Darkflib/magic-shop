"""Image processing utilities for the Magic Shop application."""

from pathlib import Path

from PIL import Image

from app.logger import get_logger


logger = get_logger(__name__)


class ImageConversionError(Exception):
    """Exception raised for image conversion failures."""

    pass


def convert_png_to_jpg(png_path: Path, jpg_path: Path, quality: int = 85) -> Path:
    """Convert a PNG image to JPG format.

    Handles RGBA to RGB conversion for PNG images with transparency.
    The alpha channel is replaced with a white background.

    Args:
        png_path: Path to the source PNG file
        jpg_path: Path where the JPG file should be saved
        quality: JPEG quality (1-100, default 85)

    Returns:
        Path to the created JPG file

    Raises:
        ImageConversionError: If conversion fails
        FileNotFoundError: If the PNG file doesn't exist
    """
    logger.info("Converting PNG to JPG: %s -> %s (quality=%d)", png_path, jpg_path, quality)

    if not png_path.exists():
        error_msg = f"PNG file not found: {png_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if not 1 <= quality <= 100:
        error_msg = f"Quality must be between 1 and 100, got {quality}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Ensure output directory exists
        jpg_path.parent.mkdir(parents=True, exist_ok=True)

        # Open the PNG image
        with Image.open(png_path) as img:
            logger.debug("Opened PNG image: mode=%s, size=%s", img.mode, img.size)

            # Convert RGBA to RGB (handle transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                logger.debug("Converting image mode %s to RGB", img.mode)

                # Create a white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))

                # If image has transparency, paste it onto white background
                if img.mode == 'RGBA' or img.mode == 'LA':
                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                elif img.mode == 'P' and 'transparency' in img.info:
                    # Convert palette mode with transparency
                    img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    # No transparency, just convert
                    rgb_img.paste(img)

                img = rgb_img
            elif img.mode != 'RGB':
                # Convert any other mode to RGB
                logger.debug("Converting image mode %s to RGB", img.mode)
                img = img.convert('RGB')

            # Save as JPEG
            img.save(jpg_path, 'JPEG', quality=quality, optimize=True)
            logger.info("Successfully saved JPG image to: %s", jpg_path)

        return jpg_path

    except FileNotFoundError:
        # Re-raise FileNotFoundError as-is
        raise
    except Exception as e:
        error_msg = f"Failed to convert PNG to JPG: {str(e)}"
        logger.error(error_msg)
        raise ImageConversionError(error_msg) from e
