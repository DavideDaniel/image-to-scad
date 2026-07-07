#!/usr/bin/env python3
"""Run the rectilinear stand component proof-of-concept end to end."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a component-built stand STL from multiview images.")
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=ROOT / "examples/sample_images/stand_multiview",
        help="Multiview image folder.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs/component_stand_poc",
        help="Output directory.",
    )
    parser.add_argument("--width-mm", type=float, default=180.0, help="Target overall width.")
    parser.add_argument("--depth-mm", type=float, help="Functional shelf depth override.")
    parser.add_argument("--clearance-mm", type=float, help="Internal cup clearance under the shelf.")
    parser.add_argument("--mug-wells", type=int, default=2, help="Number of shallow top mug recesses.")
    parser.add_argument("--well-diameter-mm", type=float, help="Diameter of mug recesses.")
    parser.add_argument("--well-depth-mm", type=float, default=1.4, help="Depth of mug recesses.")
    parser.add_argument("--well-style", choices=["recess", "rim"], default="recess", help="Mug locator style.")
    parser.add_argument("--modular", action="store_true", help="Add side alignment key/socket details.")
    parser.add_argument("--stackable", action="store_true", help="Add bottom stacking feet and top receiver pockets.")
    parser.add_argument("--blender", default="blender", help="Blender executable.")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    plan = args.out_dir / "stand_plan.json"
    stl = args.out_dir / "stand_component.stl"
    obj = args.out_dir / "stand_component.obj"
    blend = args.out_dir / "stand_component.blend"
    renders = args.out_dir / "renders"

    plan_cmd = [
        sys.executable,
        str(ROOT / "scripts/component_plan_from_stand_images.py"),
        str(args.image_dir),
        "--output",
        str(plan),
        "--width-mm",
        str(args.width_mm),
        "--mug-wells",
        str(args.mug_wells),
        "--well-depth-mm",
        str(args.well_depth_mm),
        "--well-style",
        args.well_style,
    ]
    if args.well_diameter_mm:
        plan_cmd.extend(["--well-diameter-mm", str(args.well_diameter_mm)])
    if args.depth_mm:
        plan_cmd.extend(["--depth-mm", str(args.depth_mm)])
    if args.clearance_mm:
        plan_cmd.extend(["--clearance-mm", str(args.clearance_mm)])
    if args.modular:
        plan_cmd.append("--modular")
    if args.stackable:
        plan_cmd.append("--stackable")
    subprocess.run(plan_cmd, check=True)

    subprocess.run(
        [
            args.blender,
            "--background",
            "--python",
            str(ROOT / "scripts/blender_build_components.py"),
            "--",
            str(plan),
            str(stl),
            "--obj",
            str(obj),
            "--blend",
            str(blend),
            "--render-dir",
            str(renders),
        ],
        check=True,
    )

    print("\nComponent POC complete")
    print(f"Plan:    {plan}")
    print(f"STL:     {stl}")
    print(f"OBJ:     {obj}")
    print(f"Blend:   {blend}")
    print(f"Renders: {renders}")


if __name__ == "__main__":
    main()
