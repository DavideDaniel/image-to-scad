"""
Pipeline orchestration for image-to-OpenSCAD conversion.

This module provides the main Converter class that coordinates all
pipeline stages to convert an image to OpenSCAD code.
"""

import time
from pathlib import Path
from typing import Optional, Callable

import numpy as np

from image_to_scad.config import ConversionConfig, ConversionResult, HeightData
from image_to_scad.pipeline.image_loader import ImageLoader
from image_to_scad.pipeline.depth_estimator import DepthEstimator
from image_to_scad.pipeline.depth_analyzer import DepthAnalyzer
from image_to_scad.pipeline.scad_generator import OpenSCADGenerator
from image_to_scad.exporters.stl_exporter import STLExporter
from image_to_scad.utils.file_utils import save_scad
from image_to_scad.utils.logging import get_logger


# Type alias for progress callback
ProgressCallback = Callable[[str, float], None]


class Converter:
    """
    Main pipeline orchestrator for image-to-OpenSCAD conversion.

    This class coordinates the processing pipeline stages:
    1. Load and validate input image
    2. Estimate depth using AI model
    3. Analyze and process depth map
    4. Generate OpenSCAD code
    5. Optionally render to STL

    Example:
        >>> converter = Converter()
        >>> result = converter.convert("photo.jpg", Path("output.scad"))
        >>> print(f"Generated: {result.scad_path}")
    """

    def __init__(self) -> None:
        """Initialize the converter with pipeline components."""
        self._logger = get_logger(__name__)
        self._image_loader = ImageLoader()
        self._depth_estimator: Optional[DepthEstimator] = None  # Lazy loaded
        self._depth_analyzer = DepthAnalyzer()
        self._scad_generator = OpenSCADGenerator()
        self._stl_exporter = STLExporter()

    def _get_depth_estimator(self) -> DepthEstimator:
        """
        Get or create the depth estimator (lazy loading).

        Returns:
            DepthEstimator: Initialized depth estimator.
        """
        if self._depth_estimator is None:
            self._logger.info("Loading depth estimation model...")
            self._depth_estimator = DepthEstimator()
        return self._depth_estimator

    def convert(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        config: Optional[ConversionConfig] = None,
        generate_stl: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ConversionResult:
        """
        Convert an image to OpenSCAD code.

        Args:
            input_path: Path to input image file.
            output_path: Path for output .scad file. If None, derived from input.
            config: Conversion configuration. If None, uses defaults.
            generate_stl: Whether to also generate STL file.
            progress_callback: Optional callback for progress updates.
                              Called with (stage_name, progress_fraction).

        Returns:
            ConversionResult: Result containing generated code and file paths.

        Raises:
            FileNotFoundError: If input file doesn't exist.
            ValueError: If input file is invalid.
            RuntimeError: If conversion fails.
        """
        start_time = time.time()
        config = config or ConversionConfig()

        def report_progress(stage: str, progress: float) -> None:
            if progress_callback:
                progress_callback(stage, progress)
            self._logger.debug(f"{stage}: {progress*100:.0f}%")

        # Stage 1: Load image
        report_progress("Loading image", 0.0)
        input_path = Path(input_path)
        image = self._image_loader.load(input_path)
        report_progress("Loading image", 1.0)

        # Stage 2: Estimate depth
        report_progress("Estimating depth", 0.0)
        depth_estimator = self._get_depth_estimator()
        depth_map = depth_estimator.estimate(image)
        report_progress("Estimating depth", 1.0)

        # Stage 3: Analyze depth
        report_progress("Processing depth", 0.0)
        height_data = self._depth_analyzer.analyze(depth_map, config)
        report_progress("Processing depth", 1.0)

        # Stage 4: Generate OpenSCAD
        report_progress("Generating OpenSCAD", 0.0)
        scad_code = self._scad_generator.generate(height_data, config)
        report_progress("Generating OpenSCAD", 1.0)

        # Save SCAD file
        scad_path = None
        if output_path is not None:
            output_path = Path(output_path)
            scad_path = save_scad(scad_code, output_path)
            self._logger.info(f"Saved OpenSCAD file: {scad_path}")

        # Stage 5: Optional STL export
        stl_path = None
        if generate_stl and scad_path is not None:
            report_progress("Rendering STL", 0.0)
            stl_path = self._stl_exporter.export(scad_path)
            report_progress("Rendering STL", 1.0)
            self._logger.info(f"Saved STL file: {stl_path}")

        processing_time = time.time() - start_time

        return ConversionResult(
            scad_code=scad_code,
            scad_path=scad_path,
            stl_path=stl_path,
            depth_map=depth_map,
            processing_time=processing_time,
        )

    def estimate_depth_only(
        self,
        input_path: Path,
    ) -> np.ndarray:
        """
        Run only the depth estimation stage.

        Useful for debugging or visualizing the depth map.

        Args:
            input_path: Path to input image file.

        Returns:
            np.ndarray: Depth map as 2D numpy array.
        """
        image = self._image_loader.load(input_path)
        depth_estimator = self._get_depth_estimator()
        return depth_estimator.estimate(image)

    def release_model(self) -> None:
        """
        Release the depth estimation model from memory.

        Call this to free GPU/RAM when the model is no longer needed.
        """
        if self._depth_estimator is not None:
            self._depth_estimator.release()
            self._depth_estimator = None
            self._logger.info("Released depth estimation model")
