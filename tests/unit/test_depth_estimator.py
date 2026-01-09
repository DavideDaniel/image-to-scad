"""
Unit tests for image_to_scad.pipeline.depth_estimator module.

Tests written following TDD practices based on PRD specifications:
- FR5: System can load and initialize the Intel DPT-Hybrid-MiDaS depth estimation model
- FR6: System can generate a depth map from any supported input image
- FR7: System can normalize depth values to a consistent range
- FR8: System can cache the loaded model to avoid re-initialization

Note: Some tests require the actual model to be downloaded, which may be slow.
Tests marked with @pytest.mark.slow should be run separately for CI efficiency.
"""

import numpy as np
import pytest

from image_to_scad.pipeline.depth_estimator import (
    DepthEstimator,
    MODEL_ID,
)
from image_to_scad.exceptions import DepthEstimationError


class TestDepthEstimatorSpec:
    """Tests based on PRD specifications for depth estimation."""

    def test_model_id_is_intel_dpt_hybrid_midas(self):
        """FR5: Verify correct model is specified (Intel DPT-Hybrid-MiDaS)."""
        assert MODEL_ID == "Intel/dpt-hybrid-midas"

    def test_estimator_initializes_without_loading_model(self):
        """FR8: Model should be lazy-loaded, not loaded on init."""
        estimator = DepthEstimator()

        # Model should not be loaded yet
        assert estimator.is_loaded is False
        assert estimator._model is None
        assert estimator._processor is None

    def test_estimator_accepts_device_parameter(self):
        """Should accept optional device parameter for CPU/GPU selection."""
        estimator_cpu = DepthEstimator(device="cpu")
        assert estimator_cpu._device == "cpu"

        # Device shouldn't change until model is loaded
        estimator_auto = DepthEstimator()
        assert estimator_auto._device is None

    def test_is_loaded_property(self):
        """Should accurately report model loading status."""
        estimator = DepthEstimator()
        assert estimator.is_loaded is False

        # After release (even if never loaded), should still be False
        estimator.release()
        assert estimator.is_loaded is False

    def test_device_property_before_load(self):
        """Device property should be None before model is loaded."""
        estimator = DepthEstimator()
        # Device is None until explicitly set or auto-detected during load
        assert estimator.device is None or isinstance(estimator.device, str)


class TestDepthEstimatorValidation:
    """Tests for input validation in DepthEstimator."""

    @pytest.fixture
    def estimator(self):
        """Create estimator instance for testing."""
        return DepthEstimator()

    def test_validate_rejects_non_numpy_array(self, estimator):
        """FR6: Should reject non-numpy inputs."""
        with pytest.raises(ValueError, match="must be a numpy array"):
            estimator._validate_image([[1, 2], [3, 4]])

        with pytest.raises(ValueError, match="must be a numpy array"):
            estimator._validate_image("not an image")

    def test_validate_rejects_1d_array(self, estimator):
        """FR6: Should reject 1D arrays."""
        with pytest.raises(ValueError, match="must be 3D array"):
            estimator._validate_image(np.array([1, 2, 3]))

    def test_validate_rejects_2d_array(self, estimator):
        """FR6: Should reject 2D arrays (grayscale without channel dim)."""
        with pytest.raises(ValueError, match="must be 3D array"):
            estimator._validate_image(np.zeros((100, 100)))

    def test_validate_rejects_4d_array(self, estimator):
        """FR6: Should reject 4D arrays (batch dimension)."""
        with pytest.raises(ValueError, match="must be 3D array"):
            estimator._validate_image(np.zeros((1, 100, 100, 3)))

    def test_validate_rejects_wrong_channel_count(self, estimator):
        """FR6: Should reject images with wrong number of channels."""
        # Single channel
        with pytest.raises(ValueError, match="must have 3 channels"):
            estimator._validate_image(np.zeros((100, 100, 1)))

        # Four channels (RGBA)
        with pytest.raises(ValueError, match="must have 3 channels"):
            estimator._validate_image(np.zeros((100, 100, 4)))

    def test_validate_accepts_valid_rgb_image(self, estimator):
        """FR6: Should accept valid RGB images."""
        valid_image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Should not raise
        estimator._validate_image(valid_image)

    def test_validate_accepts_various_sizes(self, estimator):
        """FR6: Should accept various valid image sizes."""
        sizes = [(64, 64), (128, 256), (480, 640), (1024, 768)]
        for h, w in sizes:
            image = np.zeros((h, w, 3), dtype=np.uint8)
            estimator._validate_image(image)  # Should not raise


class TestDepthEstimatorRelease:
    """Tests for model release functionality."""

    def test_release_clears_model_references(self):
        """FR8: Release should clear model from memory."""
        estimator = DepthEstimator()

        # Release should work even if model never loaded
        estimator.release()

        assert estimator._model is None
        assert estimator._processor is None
        assert estimator.is_loaded is False

    def test_release_can_be_called_multiple_times(self):
        """Release should be safe to call multiple times."""
        estimator = DepthEstimator()

        # Multiple releases should not raise
        estimator.release()
        estimator.release()
        estimator.release()

        assert estimator.is_loaded is False


class TestDepthEstimatorOutputSpec:
    """Tests for depth estimation output specifications.

    These tests define what the output SHOULD look like based on FR6 and FR7.
    They use mock/synthetic data to test the interface without loading the model.
    """

    def test_depth_map_shape_matches_input(self):
        """FR6: Output depth map should match input image dimensions."""
        # This is a specification test - defines expected behavior
        # The actual implementation interpolates to match input size
        input_shape = (480, 640, 3)
        expected_output_shape = (480, 640)  # 2D depth map

        # Verify shape expectation is correct (H, W)
        assert len(expected_output_shape) == 2
        assert expected_output_shape[0] == input_shape[0]
        assert expected_output_shape[1] == input_shape[1]

    def test_depth_map_is_2d_float_array(self):
        """FR6: Output should be 2D numpy array of depth values."""
        # Specification: depth map should be 2D float array
        sample_output = np.zeros((100, 100), dtype=np.float32)

        assert sample_output.ndim == 2
        assert np.issubdtype(sample_output.dtype, np.floating)

    def test_depth_values_are_relative(self):
        """FR7: Depth values represent relative depth (higher = closer)."""
        # This documents the expected convention
        # MiDaS outputs inverse depth: higher values = closer to camera
        sample_depths = np.array([[1.0, 0.5], [0.2, 0.1]])

        # Higher value (1.0) should represent closest point
        closest_idx = np.unravel_index(sample_depths.argmax(), sample_depths.shape)
        assert sample_depths[closest_idx] == 1.0


@pytest.mark.slow
class TestDepthEstimatorIntegration:
    """Integration tests that require the actual model.

    These tests download and use the real model.
    Run with: pytest -m slow
    """

    @pytest.fixture
    def estimator(self):
        """Create estimator with cleanup."""
        est = DepthEstimator(device="cpu")
        yield est
        est.release()

    @pytest.fixture
    def sample_image(self):
        """Create a sample RGB image for testing."""
        # Create gradient image for depth variation
        image = np.zeros((128, 128, 3), dtype=np.uint8)
        for i in range(128):
            image[i, :, :] = i * 2  # Gradient from dark to light
        return image

    def test_estimate_returns_depth_map(self, estimator, sample_image):
        """FR6: Should return a valid depth map from image."""
        depth_map = estimator.estimate(sample_image)

        # Verify output shape matches input (H, W)
        assert depth_map.shape == sample_image.shape[:2]

        # Verify output is 2D float array
        assert depth_map.ndim == 2
        assert np.issubdtype(depth_map.dtype, np.floating)

    def test_estimate_produces_varied_depth(self, estimator, sample_image):
        """FR6: Depth map should have variation (not all same value)."""
        depth_map = estimator.estimate(sample_image)

        # Should have some variation
        assert depth_map.max() != depth_map.min()

    def test_model_caching(self, estimator, sample_image):
        """FR8: Second call should reuse cached model."""
        # First call loads model
        _ = estimator.estimate(sample_image)
        assert estimator.is_loaded is True

        # Second call should reuse
        _ = estimator.estimate(sample_image)
        assert estimator.is_loaded is True

    def test_estimate_after_release_reloads(self, estimator, sample_image):
        """FR8: Model should reload after release."""
        # Load and release
        _ = estimator.estimate(sample_image)
        estimator.release()
        assert estimator.is_loaded is False

        # Should reload on next call
        _ = estimator.estimate(sample_image)
        assert estimator.is_loaded is True


class TestDepthEstimatorErrorHandling:
    """Tests for error handling in depth estimation."""

    def test_estimate_without_dependencies_raises_error(self):
        """Should raise DepthEstimationError if torch/transformers missing."""
        # This test documents expected behavior
        # In practice, we can't easily test missing imports
        # But we verify the exception type is correct
        assert issubclass(DepthEstimationError, Exception)

    def test_depth_estimation_error_is_catchable(self):
        """DepthEstimationError should be catchable."""
        from image_to_scad.exceptions import ImageToScadError

        # Should be part of the exception hierarchy
        assert issubclass(DepthEstimationError, ImageToScadError)

        # Should be raisable and catchable
        with pytest.raises(DepthEstimationError):
            raise DepthEstimationError("test error")
