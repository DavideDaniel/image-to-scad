#!/usr/bin/env python3
"""Static printability checks for STL files (FDM-oriented).

Reports, per file:
  - watertight / body count
  - floating bodies (disconnected pieces that never touch the bed plane)
  - overhang area beyond a threshold angle (faces that would need support)
  - bed contact area (small contact + tall part = tip-over risk)
  - extents vs bed size

Usage:
    venv/bin/python scripts/check_printability.py model.stl [more.stl ...] \
        [--bed-mm 256 256 256] [--overhang-deg 45] [--json report.json]

Exit code is 0 unless --strict is given, in which case any FAIL exits 1.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

BED_GAP_MM = 0.25          # a body starting higher than this off the bed is floating
CONTACT_BAND_MM = 0.3      # faces within this band of Z=0 count as bed contact


def check_mesh(path: Path, bed_mm: tuple[float, float, float], overhang_deg: float) -> dict[str, Any]:
    mesh = trimesh.load(str(path), force="mesh")
    # Normalize: sit the model on Z=0 like a slicer would.
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])

    result: dict[str, Any] = {
        "file": str(path),
        "watertight": bool(mesh.is_watertight),
        "bodies": int(mesh.body_count),
        "extents_mm": [round(float(v), 2) for v in mesh.extents],
        "issues": [],
    }

    # Floating bodies: disconnected pieces that never reach the bed.
    floating = []
    if mesh.body_count > 1:
        for body in mesh.split(only_watertight=False):
            gap = float(body.bounds[0][2])
            if gap > BED_GAP_MM:
                floating.append(round(gap, 2))
    result["floating_bodies"] = len(floating)
    if floating:
        result["issues"].append(
            f"FAIL: {len(floating)} disconnected bodies floating above the bed "
            f"(gaps: {floating} mm) — unprintable without redesign or assembly split"
        )

    # Overhangs: downward faces steeper than the threshold, excluding bed contact.
    normals = mesh.face_normals
    areas = mesh.area_faces
    face_z_min = mesh.vertices[mesh.faces][:, :, 2].min(axis=1)
    cos_limit = -math.cos(math.radians(overhang_deg))
    overhang_mask = (normals[:, 2] < cos_limit) & (face_z_min > CONTACT_BAND_MM)
    overhang_area = float(areas[overhang_mask].sum())
    total_area = float(areas.sum())
    pct = 100.0 * overhang_area / total_area if total_area else 0.0
    result["overhang_area_mm2"] = round(overhang_area, 1)
    result["overhang_pct_of_surface"] = round(pct, 2)
    if pct > 5.0:
        result["issues"].append(
            f"WARN: {pct:.1f}% of surface overhangs beyond {overhang_deg}° — needs supports "
            f"(or split into parts printed in better orientations)"
        )

    # Bed contact vs height: tip-over / adhesion heuristic.
    contact_mask = (normals[:, 2] < -0.9) & (face_z_min <= CONTACT_BAND_MM)
    contact_area = float(areas[contact_mask].sum())
    height = float(mesh.extents[2])
    result["bed_contact_mm2"] = round(contact_area, 1)
    if contact_area < 25.0 and height > 30.0:
        result["issues"].append(
            f"WARN: only {contact_area:.0f} mm² bed contact for a {height:.0f} mm tall part — "
            f"adhesion/tip-over risk"
        )

    # Bed fit.
    oversize = [
        f"{axis}={ext:.0f}mm > bed {limit:.0f}mm"
        for axis, ext, limit in zip("XYZ", mesh.extents, bed_mm)
        if ext > limit
    ]
    if oversize:
        result["issues"].append(f"FAIL: exceeds bed: {', '.join(oversize)} — must be split")

    if not mesh.is_watertight:
        result["issues"].append("WARN: not watertight — run a finishing pass before slicing")

    result["verdict"] = (
        "FAIL" if any(i.startswith("FAIL") for i in result["issues"])
        else "WARN" if result["issues"]
        else "PASS"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", type=Path, help="STL/OBJ files to check.")
    parser.add_argument("--bed-mm", nargs=3, type=float, default=[256, 256, 256], metavar=("X", "Y", "Z"))
    parser.add_argument("--overhang-deg", type=float, default=45.0, help="Support threshold angle from vertical.")
    parser.add_argument("--json", type=Path, help="Also write the full report to this path.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any file has a FAIL verdict.")
    args = parser.parse_args()

    reports = [check_mesh(f, tuple(args.bed_mm), args.overhang_deg) for f in args.files]

    for r in reports:
        print(f"\n{r['file']}  [{r['verdict']}]")
        print(f"  watertight={r['watertight']} bodies={r['bodies']} extents={r['extents_mm']} mm")
        print(f"  overhang>{args.overhang_deg:.0f}°: {r['overhang_pct_of_surface']}% of surface "
              f"({r['overhang_area_mm2']} mm²); bed contact {r['bed_contact_mm2']} mm²")
        for issue in r["issues"]:
            print(f"  - {issue}")
        if not r["issues"]:
            print("  no issues found")

    if args.json:
        args.json.write_text(json.dumps(reports, indent=2) + "\n")
        print(f"\nWrote {args.json}", file=sys.stderr)

    if args.strict and any(r["verdict"] == "FAIL" for r in reports):
        sys.exit(1)


if __name__ == "__main__":
    main()
