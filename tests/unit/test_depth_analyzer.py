"""
Unit tests for image_to_scad.pipeline.depth_analyzer module.

Tests written following TDD practices based on PRD specifications:
- FR9: System can convert depth map to height array suitable for 3D generation
- FR10: System can apply smoothing filters to reduce noise in depth data
- FR11: User can specify detail level to control output resolution
- FR12: System can invert depth interpretation (foreground vs background)
"""

import numpy as np
import pytest

from image_to_scad.pipeline.depth_analyzer import DepthAnalyzer
from image_to_scad.config import ConversionConfig, HeightData


@pytest.fixture
def analyzer():
    """Create DepthAnalyzer instance for testing."""
    return DepthAnalyzer()


@pytest.fixture
def sample_depth_map():
    """Create a sample depth map for testing."""
    # Create a dome-shaped depth map (center is highest)
    size = 64
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    xx, yy = np.meshgrid(x, y)
    depth = 1.0 - np.sqrt(xx**2 + yy**2)
    depth = np.clip(depth, 0, 1)
    return depth.astype(np.float32)


@pytest.fixture
def flat_depth_map():
    """Create a uniform depth map for edge case testing."""
    return np.ones((64, 64), dtype=np.float32) * 0.5


@pytest.fixture
def default_config():
    """Create default conversion config."""
    return ConversionConfig()


class TestDepthAnalyzerBasicFunctionality:
    """Basic functionality tests for DepthAnalyzer."""

    def test_analyze_returns_height_data(self, analyzer, sample_depth_map, default_config):
        """FR9: Should return HeightData from depth map."""
        result = analyzer.analyze(sample_depth_map, default_config)

        assert isinstance(result, HeightData)
        assert hasattr(result, 'heights')
        assert hasattr(result, 'width_mm')
        assert hasattr(result, 'height_mm')
        assert hasattr(result, 'resolution')

    def test_heights_array_is_2d(self, analyzer, sample_depth_map, default_config):
        """FR9: Heights should be 2D numpy array."""
        result = analyzer.analyze(sample_depth_map, default_config)

        assert isinstance(result.heights, np.ndarray)
        assert result.heights.ndim == 2

    def test_heights_are_in_mm_range(self, analyzer, sample_depth_map, default_config):
        """FR9: Heights should be in range [base_thickness, base_thickness + max_height]."""
        result = analyzer.analyze(sample_depth_map, default_config)

        min_expected = default_config.base_thickness
        max_expected = default_config.base_thickness + default_config.max_height

        assert result.heights.min() >= min_expected - 0.01  # Allow small float tolerance
        assert result.heights.max() <= max_expected + 0.01

    def test_physical_dimensions_from_config(self, analyzer, sample_depth_map, default_config):
        """FR9: Physical dimensions should be derived from config."""
        result = analyzer.analyze(sample_depth_map, default_config)

        # Width should match config
        assert result.width_mm == default_config.model_width

        # Height should preserve aspect ratio
        depth_h, depth_w = sample_depth_map.shape
        expected_height = default_config.model_width * (depth_h / depth_w)
        assert abs(result.height_mm - expected_height) < 0.01

    def test_resolution_matches_output_shape(self, analyzer, sample_depth_map, default_config):
        """FR9: Resolution tuple should match heights array shape."""
        result = analyzer.analyze(sample_depth_map, default_config)

        assert result.resolution == result.heights.shape


class TestDepthAnalyzerValidation:
    """Input validation tests for DepthAnalyzer."""

    def test_rejects_non_numpy_array(self, analyzer, default_config):
        """FR9: Should reject non-numpy inputs."""
        with pytest.raises(ValueError, match="must be a numpy array"):
            analyzer.analyze([[1, 2], [3, 4]], default_config)

    def test_rejects_1d_array(self, analyzer, default_config):
        """FR9: Should reject 1D arrays."""
        with pytest.raises(ValueError, match="must be 2D"):
            analyzer.analyze(np.array([1, 2, 3]), default_config)

    def test_rejects_3d_array(self, analyzer, default_config):
        """FR9: Should reject 3D arrays."""
        with pytest.raises(ValueError, match="must be 2D"):
            analyzer.analyze(np.zeros((10, 10, 3)), default_config)

    def test_rejects_empty_array(self, analyzer, default_config):
        """FR9: Should reject empty arrays."""
        with pytest.raises(ValueError, match="empty"):
            analyzer.analyze(np.array([]).reshape(0, 0), default_config)


class TestDepthInversion:
    """Tests for depth inversion functionality (FR12)."""

    def test_invert_depth_reverses_values(self, analyzer, sample_depth_map):
        """FR12: Inversion should reverse height relationship."""
        config_normal = ConversionConfig(invert_depth=False)
        config_inverted = ConversionConfig(invert_depth=True)

        result_normal = analyzer.analyze(sample_depth_map, config_normal)
        result_inverted = analyzer.analyze(sample_depth_map, config_inverted)

        # Find the location of max in original
        # After inversion, this should be near min (relative to range)
        max_loc_normal = np.unravel_index(result_normal.heights.argmax(), result_normal.heights.shape)
        max_loc_inverted = np.unravel_index(result_inverted.heights.argmax(), result_inverted.heights.shape)

        # Max locations should be different when inverted
        assert max_loc_normal != max_loc_inverted

    def test_invert_preserves_range(self, analyzer, sample_depth_map):
        """FR12: Inversion should preserve height range."""
        config_normal = ConversionConfig(invert_depth=False)
        config_inverted = ConversionConfig(invert_depth=True)

        result_normal = analyzer.analyze(sample_depth_map, config_normal)
        result_inverted = analyzer.analyze(sample_depth_map, config_inverted)

        # Both should have same range
        range_normal = result_normal.heights.max() - result_normal.heights.min()
        range_inverted = result_inverted.heights.max() - result_inverted.heights.min()

        assert abs(range_normal - range_inverted) < 0.1

    def test_default_is_not_inverted(self, default_config):
        """FR12: Default should be non-inverted."""
        assert default_config.invert_depth is False


class TestSmoothing:
    """Tests for smoothing functionality (FR10)."""

    def test_smoothing_enabled_by_default(self, default_config):
        """FR10: Smoothing should be enabled by default."""
        assert default_config.smoothing is True

    def test_smoothing_reduces_noise(self, analyzer):
        """FR10: Smoothing should reduce high-frequency noise."""
        # Create noisy depth map
        np.random.seed(42)
        noisy_depth = np.random.rand(64, 64).astype(np.float32)

        config_smooth = ConversionConfig(smoothing=True)
        config_no_smooth = ConversionConfig(smoothing=False)

        result_smooth = analyzer.analyze(noisy_depth, config_smooth)
        result_no_smooth = analyzer.analyze(noisy_depth, config_no_smooth)

        # Smoothed version should have lower variance in local regions
        # Calculate variance of differences between adjacent pixels
        def local_variance(arr):
            dx = np.diff(arr, axis=1)
            dy = np.diff(arr, axis=0)
            return np.var(dx) + np.var(dy)

        var_smooth = local_variance(result_smooth.heights)
        var_no_smooth = local_variance(result_no_smooth.heights)

        assert var_smooth < var_no_smooth

    def test_smoothing_can_be_disabled(self, analyzer, sample_depth_map):
        """FR10: Smoothing should be disableable via config."""
        config = ConversionConfig(smoothing=False)
        result = analyzer.analyze(sample_depth_map, config)

        # Should still produce valid output
        assert isinstance(result, HeightData)


class TestDetailLevel:
    """Tests for detail level functionality (FR11)."""

    def test_default_detail_level_is_1(self, default_config):
        """FR11: Default detail level should be 1.0."""
        assert default_config.detail_level == 1.0

    def test_higher_detail_increases_resolution(self, analyzer, sample_depth_map):
        """FR11: Higher detail should increase output resolution."""
        config_low = ConversionConfig(detail_level=0.5)
        config_high = ConversionConfig(detail_level=2.0)

        result_low = analyzer.analyze(sample_depth_map, config_low)
        result_high = analyzer.analyze(sample_depth_map, config_high)

        # Higher detail should have more points
        low_points = result_low.heights.size
        high_points = result_high.heights.size

        assert high_points > low_points

    def test_detail_level_bounds(self, default_config):
        """FR11: Detail level should be validated (0.5 to 2.0)."""
        # Valid levels
        ConversionConfig(detail_level=0.5)
        ConversionConfig(detail_level=1.0)
        ConversionConfig(detail_level=2.0)

        # Invalid levels should raise
        with pytest.raises(ValueError):
            ConversionConfig(detail_level=0.3)

        with pytest.raises(ValueError):
            ConversionConfig(detail_level=2.5)


class TestHeightMapping:
    """Tests for height value mapping."""

    def test_custom_base_thickness(self, analyzer, sample_depth_map):
        """Heights should respect custom base thickness."""
        config = ConversionConfig(base_thickness=5.0, max_height=10.0)
        result = analyzer.analyze(sample_depth_map, config)

        # Minimum height should be base_thickness
        assert result.heights.min() >= 4.9  # Allow small tolerance

    def test_custom_max_height(self, analyzer, sample_depth_map):
        """Heights should respect custom max height."""
        config = ConversionConfig(base_thickness=2.0, max_height=30.0)
        result = analyzer.analyze(sample_depth_map, config)

        # Maximum height should be base + max
        assert result.heights.max() <= 32.1  # 2 + 30 + tolerance

    def test_flat_depth_map_produces_uniform_height(self, analyzer, flat_depth_map, default_config):
        """Uniform depth map should produce uniform height (at base)."""
        result = analyzer.analyze(flat_depth_map, default_config)

        # All heights should be the same
        height_variance = np.var(result.heights)
        assert height_variance < 0.01


class TestStatistics:
    """Tests for get_statistics method."""

    def test_get_statistics_returns_dict(self, analyzer, sample_depth_map):
        """Should return dictionary with statistics."""
        stats = analyzer.get_statistics(sample_depth_map)

        assert isinstance(stats, dict)
        assert 'min' in stats
        assert 'max' in stats
        assert 'mean' in stats
        assert 'std' in stats
        assert 'shape' in stats

    def test_statistics_values_are_correct(self, analyzer, sample_depth_map):
        """Statistics should match numpy calculations."""
        stats = analyzer.get_statistics(sample_depth_map)

        assert abs(stats['min'] - float(sample_depth_map.min())) < 0.001
        assert abs(stats['max'] - float(sample_depth_map.max())) < 0.001
        assert abs(stats['mean'] - float(sample_depth_map.mean())) < 0.001
        assert stats['shape'] == sample_depth_map.shape
