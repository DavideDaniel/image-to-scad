"""
Image loading and validation for the conversion pipeline.

This module handles loading images from disk, validating formats,
and preprocessing for depth estimation.
"""

from pathlib import Path
from typing import Tuple, Optional

import numpy as np
from PIL import Image

from image_to_scad.exceptions import ImageLoadError
from image_to_scad.utils.logging import get_logger


# Supported image formats
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

# Image size constraints
MIN_DIMENSION = 64
MAX_DIMENSION = 4096
DEFAULT_MAX_DIMENSION = 1024


class ImageLoader:
    """
    Load and preprocess images for depth estimation.

    This class handles:
    - Loading images from various formats
    - Validating image dimensions
    - Converting to RGB format
    - Resizing to optimal processing dimensions

    Example:
        >>> loader = ImageLoader()
        >>> image = loader.load(Path("photo.jpg"))
        >>> print(image.shape)  # (height, width, 3)
    """

    def __init__(self, max_dimension: int = DEFAULT_MAX_DIMENSION) -> None:
        """
        Initialize the image loader.

        Args:
            max_dimension: Maximum dimension (width or height) for processing.
                          Images larger than this will be resized.
        """
        self._logger = get_logger(__name__)
        self._max_dimension = max_dimension

    def load(self, path: Path) -> np.ndarray:
        """
        Load and preprocess an image from disk.

        Args:
            path: Path to the image file.

        Returns:
            np.ndarray: RGB image as numpy array with shape (H, W, 3).

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ImageLoadError: If the file is not a valid image.
        """
        path = Path(path)
        self._validate_path(path)

        try:
            image = Image.open(path)
        except Exception as e:
            raise ImageLoadError(f"Failed to open image: {e}") from e

        # Validate and process
        self._validate_image(image, path)
        image = self._convert_to_rgb(image)
        image = self._resize_if_needed(image)

        # Convert to numpy array
        array = np.array(image, dtype=np.uint8)
        self._logger.debug(f"Loaded image: {path.name}, shape: {array.shape}")

        return array

    def validate(self, path: Path) -> bool:
        """
        Check if a file is a valid, loadable image.

        Args:
            path: Path to the file to validate.

        Returns:
            bool: True if the file is a valid image.
        """
        try:
            self._validate_path(path)
            with Image.open(path) as img:
                self._validate_image(img, path)
            return True
        except (FileNotFoundError, ImageLoadError, Exception):
            # Catch PIL.UnidentifiedImageError and other PIL exceptions
            return False

    def get_dimensions(self, path: Path) -> Tuple[int, int]:
        """
        Get image dimensions without fully loading the image.

        Args:
            path: Path to the image file.

        Returns:
            Tuple[int, int]: Image dimensions as (width, height).

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ImageLoadError: If the file is not a valid image.
        """
        path = Path(path)
        self._validate_path(path)

        try:
            with Image.open(path) as img:
                return img.size
        except Exception as e:
            raise ImageLoadError(f"Failed to read image dimensions: {e}") from e

    def _validate_path(self, path: Path) -> None:
        """
        Validate that the path exists and has a supported format.

        Args:
            path: Path to validate.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ImageLoadError: If the format is not supported.
        """
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        if not path.is_file():
            raise ImageLoadError(f"Path is not a file: {path}")

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_FORMATS:
            supported = ", ".join(sorted(SUPPORTED_FORMATS))
            raise ImageLoadError(
                f"Unsupported image format: {suffix}. "
                f"Supported formats: {supported}"
            )

    def _validate_image(self, image: Image.Image, path: Path) -> None:
        """
        Validate image dimensions and format.

        Args:
            image: PIL Image object.
            path: Path to the image (for error messages).

        Raises:
            ImageLoadError: If the image is invalid.
        """
        width, height = image.size

        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            raise ImageLoadError(
                f"Image too small: {width}x{height}. "
                f"Minimum dimension is {MIN_DIMENSION}px."
            )

        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            self._logger.warning(
                f"Large image ({width}x{height}) will be resized "
                f"to max {self._max_dimension}px for processing."
            )

    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """
        Convert image to RGB format.

        Args:
            image: PIL Image object.

        Returns:
            Image.Image: RGB image.
        """
        if image.mode == "RGB":
            return image

        if image.mode == "RGBA":
            # Create white background for transparency
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            return background

        # Convert other modes (L, P, etc.) to RGB
        return image.convert("RGB")

    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum dimensions.

        Args:
            image: PIL Image object.

        Returns:
            Image.Image: Resized image if needed, otherwise original.
        """
        width, height = image.size

        if width <= self._max_dimension and height <= self._max_dimension:
            return image

        # Calculate new dimensions preserving aspect ratio
        if width > height:
            new_width = self._max_dimension
            new_height = int(height * (self._max_dimension / width))
        else:
            new_height = self._max_dimension
            new_width = int(width * (self._max_dimension / height))

        self._logger.debug(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
