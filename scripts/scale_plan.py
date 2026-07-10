#!/usr/bin/env python3
"""Scale a component plan safely — geometry scales, tolerances don't.

Uniformly scaling an STL in the slicer breaks assemblies: joint clearances are
absolute printer tolerances (0.3 mm is 0.3 mm at any model size), so scaled
parts jam or rattle. This tool rescales the PLAN instead: all component/cut/
joint geometry (sizes, centers, radii, depths) is multiplied by the factor,
while every joint `clearance` is left untouched. The bevel scales but is
floored so it stays printable.

Usage:
    venv/bin/python scripts/scale_plan.py in.json out.json --factor 0.84
    venv/bin/python scripts/scale_plan.py in.json out.json --fit-bed 220 220 250 [--margin-mm 10]

--fit-bed computes the largest factor that fits the plan's footprint (with
margin) on the given bed, capped at 1.0 (it never scales up).

The output still needs a design-rule review before building (see the print-fit
skill): after scaling, check pegs are still >=2.5 mm radius, walls >=3 mm, and
functional dimensions (wells, slots) still make sense.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MIN_BEVEL_MM = 0.4


def _plan_bbox(model: dict) -> tuple[list[float], list[float]]:
    los, his = [], []
    for spec in model.get("components", []):
        c = spec["center"]
        if spec["type"] == "box":
            half = [s / 2 for s in spec["size"]]
        else:  # cylinder
            r, d = float(spec["radius"]), float(spec["depth"])
            axis = spec.get("axis", "z")
            half = {"x": [d / 2, r, r], "y": [r, d / 2, r], "z": [r, r, d / 2]}[axis]
        los.append([c[i] - half[i] for i in range(3)])
        his.append([c[i] + half[i] for i in range(3)])
    lo = [min(v[i] for v in los) for i in range(3)]
    hi = [max(v[i] for v in his) for i in range(3)]
    return lo, hi


def _scale_primitive(spec: dict, f: float) -> None:
    spec["center"] = [round(v * f, 3) for v in spec["center"]]
    if spec.get("type", "cylinder") == "box":
        spec["size"] = [round(v * f, 3) for v in spec["size"]]
    else:
        spec["radius"] = round(float(spec["radius"]) * f, 3)
        spec["depth"] = round(float(spec["depth"]) * f, 3)


def scale_plan(plan: dict, factor: float) -> dict:
    model = plan["model"]
    for spec in model.get("components", []):
        _scale_primitive(spec, factor)
    for spec in model.get("cuts", []):
        _scale_primitive(spec, factor)
    if "bevel" in model:
        model["bevel"] = round(max(float(model["bevel"]) * factor, MIN_BEVEL_MM), 3)
    assembly = model.get("assembly")
    if assembly:
        for joint in assembly.get("joints", []):
            _scale_primitive(joint["cylinder"], factor)
            # clearance intentionally NOT scaled: it is a printer tolerance
    plan.setdefault("scaling_history", []).append({"factor": round(factor, 4)})
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--factor", type=float, help="Explicit scale factor.")
    group.add_argument("--fit-bed", nargs=3, type=float, metavar=("X", "Y", "Z"),
                       help="Compute the factor to fit this bed (never scales up).")
    parser.add_argument("--margin-mm", type=float, default=10.0, help="Bed margin used with --fit-bed.")
    args = parser.parse_args()

    plan = json.loads(args.input.read_text())
    lo, hi = _plan_bbox(plan["model"])
    extents = [hi[i] - lo[i] for i in range(3)]

    if args.factor:
        factor = args.factor
    else:
        usable = [max(b - (args.margin_mm if i < 2 else 0), 1.0) for i, b in enumerate(args.fit_bed)]
        factor = min(1.0, *(usable[i] / extents[i] for i in range(3)))

    plan = scale_plan(plan, factor)
    args.output.write_text(json.dumps(plan, indent=2) + "\n")

    new_extents = [round(e * factor, 1) for e in extents]
    print(f"extents {['%.1f' % e for e in extents]} mm -> {new_extents} mm (factor {factor:.4f})")
    joints = plan["model"].get("assembly", {}).get("joints", [])
    for j in joints:
        r = j["cylinder"]["radius"]
        note = "  <-- REVIEW: peg under 2.5 mm radius" if r < 2.5 else ""
        print(f"joint {j['name']}: peg r={r} mm, clearance {j.get('clearance', 0.3)} mm (unchanged){note}")
    print(f"Wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
