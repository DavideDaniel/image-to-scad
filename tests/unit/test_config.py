"""
Unit tests for image_to_scad.config module.
"""

import numpy as np
import pytest

from image_to_scad.config import ConversionConfig, HeightData, ConversionResult


class TestConversionConfig:
    """Tests for ConversionConfig dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = ConversionConfig()

        assert config.base_thickness == 2.0
        assert config.max_height == 15.0
        assert config.model_width == 100.0
        assert config.detail_level == 1.0
        assert config.smoothing is True
        assert config.invert_depth is False
        assert config.output_style == "relief"

    def test_custom_values(self):
        """Test creating config with custom values."""
        config = ConversionConfig(
            base_thickness=3.0,
            max_height=20.0,
            model_width=150.0,
            detail_level=1.5,
            smoothing=False,
            invert_depth=True,
        )

        assert config.base_thickness == 3.0
        assert config.max_height == 20.0
        assert config.model_width == 150.0
        assert config.detail_level == 1.5
        assert config.smoothing is False
        assert config.invert_depth is True

    def test_validation_base_thickness(self):
        """Test that invalid base_thickness raises ValueError."""
        with pytest.raises(ValueError, match="base_thickness must be positive"):
            ConversionConfig(base_thickness=0)

        with pytest.raises(ValueError, match="base_thickness must be positive"):
            ConversionConfig(base_thickness=-1.0)

    def test_validation_max_height(self):
        """Test that invalid max_height raises ValueError."""
        with pytest.raises(ValueError, match="max_height must be positive"):
            ConversionConfig(max_height=0)

    def test_validation_model_width(self):
        """Test that invalid model_width raises ValueError."""
        with pytest.raises(ValueError, match="model_width must be positive"):
            ConversionConfig(model_width=-50)

    def test_validation_detail_level(self):
        """Test that invalid detail_level raises ValueError."""
        with pytest.raises(ValueError, match="detail_level must be between"):
            ConversionConfig(detail_level=0.3)

        with pytest.raises(ValueError, match="detail_level must be between"):
            ConversionConfig(detail_level=2.5)

    def test_validation_output_style(self):
        """Test that invalid output_style raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported output_style"):
            ConversionConfig(output_style="invalid")

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = ConversionConfig(base_thickness=5.0, max_height=25.0)
        data = config.to_dict()

        assert data["base_thickness"] == 5.0
        assert data["max_height"] == 25.0
        assert data["model_width"] == 100.0
        assert data["detail_level"] == 1.0
        assert data["smoothing"] is True
        assert data["invert_depth"] is False
        assert data["output_style"] == "relief"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "base_thickness": 4.0,
            "max_height": 18.0,
            "model_width": 120.0,
            "detail_level": 0.8,
            "smoothing": False,
            "invert_depth": True,
            "output_style": "relief",
        }
        config = ConversionConfig.from_dict(data)

        assert config.base_thickness == 4.0
        assert config.max_height == 18.0
        assert config.model_width == 120.0
        assert config.detail_level == 0.8
        assert config.smoothing is False
        assert config.invert_depth is True

    def test_from_dict_with_defaults(self):
        """Test that from_dict uses defaults for missing keys."""
        data = {"base_thickness": 3.0}
        config = ConversionConfig.from_dict(data)

        assert config.base_thickness == 3.0
        assert config.max_height == 15.0  # default
        assert config.model_width == 100.0  # default

    def test_roundtrip(self):
        """Test that to_dict and from_dict are reversible."""
        original = ConversionConfig(
            base_thickness=3.5,
            max_height=22.0,
            model_width=80.0,
            detail_level=1.2,
            smoothing=False,
            invert_depth=True,
        )
        data = original.to_dict()
        restored = ConversionConfig.from_dict(data)

        assert original.base_thickness == restored.base_thickness
        assert original.max_height == restored.max_height
        assert original.model_width == restored.model_width
        assert original.detail_level == restored.detail_level
        assert original.smoothing == restored.smoothing
        assert original.invert_depth == restored.invert_depth


class TestHeightData:
    """Tests for HeightData dataclass."""

    def test_basic_creation(self):
        """Test creating HeightData with valid data."""
        heights = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        data = HeightData(heights=heights, width_mm=100.0, height_mm=100.0)

        assert data.width_mm == 100.0
        assert data.height_mm == 100.0
        assert data.resolution == (2, 2)
        np.testing.assert_array_equal(data.heights, heights)

    def test_resolution_calculation(self):
        """Test that resolution is calculated correctly."""
        heights = np.zeros((64, 128), dtype=np.float32)
        data = HeightData(heights=heights, width_mm=200.0, height_mm=100.0)

        assert data.resolution == (64, 128)

    def test_validation_2d_array(self):
        """Test that non-2D arrays raise ValueError."""
        with pytest.raises(ValueError, match="heights must be a 2D array"):
            HeightData(
                heights=np.array([1, 2, 3]),  # 1D array
                width_mm=100.0,
                height_mm=100.0,
            )

        with pytest.raises(ValueError, match="heights must be a 2D array"):
            HeightData(
                heights=np.zeros((2, 3, 4)),  # 3D array
                width_mm=100.0,
                height_mm=100.0,
            )


class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_basic_creation(self):
        """Test creating ConversionResult with minimal data."""
        result = ConversionResult(scad_code="// test code")

        assert result.scad_code == "// test code"
        assert result.scad_path is None
        assert result.stl_path is None
        assert result.depth_map is None
        assert result.processing_time == 0.0

    def test_full_creation(self):
        """Test creating ConversionResult with all fields."""
        from pathlib import Path

        depth_map = np.zeros((10, 10), dtype=np.float32)
        result = ConversionResult(
            scad_code="// full test",
            scad_path=Path("/output/model.scad"),
            stl_path=Path("/output/model.stl"),
            depth_map=depth_map,
            processing_time=1.5,
        )

        assert result.scad_code == "// full test"
        assert result.scad_path == Path("/output/model.scad")
        assert result.stl_path == Path("/output/model.stl")
        np.testing.assert_array_equal(result.depth_map, depth_map)
        assert result.processing_time == 1.5
