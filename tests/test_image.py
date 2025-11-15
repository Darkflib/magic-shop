"""Tests for image conversion service."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from app.services.image import convert_png_to_jpg, ImageConversionError


class TestImageConversion:
    """Test suite for PNG to JPG image conversion."""

    def test_convert_simple_png_to_jpg(self):
        """Test converting a simple RGB PNG to JPG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a simple RGB PNG image
            png_path = tmpdir_path / "test_image.png"
            img = Image.new('RGB', (100, 100), color=(255, 0, 0))  # Red square
            img.save(png_path, 'PNG')

            # Convert to JPG
            jpg_path = tmpdir_path / "test_image.jpg"
            result_path = convert_png_to_jpg(png_path, jpg_path, quality=85)

            # Verify the JPG was created
            assert result_path == jpg_path
            assert jpg_path.exists()

            # Verify it's a valid JPG
            with Image.open(jpg_path) as jpg_img:
                assert jpg_img.format == 'JPEG'
                assert jpg_img.size == (100, 100)
                assert jpg_img.mode == 'RGB'

    def test_convert_rgba_png_to_jpg(self):
        """Test converting a PNG with transparency (RGBA) to JPG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create an RGBA PNG image with transparency
            png_path = tmpdir_path / "test_rgba.png"
            img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))  # Semi-transparent red
            img.save(png_path, 'PNG')

            # Convert to JPG
            jpg_path = tmpdir_path / "test_rgba.jpg"
            result_path = convert_png_to_jpg(png_path, jpg_path, quality=90)

            # Verify the JPG was created
            assert result_path == jpg_path
            assert jpg_path.exists()

            # Verify it's a valid JPG without alpha channel
            with Image.open(jpg_path) as jpg_img:
                assert jpg_img.format == 'JPEG'
                assert jpg_img.size == (100, 100)
                assert jpg_img.mode == 'RGB'  # No alpha channel

    def test_convert_palette_mode_png(self):
        """Test converting a palette mode PNG to JPG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a palette mode PNG
            png_path = tmpdir_path / "test_palette.png"
            img = Image.new('P', (100, 100))
            img.putpalette([i % 256 for i in range(256 * 3)])
            img.save(png_path, 'PNG')

            # Convert to JPG
            jpg_path = tmpdir_path / "test_palette.jpg"
            result_path = convert_png_to_jpg(png_path, jpg_path)

            # Verify the JPG was created
            assert result_path == jpg_path
            assert jpg_path.exists()

            # Verify it's a valid JPG
            with Image.open(jpg_path) as jpg_img:
                assert jpg_img.format == 'JPEG'
                assert jpg_img.mode == 'RGB'

    def test_custom_quality_setting(self):
        """Test that different quality settings produce different file sizes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a complex PNG image
            png_path = tmpdir_path / "test_quality.png"
            img = Image.new('RGB', (200, 200))
            # Add some patterns to make compression differences visible
            pixels = img.load()
            for i in range(200):
                for j in range(200):
                    pixels[i, j] = ((i * j) % 256, (i + j) % 256, (i - j) % 256)
            img.save(png_path, 'PNG')

            # Convert with different quality settings
            jpg_low = tmpdir_path / "test_low.jpg"
            jpg_high = tmpdir_path / "test_high.jpg"

            convert_png_to_jpg(png_path, jpg_low, quality=50)
            convert_png_to_jpg(png_path, jpg_high, quality=95)

            # Higher quality should produce larger files
            low_size = jpg_low.stat().st_size
            high_size = jpg_high.stat().st_size
            assert high_size > low_size

    def test_creates_output_directory(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a PNG
            png_path = tmpdir_path / "test.png"
            img = Image.new('RGB', (50, 50), color=(0, 255, 0))
            img.save(png_path, 'PNG')

            # Specify output in a non-existent subdirectory
            jpg_path = tmpdir_path / "subdir" / "output" / "test.jpg"
            assert not jpg_path.parent.exists()

            # Convert - should create the directory
            result_path = convert_png_to_jpg(png_path, jpg_path)

            assert jpg_path.parent.exists()
            assert jpg_path.exists()
            assert result_path == jpg_path

    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised when PNG doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            png_path = tmpdir_path / "nonexistent.png"
            jpg_path = tmpdir_path / "output.jpg"

            with pytest.raises(FileNotFoundError):
                convert_png_to_jpg(png_path, jpg_path)

    def test_invalid_quality_value(self):
        """Test that ValueError is raised for invalid quality values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a PNG
            png_path = tmpdir_path / "test.png"
            img = Image.new('RGB', (50, 50))
            img.save(png_path, 'PNG')

            jpg_path = tmpdir_path / "output.jpg"

            # Test quality too low
            with pytest.raises(ValueError, match="Quality must be between 1 and 100"):
                convert_png_to_jpg(png_path, jpg_path, quality=0)

            # Test quality too high
            with pytest.raises(ValueError, match="Quality must be between 1 and 100"):
                convert_png_to_jpg(png_path, jpg_path, quality=101)

    def test_corrupt_png_file(self):
        """Test that ImageConversionError is raised for corrupt PNG files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a corrupt PNG file (just random bytes)
            png_path = tmpdir_path / "corrupt.png"
            with open(png_path, 'wb') as f:
                f.write(b'Not a real PNG file')

            jpg_path = tmpdir_path / "output.jpg"

            with pytest.raises(ImageConversionError):
                convert_png_to_jpg(png_path, jpg_path)

    def test_grayscale_png_conversion(self):
        """Test converting a grayscale PNG to JPG."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a grayscale PNG
            png_path = tmpdir_path / "test_gray.png"
            img = Image.new('L', (100, 100), color=128)
            img.save(png_path, 'PNG')

            # Convert to JPG
            jpg_path = tmpdir_path / "test_gray.jpg"
            result_path = convert_png_to_jpg(png_path, jpg_path)

            # Verify the JPG was created
            assert result_path == jpg_path
            assert jpg_path.exists()

            # Verify it's a valid RGB JPG (grayscale is converted to RGB)
            with Image.open(jpg_path) as jpg_img:
                assert jpg_img.format == 'JPEG'
                assert jpg_img.mode == 'RGB'

    def test_large_image_conversion(self):
        """Test converting a larger image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a larger PNG
            png_path = tmpdir_path / "test_large.png"
            img = Image.new('RGB', (1024, 1024), color=(100, 150, 200))
            img.save(png_path, 'PNG')

            # Convert to JPG
            jpg_path = tmpdir_path / "test_large.jpg"
            result_path = convert_png_to_jpg(png_path, jpg_path, quality=85)

            # Verify the JPG was created with correct dimensions
            assert jpg_path.exists()
            with Image.open(jpg_path) as jpg_img:
                assert jpg_img.format == 'JPEG'
                assert jpg_img.size == (1024, 1024)

    def test_overwrite_existing_jpg(self):
        """Test that converting overwrites an existing JPG file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a PNG
            png_path = tmpdir_path / "test.png"
            img = Image.new('RGB', (100, 100), color=(255, 0, 0))
            img.save(png_path, 'PNG')

            # Create an existing JPG with different content
            jpg_path = tmpdir_path / "output.jpg"
            old_img = Image.new('RGB', (50, 50), color=(0, 255, 0))
            old_img.save(jpg_path, 'JPEG')

            old_size = jpg_path.stat().st_size

            # Convert - should overwrite
            convert_png_to_jpg(png_path, jpg_path)

            # Verify the file was overwritten (different size)
            new_size = jpg_path.stat().st_size
            assert new_size != old_size

            # Verify new image has correct dimensions
            with Image.open(jpg_path) as jpg_img:
                assert jpg_img.size == (100, 100)
