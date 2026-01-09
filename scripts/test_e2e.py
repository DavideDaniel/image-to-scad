#!/usr/bin/env python3
"""
End-to-end test script for image-to-scad conversion.

Usage:
    python scripts/test_e2e.py <image_path> [output_dir]

Example:
    python scripts/test_e2e.py ~/Desktop/cupholder.jpg ./output
"""

import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from image_to_scad import Converter, ConversionConfig
from image_to_scad.utils.logging import setup_logging


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_e2e.py <image_path> [output_dir]")
        print("\nExample:")
        print("  python scripts/test_e2e.py ~/Desktop/cupholder.jpg ./output")
        sys.exit(1)

    image_path = Path(sys.argv[1]).expanduser()
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./output")

    # Setup
    setup_logging("INFO")
    output_dir.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print("IMAGE-TO-SCAD END-TO-END TEST")
    print(f"{'='*60}")
    print(f"Input:  {image_path}")
    print(f"Output: {output_dir}")

    # Verify input exists
    if not image_path.exists():
        print(f"\nERROR: Image not found: {image_path}")
        sys.exit(1)

    # Configure conversion
    config = ConversionConfig(
        base_thickness=2.0,
        max_height=15.0,
        model_width=100.0,
        detail_level=1.0,
        smoothing=True,
        invert_depth=False,
    )

    print(f"\nConfiguration:")
    print(f"  Base thickness: {config.base_thickness}mm")
    print(f"  Max height:     {config.max_height}mm")
    print(f"  Model width:    {config.model_width}mm")
    print(f"  Detail level:   {config.detail_level}")
    print(f"  Smoothing:      {config.smoothing}")
    print(f"  Invert depth:   {config.invert_depth}")

    # Run conversion
    print(f"\n{'='*60}")
    print("RUNNING CONVERSION")
    print(f"{'='*60}")

    output_path = output_dir / f"{image_path.stem}.scad"

    start_time = time.time()
    converter = Converter()

    def progress_callback(stage: str, progress: float):
        print(f"  [{progress*100:3.0f}%] {stage}")

    try:
        result = converter.convert(
            input_path=image_path,
            output_path=output_path,
            config=config,
            generate_stl=False,  # Skip STL for now
            progress_callback=progress_callback,
        )

        total_time = time.time() - start_time

        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"  Status:          SUCCESS")
        print(f"  Processing time: {result.processing_time:.2f}s")
        print(f"  Total time:      {total_time:.2f}s")
        print(f"  SCAD file:       {result.scad_path}")
        print(f"  Code length:     {len(result.scad_code):,} chars")

        if result.depth_map is not None:
            print(f"  Depth map shape: {result.depth_map.shape}")
            print(f"  Depth range:     [{result.depth_map.min():.2f}, {result.depth_map.max():.2f}]")

        # Show preview of generated code
        print(f"\n{'='*60}")
        print("GENERATED CODE (first 50 lines)")
        print(f"{'='*60}")
        lines = result.scad_code.split('\n')[:50]
        for line in lines:
            print(line)
        if len(result.scad_code.split('\n')) > 50:
            print(f"... ({len(result.scad_code.split(chr(10))) - 50} more lines)")

        print(f"\n{'='*60}")
        print(f"Output saved to: {result.scad_path}")
        print(f"Open in OpenSCAD to preview the 3D model")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        converter.release_model()


if __name__ == "__main__":
    main()
