"""
Command-line interface for image_to_scad.

This module provides the CLI for converting images to OpenSCAD files.

Usage:
    image-to-scad input.jpg -o output.scad
    image-to-scad input.png --max-height 20 --width 150 --stl
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from image_to_scad.config import ConversionConfig
from image_to_scad.converter import Converter
from image_to_scad.utils.logging import setup_logging, get_logger


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="image-to-scad",
        description="Convert 2D images to 3D relief models using AI depth estimation.",
        epilog="Example: image-to-scad photo.jpg -o relief.scad --max-height 15",
    )

    # Required arguments
    parser.add_argument(
        "input",
        type=Path,
        help="Input image file (JPG, PNG, WebP, BMP, or TIFF)",
    )

    # Output options
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output .scad file path (default: input_name.scad)",
    )
    parser.add_argument(
        "--stl",
        action="store_true",
        help="Also generate STL file (requires OpenSCAD)",
    )

    # Model parameters
    parser.add_argument(
        "--base-thickness",
        type=float,
        default=2.0,
        metavar="MM",
        help="Base thickness in mm (default: 2.0)",
    )
    parser.add_argument(
        "--max-height",
        type=float,
        default=15.0,
        metavar="MM",
        help="Maximum relief height in mm (default: 15.0)",
    )
    parser.add_argument(
        "--width",
        type=float,
        default=100.0,
        metavar="MM",
        help="Model width in mm (default: 100.0)",
    )
    parser.add_argument(
        "--detail",
        type=float,
        default=1.0,
        metavar="LEVEL",
        help="Detail level 0.5-2.0 (default: 1.0)",
    )

    # Processing options
    parser.add_argument(
        "--no-smoothing",
        action="store_true",
        help="Disable smoothing filter",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert depth (foreground becomes background)",
    )

    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: List of arguments to parse. If None, uses sys.argv.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = create_parser()
    return parser.parse_args(args)


def validate_args(args: argparse.Namespace) -> None:
    """
    Validate parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Raises:
        ValueError: If arguments are invalid.
        FileNotFoundError: If input file doesn't exist.
    """
    # Check input file exists
    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    # Check input file is a file
    if not args.input.is_file():
        raise ValueError(f"Input path is not a file: {args.input}")

    # Validate detail level
    if not 0.5 <= args.detail <= 2.0:
        raise ValueError("Detail level must be between 0.5 and 2.0")

    # Validate positive dimensions
    if args.base_thickness <= 0:
        raise ValueError("Base thickness must be positive")
    if args.max_height <= 0:
        raise ValueError("Max height must be positive")
    if args.width <= 0:
        raise ValueError("Width must be positive")


def build_config(args: argparse.Namespace) -> ConversionConfig:
    """
    Build ConversionConfig from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        ConversionConfig: Configuration object for conversion.
    """
    return ConversionConfig(
        base_thickness=args.base_thickness,
        max_height=args.max_height,
        model_width=args.width,
        detail_level=args.detail,
        smoothing=not args.no_smoothing,
        invert_depth=args.invert,
    )


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: List of arguments to parse. If None, uses sys.argv.

    Returns:
        int: Exit code (0 for success, non-zero for errors).
    """
    try:
        parsed_args = parse_args(args)
        validate_args(parsed_args)

        # Setup logging
        if parsed_args.quiet:
            log_level = "ERROR"
        elif parsed_args.verbose:
            log_level = "DEBUG"
        else:
            log_level = "INFO"
        setup_logging(log_level)
        logger = get_logger(__name__)

        # Build configuration
        config = build_config(parsed_args)

        # Determine output path
        output_path = parsed_args.output
        if output_path is None:
            output_path = parsed_args.input.with_suffix(".scad")

        # Run conversion
        logger.info(f"Converting {parsed_args.input} to {output_path}")
        converter = Converter()
        result = converter.convert(
            input_path=parsed_args.input,
            output_path=output_path,
            config=config,
            generate_stl=parsed_args.stl,
        )

        # Report results
        logger.info(f"Generated: {result.scad_path}")
        if result.stl_path:
            logger.info(f"Generated: {result.stl_path}")
        logger.info(f"Processing time: {result.processing_time:.2f}s")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
