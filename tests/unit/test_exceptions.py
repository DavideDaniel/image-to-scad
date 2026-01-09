"""
Unit tests for image_to_scad.exceptions module.
"""

import pytest

from image_to_scad.exceptions import (
    ImageToScadError,
    ImageLoadError,
    DepthEstimationError,
    DepthAnalysisError,
    OpenSCADGenerationError,
    STLExportError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_base_exception(self):
        """Test that ImageToScadError can be raised."""
        with pytest.raises(ImageToScadError):
            raise ImageToScadError("test error")

    def test_image_load_error_inheritance(self):
        """Test that ImageLoadError inherits from ImageToScadError."""
        assert issubclass(ImageLoadError, ImageToScadError)

        with pytest.raises(ImageToScadError):
            raise ImageLoadError("image error")

    def test_depth_estimation_error_inheritance(self):
        """Test that DepthEstimationError inherits from ImageToScadError."""
        assert issubclass(DepthEstimationError, ImageToScadError)

        with pytest.raises(ImageToScadError):
            raise DepthEstimationError("depth error")

    def test_depth_analysis_error_inheritance(self):
        """Test that DepthAnalysisError inherits from ImageToScadError."""
        assert issubclass(DepthAnalysisError, ImageToScadError)

    def test_openscad_generation_error_inheritance(self):
        """Test that OpenSCADGenerationError inherits from ImageToScadError."""
        assert issubclass(OpenSCADGenerationError, ImageToScadError)

    def test_stl_export_error_inheritance(self):
        """Test that STLExportError inherits from ImageToScadError."""
        assert issubclass(STLExportError, ImageToScadError)

    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from ImageToScadError."""
        assert issubclass(ConfigurationError, ImageToScadError)

    def test_catch_all_package_errors(self):
        """Test that all exceptions can be caught with ImageToScadError."""
        exceptions = [
            ImageLoadError("test"),
            DepthEstimationError("test"),
            DepthAnalysisError("test"),
            OpenSCADGenerationError("test"),
            STLExportError("test"),
            ConfigurationError("test"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except ImageToScadError as e:
                assert str(e) == "test"

    def test_exception_messages(self):
        """Test that exceptions preserve messages."""
        msg = "Detailed error message"
        exc = ImageLoadError(msg)
        assert str(exc) == msg
