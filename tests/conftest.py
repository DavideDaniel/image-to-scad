"""
Pytest configuration and fixtures for image_to_scad tests.
"""

from pathlib import Path
from typing import Generator

import numpy as np
import pytest


# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def images_dir() -> Path:
    """Return the path to the test images directory."""
    return IMAGES_DIR


@pytest.fixture
def sample_image_array() -> np.ndarray:
    """
    Create a sample RGB image array for testing.

    Returns:
        np.ndarray: 128x128 RGB image with gradient pattern.
    """
    # Create a simple gradient image
    size = 128
    image = np.zeros((size, size, 3), dtype=np.uint8)

    # Horizontal gradient (red channel)
    image[:, :, 0] = np.tile(np.linspace(0, 255, size, dtype=np.uint8), (size, 1))

    # Vertical gradient (green channel)
    image[:, :, 1] = np.tile(
        np.linspace(0, 255, size, dtype=np.uint8).reshape(-1, 1), (1, size)
    )

    # Constant blue
    image[:, :, 2] = 128

    return image


@pytest.fixture
def sample_depth_map() -> np.ndarray:
    """
    Create a sample depth map for testing.

    Returns:
        np.ndarray: 64x64 depth map with dome pattern.
    """
    size = 64
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)

    # Create a dome-shaped depth map
    depth = 1.0 - np.sqrt(xx**2 + yy**2)
    depth = np.clip(depth, 0, 1)

    return depth.astype(np.float32)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """
    Create a temporary output directory for tests.

    Args:
        tmp_path: Pytest's temporary path fixture.

    Returns:
        Path: Path to temporary directory.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def default_config():
    """
    Create a default ConversionConfig for testing.

    Returns:
        ConversionConfig: Default configuration.
    """
    from image_to_scad.config import ConversionConfig

    return ConversionConfig()


@pytest.fixture
def sample_height_data(sample_depth_map: np.ndarray):
    """
    Create sample HeightData for testing.

    Args:
        sample_depth_map: Sample depth map fixture.

    Returns:
        HeightData: Sample height data.
    """
    from image_to_scad.config import HeightData

    # Scale depth map to height values
    heights = sample_depth_map * 15.0 + 2.0  # 2-17mm range

    return HeightData(
        heights=heights,
        width_mm=100.0,
        height_mm=100.0,
    )
