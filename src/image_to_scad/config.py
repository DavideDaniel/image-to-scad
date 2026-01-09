"""
Configuration dataclasses for image_to_scad.

This module defines the configuration and data structures used throughout
the conversion pipeline.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


@dataclass
class ConversionConfig:
    """
    User-configurable conversion parameters.

    Attributes:
        base_thickness: Minimum thickness of the model base in mm.
        max_height: Maximum relief height above the base in mm.
        model_width: Width of the output model in mm.
        detail_level: Detail multiplier (0.5 = coarse, 1.0 = normal, 2.0 = fine).
        smoothing: Whether to apply smoothing filter to the depth map.
        invert_depth: Whether to invert depth (foreground becomes background).
        output_style: Output style for OpenSCAD generation (MVP: "relief" only).
    """

    base_thickness: float = 2.0
    max_height: float = 15.0
    model_width: float = 100.0
    detail_level: float = 1.0
    smoothing: bool = True
    invert_depth: bool = False
    output_style: str = "relief"

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.base_thickness <= 0:
            raise ValueError("base_thickness must be positive")
        if self.max_height <= 0:
            raise ValueError("max_height must be positive")
        if self.model_width <= 0:
            raise ValueError("model_width must be positive")
        if not 0.5 <= self.detail_level <= 2.0:
            raise ValueError("detail_level must be between 0.5 and 2.0")
        if self.output_style not in ("relief",):
            raise ValueError(f"Unsupported output_style: {self.output_style}")

    def to_dict(self) -> dict:
        """
        Serialize configuration to a dictionary.

        Returns:
            dict: Configuration as dictionary.
        """
        return {
            "base_thickness": self.base_thickness,
            "max_height": self.max_height,
            "model_width": self.model_width,
            "detail_level": self.detail_level,
            "smoothing": self.smoothing,
            "invert_depth": self.invert_depth,
            "output_style": self.output_style,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversionConfig":
        """
        Create configuration from a dictionary.

        Args:
            data: Dictionary with configuration values.

        Returns:
            ConversionConfig: New configuration instance.
        """
        return cls(
            base_thickness=data.get("base_thickness", 2.0),
            max_height=data.get("max_height", 15.0),
            model_width=data.get("model_width", 100.0),
            detail_level=data.get("detail_level", 1.0),
            smoothing=data.get("smoothing", True),
            invert_depth=data.get("invert_depth", False),
            output_style=data.get("output_style", "relief"),
        )


@dataclass
class HeightData:
    """
    Processed height data ready for OpenSCAD generation.

    Attributes:
        heights: 2D numpy array of height values in mm.
        width_mm: Physical width of the model in mm.
        height_mm: Physical height (depth) of the model in mm.
        resolution: Grid resolution as (rows, cols) tuple.
    """

    heights: np.ndarray
    width_mm: float
    height_mm: float
    resolution: Tuple[int, int] = field(init=False)

    def __post_init__(self) -> None:
        """Calculate resolution from heights array."""
        if self.heights.ndim != 2:
            raise ValueError("heights must be a 2D array")
        self.resolution = (self.heights.shape[0], self.heights.shape[1])


@dataclass
class ConversionResult:
    """
    Result of a conversion operation.

    Attributes:
        scad_code: Generated OpenSCAD code as a string.
        scad_path: Path to the saved .scad file, if saved.
        stl_path: Path to the rendered .stl file, if generated.
        depth_map: Intermediate depth map array for debugging.
        processing_time: Total processing time in seconds.
    """

    scad_code: str
    scad_path: Optional[Path] = None
    stl_path: Optional[Path] = None
    depth_map: Optional[np.ndarray] = None
    processing_time: float = 0.0
