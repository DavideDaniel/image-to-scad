"""
Depth map analysis and processing for height data generation.

This module converts raw depth maps into normalized height data
suitable for OpenSCAD generation.
"""

from typing import Optional

import numpy as np

from image_to_scad.config import ConversionConfig, HeightData
from image_to_scad.utils.logging import get_logger


class DepthAnalyzer:
    """
    Analyze and process depth maps for OpenSCAD generation.

    This class handles:
    - Depth map normalization
    - Height range mapping
    - Optional smoothing
    - Depth inversion

    Example:
        >>> analyzer = DepthAnalyzer()
        >>> config = ConversionConfig(max_height=15.0, model_width=100.0)
        >>> height_data = analyzer.analyze(depth_map, config)
        >>> print(height_data.heights.shape)
    """

    def __init__(self) -> None:
        """Initialize the depth analyzer."""
        self._logger = get_logger(__name__)

    def analyze(
        self,
        depth_map: np.ndarray,
        config: ConversionConfig,
    ) -> HeightData:
        """
        Convert a depth map to height data for OpenSCAD generation.

        Args:
            depth_map: 2D depth map array from depth estimation.
            config: Conversion configuration with height parameters.

        Returns:
            HeightData: Processed height data ready for OpenSCAD generation.

        Raises:
            ValueError: If depth_map format is invalid.
        """
        self._validate_depth_map(depth_map)

        # Work with a copy to avoid modifying the original
        heights = depth_map.astype(np.float32).copy()

        # Apply detail level (resolution adjustment)
        heights = self._apply_detail_level(heights, config.detail_level)

        # Optionally invert depth
        if config.invert_depth:
            heights = self._invert(heights)

        # Apply smoothing if enabled
        if config.smoothing:
            heights = self._smooth(heights)

        # Normalize to height range
        heights = self._normalize_to_range(
            heights,
            config.base_thickness,
            config.base_thickness + config.max_height,
        )

        # Calculate physical dimensions
        rows, cols = heights.shape
        aspect_ratio = rows / cols
        width_mm = config.model_width
        height_mm = width_mm * aspect_ratio

        self._logger.debug(
            f"Analyzed depth map: {cols}x{rows} -> "
            f"{width_mm:.1f}x{height_mm:.1f}mm, "
            f"height range: {heights.min():.2f}-{heights.max():.2f}mm"
        )

        return HeightData(
            heights=heights,
            width_mm=width_mm,
            height_mm=height_mm,
        )

    def _validate_depth_map(self, depth_map: np.ndarray) -> None:
        """
        Validate depth map format.

        Args:
            depth_map: Depth map to validate.

        Raises:
            ValueError: If format is invalid.
        """
        if not isinstance(depth_map, np.ndarray):
            raise ValueError("depth_map must be a numpy array")

        if depth_map.ndim != 2:
            raise ValueError(f"depth_map must be 2D, got {depth_map.ndim}D")

        if depth_map.size == 0:
            raise ValueError("depth_map is empty")

    def _apply_detail_level(
        self,
        heights: np.ndarray,
        detail_level: float,
    ) -> np.ndarray:
        """
        Apply detail level by resizing the height map.

        Args:
            heights: Height array.
            detail_level: Detail multiplier (0.5 = coarse, 2.0 = fine).

        Returns:
            np.ndarray: Resized height array.
        """
        if detail_level == 1.0:
            return heights

        # Import here to avoid circular dependency
        import cv2

        rows, cols = heights.shape
        new_rows = int(rows * detail_level)
        new_cols = int(cols * detail_level)

        # Clamp to reasonable limits
        new_rows = max(32, min(2048, new_rows))
        new_cols = max(32, min(2048, new_cols))

        if (new_rows, new_cols) == (rows, cols):
            return heights

        resized = cv2.resize(
            heights,
            (new_cols, new_rows),
            interpolation=cv2.INTER_CUBIC,
        )

        self._logger.debug(f"Applied detail level {detail_level}: {cols}x{rows} -> {new_cols}x{new_rows}")
        return resized

    def _invert(self, heights: np.ndarray) -> np.ndarray:
        """
        Invert depth values (flip foreground/background).

        Args:
            heights: Height array.

        Returns:
            np.ndarray: Inverted height array.
        """
        return heights.max() - heights + heights.min()

    def _smooth(
        self,
        heights: np.ndarray,
        kernel_size: int = 5,
    ) -> np.ndarray:
        """
        Apply Gaussian smoothing to the height map.

        Args:
            heights: Height array.
            kernel_size: Size of the Gaussian kernel.

        Returns:
            np.ndarray: Smoothed height array.
        """
        import cv2

        # Ensure kernel size is odd
        kernel_size = kernel_size if kernel_size % 2 == 1 else kernel_size + 1

        smoothed = cv2.GaussianBlur(heights, (kernel_size, kernel_size), 0)
        return smoothed

    def _normalize_to_range(
        self,
        heights: np.ndarray,
        min_height: float,
        max_height: float,
    ) -> np.ndarray:
        """
        Normalize height values to a specific range in mm.

        Args:
            heights: Height array.
            min_height: Minimum height value (base thickness).
            max_height: Maximum height value.

        Returns:
            np.ndarray: Normalized height array in mm.
        """
        h_min, h_max = heights.min(), heights.max()

        if h_max - h_min < 1e-6:
            # Flat image, return base thickness
            return np.full_like(heights, min_height)

        # Normalize to [0, 1] then scale to [min_height, max_height]
        normalized = (heights - h_min) / (h_max - h_min)
        scaled = normalized * (max_height - min_height) + min_height

        return scaled

    def get_statistics(self, depth_map: np.ndarray) -> dict:
        """
        Get statistical information about a depth map.

        Args:
            depth_map: Depth map to analyze.

        Returns:
            dict: Statistics including min, max, mean, std.
        """
        return {
            "min": float(depth_map.min()),
            "max": float(depth_map.max()),
            "mean": float(depth_map.mean()),
            "std": float(depth_map.std()),
            "shape": depth_map.shape,
        }
