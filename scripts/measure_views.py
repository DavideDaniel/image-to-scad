#!/usr/bin/env python3
"""Measure object silhouette proportions from orthographic-ish view images.

Object-agnostic helper for the component-model workflow: it does NOT know what
the object is, it only reports how big the silhouette is in each view and, if
you anchor one real-world dimension, estimates the others by proportion.

Views are passed as label=path pairs. Labels are free-form, but the standard
labels front / right / top unlock cross-view estimates:
  - front  -> width x height
  - right  -> depth x height
  - top    -> width x depth

Usage:
    python scripts/measure_views.py front=f.png right=r.png top=t.png \
        [--width-mm 180] [--threshold 210] [--output measurements.json]

With --width-mm (real overall width), prints estimated overall height and
depth in mm. Depth blends the top view (0.8) with the right view (0.2) when
both exist, matching the original stand workflow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


def object_bbox(path: Path, threshold: int = 210) -> tuple[int, int, int, int]:
    """Return a conservative bbox for the object silhouette.

    Uses the alpha channel when the image has a meaningful one (e.g. Blender
    renders); otherwise assumes a dark object on a light background.
    """
    image = Image.open(path)
    rgba = np.asarray(image.convert("RGBA"))
    alpha = rgba[..., 3]
    if alpha.min() < 250:
        mask = alpha > 8
    else:
        gray = np.asarray(image.convert("L"))
        mask = gray < threshold

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        raise ValueError(
            f"could not find object pixels in {path} "
            f"(threshold {threshold}; try --threshold for darker/lighter backgrounds)"
        )
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _display_path(path: Path) -> str:
    """Portable form of a path for output metadata: cwd-relative, never absolute."""
    try:
        return str(path.resolve().relative_to(Path.cwd()))
    except ValueError:
        return path.name


def measure(views: dict[str, Path], threshold: int, width_mm: float | None) -> dict[str, Any]:
    result: dict[str, Any] = {"schema": "view-measurements/v0", "views": {}, "units": "px"}
    for label, path in views.items():
        x0, y0, x1, y1 = object_bbox(path, threshold)
        w = x1 - x0 + 1
        h = y1 - y0 + 1
        result["views"][label] = {
            "image": _display_path(path),
            "bbox_px": [x0, y0, x1, y1],
            "width_px": w,
            "height_px": h,
            "aspect_w_over_h": round(w / h, 4),
        }

    front = result["views"].get("front")
    right = result["views"].get("right")
    top = result["views"].get("top")

    if width_mm and front:
        est: dict[str, float] = {"width_mm": width_mm}
        height_mm = width_mm * front["height_px"] / front["width_px"]
        est["height_mm"] = round(height_mm, 3)
        depth_from_top = width_mm * top["height_px"] / top["width_px"] if top else None
        depth_from_side = height_mm * right["width_px"] / right["height_px"] if right else None
        if depth_from_top is not None and depth_from_side is not None:
            est["depth_mm"] = round(depth_from_top * 0.8 + depth_from_side * 0.2, 3)
            est["depth_from_top_mm"] = round(depth_from_top, 3)
            est["depth_from_side_mm"] = round(depth_from_side, 3)
        elif depth_from_top is not None:
            est["depth_mm"] = round(depth_from_top, 3)
        elif depth_from_side is not None:
            est["depth_mm"] = round(depth_from_side, 3)
        result["estimated_overall_mm"] = est

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("views", nargs="+", help="View images as label=path pairs (e.g. front=f.png).")
    parser.add_argument("--threshold", type=int, default=210, help="Gray level below which pixels count as object.")
    parser.add_argument("--width-mm", type=float, help="Real overall width; unlocks mm estimates (needs a front view).")
    parser.add_argument("--output", type=Path, help="Also write the JSON to this path.")
    args = parser.parse_args()

    views: dict[str, Path] = {}
    for spec in args.views:
        if "=" not in spec:
            parser.error(f"expected label=path, got: {spec}")
        label, _, raw = spec.partition("=")
        path = Path(raw)
        if not path.exists():
            parser.error(f"no such image: {path}")
        views[label] = path

    result = measure(views, args.threshold, args.width_mm)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")
        print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
