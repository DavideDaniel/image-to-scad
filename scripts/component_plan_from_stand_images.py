#!/usr/bin/env python3
"""Infer a simple component plan for a rectilinear stand from multiview images.

This is intentionally a proof-of-concept for the "image -> components -> Blender"
path. It targets the sample stand class: a symmetric, planar object made from
rectangular slabs. The output is editable JSON consumed by
scripts/blender_build_components.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


FRONT_NAMES = ("01_front.png", "05_back.png")
RIGHT_NAME = "03_right.png"
TOP_NAME = "06_top.png"


def _load_gray(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("L"))


def _object_bbox(path: Path, threshold: int = 210) -> tuple[int, int, int, int]:
    """Return a conservative bbox for the gray object on the light background."""
    gray = _load_gray(path)
    mask = gray < threshold

    # Remove tiny speckles but keep long straight model edges.
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        raise ValueError(f"could not find object pixels in {path}")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _round(value: float) -> float:
    return round(value, 3)


def _display_path(path: Path) -> str:
    """Portable form of a path for plan metadata: cwd-relative, never absolute."""
    try:
        return str(path.resolve().relative_to(Path.cwd()))
    except ValueError:
        return path.name


def infer_plan(
    image_dir: Path,
    width_mm: float,
    depth_mm: float | None,
    clearance_mm: float | None,
    mug_wells: int,
    well_diameter_mm: float | None,
    well_depth_mm: float,
    well_style: str,
    modular: bool,
    stackable: bool,
) -> dict[str, Any]:
    front_path = next((image_dir / name for name in FRONT_NAMES if (image_dir / name).exists()), None)
    if front_path is None:
        raise FileNotFoundError(f"expected one of {FRONT_NAMES} in {image_dir}")

    top_path = image_dir / TOP_NAME
    right_path = image_dir / RIGHT_NAME
    if not top_path.exists():
        raise FileNotFoundError(f"expected {TOP_NAME} in {image_dir}")
    if not right_path.exists():
        raise FileNotFoundError(f"expected {RIGHT_NAME} in {image_dir}")

    fx0, fy0, fx1, fy1 = _object_bbox(front_path)
    tx0, ty0, tx1, ty1 = _object_bbox(top_path)
    rx0, ry0, rx1, ry1 = _object_bbox(right_path)

    front_w_px = fx1 - fx0 + 1
    front_h_px = fy1 - fy0 + 1
    top_w_px = tx1 - tx0 + 1
    top_d_px = ty1 - ty0 + 1
    right_d_px = rx1 - rx0 + 1
    right_h_px = ry1 - ry0 + 1

    total_w = width_mm
    total_h = width_mm * front_h_px / front_w_px
    # Prefer the top view for footprint depth, lightly blended with side view.
    depth_from_top = width_mm * top_d_px / top_w_px
    depth_from_side = total_h * right_d_px / right_h_px
    total_d = depth_mm or ((depth_from_top * 0.8) + (depth_from_side * 0.2))

    if clearance_mm:
        top_thick = max(total_w * 0.055, 14.0)
        raised_h = max(top_thick * 0.34, 4.0)
        leg_h = clearance_mm
        total_h = leg_h + top_thick
    else:
        top_thick = total_h * 0.16
        raised_h = total_h * 0.055
        leg_h = total_h - top_thick
    leg_w = total_w * 0.078
    foot_h = max(total_h * 0.04, 2.0)
    foot_d = total_d * 0.14
    side_lip_w = total_w * 0.024
    inset_x = total_w * 0.026
    inset_y = total_d * 0.055
    bevel = max(min(total_w, total_d, total_h) * 0.008, 0.6)
    join_overlap = max(total_h * 0.008, 0.4)

    components = [
        {
            "name": "top_main_beam",
            "type": "box",
            "size": [_round(total_w), _round(total_d), _round(top_thick)],
            "center": [0, 0, _round(leg_h + top_thick / 2)],
        },
        {
            "name": "top_raised_slab",
            "type": "box",
            "size": [
                _round(total_w - 2 * inset_x),
                _round(total_d - 2 * inset_y),
                _round(raised_h + join_overlap),
            ],
            "center": [0, 0, _round(leg_h + top_thick + raised_h / 2 - join_overlap / 2)],
        },
        {
            "name": "left_leg",
            "type": "box",
            "size": [_round(leg_w), _round(total_d), _round(leg_h + join_overlap)],
            "center": [_round(-total_w / 2 + leg_w / 2), 0, _round(leg_h / 2 + join_overlap / 2)],
        },
        {
            "name": "right_leg",
            "type": "box",
            "size": [_round(leg_w), _round(total_d), _round(leg_h + join_overlap)],
            "center": [_round(total_w / 2 - leg_w / 2), 0, _round(leg_h / 2 + join_overlap / 2)],
        },
        {
            "name": "left_inner_foot_lip",
            "type": "box",
            "size": [_round(leg_w + side_lip_w), _round(foot_d), _round(foot_h)],
            "center": [
                _round(-total_w / 2 + (leg_w + side_lip_w) / 2),
                _round(-total_d / 2 + foot_d / 2),
                _round(foot_h / 2),
            ],
        },
        {
            "name": "right_inner_foot_lip",
            "type": "box",
            "size": [_round(leg_w + side_lip_w), _round(foot_d), _round(foot_h)],
            "center": [
                _round(total_w / 2 - (leg_w + side_lip_w) / 2),
                _round(-total_d / 2 + foot_d / 2),
                _round(foot_h / 2),
            ],
        },
    ]

    cuts: list[dict[str, Any]] = []
    top_z = leg_h + top_thick + raised_h
    if mug_wells > 0:
        usable_w = total_w - (2 * inset_x) - (2 * leg_w)
        spacing = usable_w / mug_wells
        diameter = well_diameter_mm or min(spacing * 0.68, total_d * 0.82)
        diameter = min(diameter, total_d - 6.0)
        start_x = -usable_w / 2 + spacing / 2
        for index in range(mug_wells):
            x = start_x + index * spacing
            cx = 0 if abs(x) < 0.001 else _round(x)
            if well_style == "rim":
                ring_width = max(min(diameter * 0.06, 4.0), 2.4)
                ring_h = max(well_depth_mm, 1.2)
                components.append(
                    {
                        "name": f"mug_locator_outer_{index + 1}",
                        "type": "cylinder",
                        "radius": _round(diameter / 2 + ring_width),
                        "depth": _round(ring_h + join_overlap),
                        "center": [cx, 0, _round(top_z + ring_h / 2 - join_overlap / 2)],
                        "vertices": 192,
                        "role": "raised circular locator ring",
                    }
                )
                cuts.append(
                    {
                        "name": f"mug_locator_inner_{index + 1}",
                        "type": "cylinder",
                        "radius": _round(diameter / 2),
                        "depth": _round(ring_h + join_overlap + 0.8),
                        "center": [cx, 0, _round(top_z + ring_h / 2 - join_overlap / 2)],
                        "vertices": 192,
                        "role": "open center of raised mug locator ring",
                    }
                )
            else:
                cuts.append(
                    {
                        "name": f"mug_well_{index + 1}",
                        "type": "cylinder",
                        "radius": _round(diameter / 2),
                        "depth": _round(well_depth_mm + 0.25),
                        "center": [cx, 0, _round(top_z - well_depth_mm / 2 + 0.125)],
                        "vertices": 160,
                        "role": "shallow circular recess for mug base",
                    }
                )

    if modular:
        rail_w = max(total_w * 0.018, 3.0)
        rail_h = max(total_h * 0.06, 3.5)
        slot_clearance = 0.35
        # Cut matching side sockets for a separate printed clip. This keeps the
        # shelf body watertight and avoids fragile protruding rails.
        for side, sign in (("left", -1), ("right", 1)):
            cuts.append(
                {
                    "name": f"{side}_side_clip_socket",
                    "type": "box",
                    "size": [_round(rail_w + slot_clearance), _round(total_d * 0.62), _round(rail_h + slot_clearance)],
                    "center": [
                        _round(sign * (total_w / 2 - (rail_w + slot_clearance) / 2 - 0.2)),
                        0,
                        _round(leg_h * 0.55),
                    ],
                    "role": "side-by-side clip socket",
                }
            )

    if stackable:
        peg_radius = max(min(total_w, total_d) * 0.055, 8.0)
        peg_depth = max(total_h * 0.075, 8.0)
        boss_radius = peg_radius + 5.0
        boss_height = max(total_h * 0.035, 4.0)
        socket_clearance = 0.65
        socket_depth = peg_depth + 1.2
        peg_x = total_w / 2 - leg_w / 2
        peg_y = total_d / 2 - max(boss_radius + 5.0, 18.0)
        boss_top_z = top_z + boss_height
        for side, x in (("left", -peg_x), ("right", peg_x)):
            for row, y in (("front", -peg_y), ("back", peg_y)):
                components.append(
                    {
                        "name": f"{side}_{row}_stacking_top_pad",
                        "type": "cylinder",
                        "radius": _round(boss_radius),
                        "depth": _round(boss_height + join_overlap),
                        "center": [_round(x), _round(y), _round(top_z + boss_height / 2 - join_overlap / 2)],
                        "vertices": 112,
                        "role": "visible top load pad for stacking",
                    }
                )
                components.append(
                    {
                        "name": f"{side}_{row}_stacking_foot",
                        "type": "cylinder",
                        "radius": _round(peg_radius),
                        "depth": _round(peg_depth),
                        "center": [_round(x), _round(y), _round(-peg_depth / 2 + join_overlap)],
                        "vertices": 112,
                        "role": "bottom stacking registration peg",
                    }
                )
                cuts.append(
                    {
                        "name": f"{side}_{row}_stacking_socket",
                        "type": "cylinder",
                        "radius": _round(peg_radius + socket_clearance),
                        "depth": _round(socket_depth),
                        "center": [_round(x), _round(y), _round(boss_top_z - socket_depth / 2 + 0.2)],
                        "vertices": 112,
                        "role": "top receiver pocket inside visible stacking pad",
                    }
                )

    return {
        "schema": "component-plan/v0",
        "generator": "component_plan_from_stand_images.py",
        "source_images": {
            "front": _display_path(front_path),
            "right": _display_path(right_path),
            "top": _display_path(top_path),
        },
        "measurements": {
            "front_bbox_px": [fx0, fy0, fx1, fy1],
            "top_bbox_px": [tx0, ty0, tx1, ty1],
            "right_bbox_px": [rx0, ry0, rx1, ry1],
            "front_width_px": front_w_px,
            "front_height_px": front_h_px,
            "top_width_px": top_w_px,
            "top_depth_px": top_d_px,
            "right_depth_px": right_d_px,
            "right_height_px": right_h_px,
        },
        "units": "mm",
        "model": {
            "name": "rectilinear_stand",
            "strategy": "component_boxes",
            "design_intent": "stackable modular mug shelf" if stackable else (
                "modular mug shelf" if modular or mug_wells else "rectilinear stand"
            ),
            "target_width": _round(total_w),
            "inferred_depth": _round(total_d),
            "inferred_height": _round(total_h + raised_h),
            "internal_clearance": _round(leg_h),
            "bevel": _round(bevel),
            "components": components,
            "cuts": cuts,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Infer a rectilinear stand component plan from multiview images.")
    parser.add_argument("image_dir", type=Path, help="Folder containing 01_front.png, 03_right.png, 06_top.png.")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output JSON component plan.")
    parser.add_argument("--width-mm", type=float, default=180.0, help="Target overall stand width in mm.")
    parser.add_argument("--depth-mm", type=float, help="Override inferred depth with a functional shelf depth.")
    parser.add_argument("--clearance-mm", type=float, help="Override internal cup clearance under the shelf.")
    parser.add_argument("--mug-wells", type=int, default=0, help="Add this many shallow circular mug recesses.")
    parser.add_argument("--well-diameter-mm", type=float, help="Diameter of mug recesses. Defaults from shelf proportions.")
    parser.add_argument("--well-depth-mm", type=float, default=1.4, help="Depth of mug recesses.")
    parser.add_argument("--well-style", choices=["recess", "rim"], default="recess", help="Mug locator style.")
    parser.add_argument("--modular", action="store_true", help="Add simple side alignment key/socket features.")
    parser.add_argument("--stackable", action="store_true", help="Add bottom stacking feet and top receiver pockets.")
    args = parser.parse_args()

    plan = infer_plan(
        args.image_dir,
        args.width_mm,
        args.depth_mm,
        args.clearance_mm,
        args.mug_wells,
        args.well_diameter_mm,
        args.well_depth_mm,
        args.well_style,
        args.modular,
        args.stackable,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n")
    model = plan["model"]
    print(f"Wrote {args.output}")
    print(
        "Inferred stand: "
        f"{model['target_width']}w x {model['inferred_depth']}d x {model['inferred_height']}h mm, "
        f"{len(model['components'])} components"
    )


if __name__ == "__main__":
    main()
