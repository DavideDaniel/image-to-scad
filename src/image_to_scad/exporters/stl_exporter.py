"""
STL export using OpenSCAD command-line interface.

This module provides functionality to render OpenSCAD files
to STL format using the OpenSCAD CLI.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from image_to_scad.exceptions import STLExportError
from image_to_scad.utils.logging import get_logger


# Default timeout for OpenSCAD rendering (5 minutes)
DEFAULT_RENDER_TIMEOUT = 300


class STLExporter:
    """
    Export OpenSCAD files to STL format using OpenSCAD CLI.

    This class wraps the OpenSCAD command-line interface to render
    .scad files to .stl format.

    Example:
        >>> exporter = STLExporter()
        >>> stl_path = exporter.export(Path("model.scad"))
        >>> print(f"Generated: {stl_path}")
    """

    def __init__(
        self,
        openscad_path: Optional[str] = None,
        timeout: int = DEFAULT_RENDER_TIMEOUT,
    ) -> None:
        """
        Initialize the STL exporter.

        Args:
            openscad_path: Path to OpenSCAD executable. If None, searches PATH.
            timeout: Timeout for rendering in seconds.
        """
        self._logger = get_logger(__name__)
        self._openscad_path = openscad_path
        self._timeout = timeout

    def export(
        self,
        scad_path: Path,
        stl_path: Optional[Path] = None,
    ) -> Path:
        """
        Export an OpenSCAD file to STL format.

        Args:
            scad_path: Path to the input .scad file.
            stl_path: Path for the output .stl file. If None, uses same
                     name as input with .stl extension.

        Returns:
            Path: Path to the generated STL file.

        Raises:
            STLExportError: If export fails.
            FileNotFoundError: If input file doesn't exist.
        """
        scad_path = Path(scad_path)

        if not scad_path.exists():
            raise FileNotFoundError(f"OpenSCAD file not found: {scad_path}")

        if stl_path is None:
            stl_path = scad_path.with_suffix(".stl")
        else:
            stl_path = Path(stl_path)

        # Find OpenSCAD executable
        openscad_cmd = self._find_openscad()

        # Build command
        cmd = [
            openscad_cmd,
            "-o", str(stl_path),
            str(scad_path),
        ]

        self._logger.info(f"Rendering STL: {scad_path.name} -> {stl_path.name}")
        self._logger.debug(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise STLExportError(f"OpenSCAD rendering failed: {error_msg}")

            if not stl_path.exists():
                raise STLExportError("OpenSCAD completed but STL file was not created")

            self._logger.info(f"STL export complete: {stl_path}")
            return stl_path

        except subprocess.TimeoutExpired:
            raise STLExportError(
                f"OpenSCAD rendering timed out after {self._timeout} seconds"
            )
        except FileNotFoundError:
            raise STLExportError(
                f"OpenSCAD executable not found: {openscad_cmd}. "
                "Please install OpenSCAD: https://openscad.org/downloads.html"
            )

    def _find_openscad(self) -> str:
        """
        Find the OpenSCAD executable.

        Returns:
            str: Path to OpenSCAD executable.

        Raises:
            STLExportError: If OpenSCAD is not found.
        """
        if self._openscad_path:
            if Path(self._openscad_path).exists():
                return self._openscad_path
            raise STLExportError(f"OpenSCAD not found at: {self._openscad_path}")

        # Try common locations
        common_names = ["openscad", "OpenSCAD"]
        common_paths = [
            "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",  # macOS
            "/usr/bin/openscad",  # Linux
            "/usr/local/bin/openscad",  # Linux
            "C:\\Program Files\\OpenSCAD\\openscad.exe",  # Windows
        ]

        # Check PATH first
        for name in common_names:
            path = shutil.which(name)
            if path:
                self._logger.debug(f"Found OpenSCAD in PATH: {path}")
                return path

        # Check common installation locations
        for path in common_paths:
            if Path(path).exists():
                self._logger.debug(f"Found OpenSCAD at: {path}")
                return path

        raise STLExportError(
            "OpenSCAD not found. Please install OpenSCAD and ensure it's in your PATH. "
            "Download from: https://openscad.org/downloads.html"
        )

    def is_available(self) -> bool:
        """
        Check if OpenSCAD is available on the system.

        Returns:
            bool: True if OpenSCAD is available.
        """
        try:
            self._find_openscad()
            return True
        except STLExportError:
            return False

    def get_version(self) -> Optional[str]:
        """
        Get the OpenSCAD version string.

        Returns:
            Optional[str]: Version string, or None if not available.
        """
        try:
            openscad_cmd = self._find_openscad()
            result = subprocess.run(
                [openscad_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() or result.stderr.strip()
        except (STLExportError, subprocess.SubprocessError):
            return None
