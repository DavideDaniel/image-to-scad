"""
Entry point for running image_to_scad as a module.

Usage:
    python -m image_to_scad input.jpg -o output.scad
    python -m image_to_scad --help
"""

from image_to_scad.cli import main

if __name__ == "__main__":
    main()
