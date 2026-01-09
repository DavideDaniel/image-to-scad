"""
Unit tests for image_to_scad.pipeline.image_loader module.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from image_to_scad.pipeline.image_loader import (
    ImageLoader,
    SUPPORTED_FORMATS,
    MIN_DIMENSION,
)
from image_to_scad.exceptions import ImageLoadError


@pytest.fixture
def image_loader():
    """Create an ImageLoader instance for testing."""
    return ImageLoader()


@pytest.fixture
def temp_image_dir(tmp_path):
    """Create a temporary directory for test images."""
    return tmp_path


def create_test_image(path: Path, size: tuple = (128, 128), mode: str = "RGB"):
    """Helper to create test images."""
    # Grayscale modes need single-value color
    if mode in ("L", "1", "I", "F"):
        color = 128
    elif mode in ("LA",):
        color = (128, 255)
    elif mode in ("RGBA",):
        color = (128, 64, 32, 255)
    else:
        color = (128, 64, 32)
    image = Image.new(mode, size, color=color)
    image.save(path)
    return path


class TestImageLoader:
    """Tests for ImageLoader class."""

    def test_load_rgb_image(self, image_loader, temp_image_dir):
        """Test loading a standard RGB image."""
        image_path = temp_image_dir / "test.jpg"
        create_test_image(image_path, size=(100, 100), mode="RGB")

        result = image_loader.load(image_path)

        assert isinstance(result, np.ndarray)
        assert result.ndim == 3
        assert result.shape[2] == 3  # RGB channels
        assert result.dtype == np.uint8

    def test_load_png_image(self, image_loader, temp_image_dir):
        """Test loading a PNG image."""
        image_path = temp_image_dir / "test.png"
        create_test_image(image_path, size=(100, 100), mode="RGB")

        result = image_loader.load(image_path)

        assert isinstance(result, np.ndarray)
        assert result.shape[2] == 3

    def test_load_rgba_image_converts_to_rgb(self, image_loader, temp_image_dir):
        """Test that RGBA images are converted to RGB."""
        image_path = temp_image_dir / "test_rgba.png"
        create_test_image(image_path, size=(100, 100), mode="RGBA")

        result = image_loader.load(image_path)

        assert result.shape[2] == 3  # Should be RGB, not RGBA

    def test_load_grayscale_converts_to_rgb(self, image_loader, temp_image_dir):
        """Test that grayscale images are converted to RGB."""
        image_path = temp_image_dir / "test_gray.png"
        create_test_image(image_path, size=(100, 100), mode="L")

        result = image_loader.load(image_path)

        assert result.shape[2] == 3  # Should be RGB

    def test_load_nonexistent_file_raises_error(self, image_loader):
        """Test that loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            image_loader.load(Path("/nonexistent/image.jpg"))

    def test_load_unsupported_format_raises_error(self, image_loader, temp_image_dir):
        """Test that unsupported formats raise ImageLoadError."""
        # Create a text file with image extension
        bad_file = temp_image_dir / "test.xyz"
        bad_file.write_text("not an image")

        with pytest.raises(ImageLoadError, match="Unsupported image format"):
            image_loader.load(bad_file)

    def test_load_corrupted_file_raises_error(self, image_loader, temp_image_dir):
        """Test that corrupted image files raise ImageLoadError."""
        bad_file = temp_image_dir / "corrupted.jpg"
        bad_file.write_bytes(b"not valid image data")

        with pytest.raises(ImageLoadError, match="Failed to open image"):
            image_loader.load(bad_file)

    def test_load_too_small_image_raises_error(self, image_loader, temp_image_dir):
        """Test that images below minimum size raise ImageLoadError."""
        small_image = temp_image_dir / "tiny.png"
        create_test_image(small_image, size=(32, 32))

        with pytest.raises(ImageLoadError, match="Image too small"):
            image_loader.load(small_image)

    def test_load_resizes_large_images(self, temp_image_dir):
        """Test that large images are resized to max dimension."""
        loader = ImageLoader(max_dimension=256)
        large_image = temp_image_dir / "large.png"
        create_test_image(large_image, size=(1024, 768))

        result = loader.load(large_image)

        # Largest dimension should be <= max_dimension
        assert max(result.shape[:2]) <= 256

    def test_load_preserves_aspect_ratio(self, temp_image_dir):
        """Test that resizing preserves aspect ratio."""
        loader = ImageLoader(max_dimension=100)
        image_path = temp_image_dir / "wide.png"
        create_test_image(image_path, size=(200, 100))  # 2:1 aspect ratio

        result = loader.load(image_path)

        height, width = result.shape[:2]
        aspect_ratio = width / height
        assert 1.9 < aspect_ratio < 2.1  # Close to 2:1

    def test_validate_valid_image(self, image_loader, temp_image_dir):
        """Test that validate returns True for valid images."""
        image_path = temp_image_dir / "valid.png"
        create_test_image(image_path, size=(100, 100))

        assert image_loader.validate(image_path) is True

    def test_validate_invalid_image(self, image_loader, temp_image_dir):
        """Test that validate returns False for invalid images."""
        bad_file = temp_image_dir / "invalid.jpg"
        bad_file.write_bytes(b"not an image")

        assert image_loader.validate(bad_file) is False

    def test_validate_nonexistent_file(self, image_loader):
        """Test that validate returns False for non-existent files."""
        assert image_loader.validate(Path("/nonexistent.jpg")) is False

    def test_get_dimensions(self, image_loader, temp_image_dir):
        """Test getting image dimensions without loading."""
        image_path = temp_image_dir / "test.png"
        create_test_image(image_path, size=(300, 200))

        width, height = image_loader.get_dimensions(image_path)

        assert width == 300
        assert height == 200

    def test_supported_formats(self):
        """Test that expected formats are supported."""
        expected = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
        assert SUPPORTED_FORMATS == expected


class TestImageLoaderFormats:
    """Tests for different image format support."""

    @pytest.fixture
    def loader(self):
        return ImageLoader()

    @pytest.mark.parametrize("suffix,mode", [
        (".jpg", "RGB"),
        (".jpeg", "RGB"),
        (".png", "RGB"),
        (".png", "RGBA"),
        (".bmp", "RGB"),
    ])
    def test_load_various_formats(self, loader, tmp_path, suffix, mode):
        """Test loading various image formats."""
        image_path = tmp_path / f"test{suffix}"
        create_test_image(image_path, size=(100, 100), mode=mode)

        result = loader.load(image_path)

        assert isinstance(result, np.ndarray)
        assert result.shape[2] == 3
