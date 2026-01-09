"""
image_to_scad - AI-powered image to OpenSCAD converter.

This package provides tools for converting 2D images into 3D relief models
using depth estimation AI and OpenSCAD code generation.

Main components:
    - Converter: Main pipeline orchestrator for image-to-SCAD conversion
    - ConversionConfig: Configuration dataclass for conversion parameters
    - ConversionResult: Result dataclass containing generated output

Example usage:
    >>> from image_to_scad import Converter, ConversionConfig
    >>> config = ConversionConfig(max_height=15.0, model_width=100.0)
    >>> converter = Converter()
    >>> result = converter.convert("input.jpg", config)
    >>> print(result.scad_code)
"""

from image_to_scad.config import ConversionConfig, HeightData, ConversionResult
from image_to_scad.converter import Converter
from image_to_scad.exceptions import (
    ImageToScadError,
    ImageLoadError,
    DepthEstimationError,
    DepthAnalysisError,
    OpenSCADGenerationError,
    STLExportError,
    ConfigurationError,
)

__version__ = "0.1.0"
__author__ = "David"
__all__ = [
    # Main classes
    "Converter",
    "ConversionConfig",
    "ConversionResult",
    "HeightData",
    # Exceptions
    "ImageToScadError",
    "ImageLoadError",
    "DepthEstimationError",
    "DepthAnalysisError",
    "OpenSCADGenerationError",
    "STLExportError",
    "ConfigurationError",
    # Metadata
    "__version__",
]
