"""
Exception hierarchy for image_to_scad.

This module defines custom exceptions for error handling throughout
the conversion pipeline. All exceptions inherit from ImageToScadError.
"""


class ImageToScadError(Exception):
    """
    Base exception for all image_to_scad errors.

    All custom exceptions in this package inherit from this class,
    allowing users to catch all package-specific errors with a single
    except clause.
    """

    pass


class ImageLoadError(ImageToScadError):
    """
    Exception raised when image loading or validation fails.

    This includes:
    - File not found
    - Unsupported image format
    - Corrupted image file
    - Image dimensions out of range
    """

    pass


class DepthEstimationError(ImageToScadError):
    """
    Exception raised when depth estimation fails.

    This includes:
    - Model loading failures
    - Model download failures
    - Inference errors
    - Invalid input format
    """

    pass


class DepthAnalysisError(ImageToScadError):
    """
    Exception raised when depth analysis fails.

    This includes:
    - Invalid depth map format
    - Processing errors
    """

    pass


class OpenSCADGenerationError(ImageToScadError):
    """
    Exception raised when OpenSCAD code generation fails.

    This includes:
    - Invalid height data
    - Template rendering errors
    """

    pass


class STLExportError(ImageToScadError):
    """
    Exception raised when STL export fails.

    This includes:
    - OpenSCAD not found
    - OpenSCAD rendering errors
    - Timeout during rendering
    - Invalid output file
    """

    pass


class ConfigurationError(ImageToScadError):
    """
    Exception raised for configuration errors.

    This includes:
    - Invalid parameter values
    - Missing required configuration
    """

    pass
