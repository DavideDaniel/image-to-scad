"""
File I/O utility functions.

This module provides helper functions for file operations
used throughout the image_to_scad package.
"""

from pathlib import Path
from typing import Union


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.

    Returns:
        Path: The directory path.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_scad(code: str, path: Union[str, Path]) -> Path:
    """
    Save OpenSCAD code to a file.

    Args:
        code: OpenSCAD code to save.
        path: Path for the output file.

    Returns:
        Path: The path to the saved file.
    """
    path = Path(path)

    # Ensure parent directory exists
    if path.parent:
        ensure_directory(path.parent)

    # Ensure .scad extension
    if path.suffix.lower() != ".scad":
        path = path.with_suffix(".scad")

    path.write_text(code, encoding="utf-8")
    return path


def get_output_path(
    input_path: Path,
    output_dir: Path = None,
    suffix: str = ".scad",
) -> Path:
    """
    Generate an output path based on input path.

    Args:
        input_path: Path to the input file.
        output_dir: Directory for output. If None, uses input directory.
        suffix: File suffix for output.

    Returns:
        Path: Generated output path.
    """
    input_path = Path(input_path)

    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)

    return output_dir / (input_path.stem + suffix)


def validate_output_path(path: Path) -> None:
    """
    Validate that an output path is writable.

    Args:
        path: Path to validate.

    Raises:
        ValueError: If path is not writable.
    """
    path = Path(path)
    parent = path.parent

    if parent and not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot create output directory: {e}") from e

    # Check if we can write to the directory
    if parent.exists() and not parent.is_dir():
        raise ValueError(f"Output path parent is not a directory: {parent}")
