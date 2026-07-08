"""Render a two-module stack preview from a shelf STL.

Usage:
    blender --background --python scripts/blender_preview_stack.py -- \
        <shelf.stl> <out_dir> [--peg-depth-mm 9] [--height-mm 128]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _argv() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _parse_args() -> dict[str, float | str]:
    argv = _argv()
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    opts: dict[str, float | str] = {
        "mesh": argv[0],
        "out_dir": argv[1],
        "peg_depth_mm": 9.0,
        "height_mm": 0.0,
    }
    flag_map = {"--peg-depth-mm": "peg_depth_mm", "--height-mm": "height_mm"}
    i = 2
    while i < len(argv):
        if argv[i] not in flag_map:
            raise SystemExit(f"unknown option: {argv[i]}")
        opts[flag_map[argv[i]]] = float(argv[i + 1])
        i += 2
    return opts


def _import_stl(path: str) -> bpy.types.Object:
    try:
        bpy.ops.wm.stl_import(filepath=path)
    except Exception:
        bpy.ops.import_mesh.stl(filepath=path)
    obj = [o for o in bpy.context.selected_objects if o.type == "MESH"][0]
    return obj


def _bbox(objects: list[bpy.types.Object]) -> tuple[Vector, Vector, Vector]:
    corners = []
    for obj in objects:
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi, (lo + hi) / 2


def main() -> None:
    opts = _parse_args()
    out_dir = Path(str(opts["out_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    lower = _import_stl(str(opts["mesh"]))
    lower.name = "lower_module"

    upper = lower.copy()
    upper.data = lower.data.copy()
    upper.name = "upper_module"
    bpy.context.scene.collection.objects.link(upper)

    lower_mat = bpy.data.materials.new("lower_gray")
    lower_mat.diffuse_color = (0.45, 0.47, 0.47, 1)
    upper_mat = bpy.data.materials.new("upper_blue_gray")
    upper_mat.diffuse_color = (0.58, 0.65, 0.68, 1)
    lower.data.materials.append(lower_mat)
    upper.data.materials.append(upper_mat)

    lo, hi, _ = _bbox([lower])
    height = float(opts["height_mm"]) or (hi.z - lo.z)
    # Approximate shoulder-on-pad placement: bottom pegs enter the lower sockets,
    # while the upper module body rests on the lower top pads.
    upper.location.z = height - float(opts["peg_depth_mm"])
    bpy.context.view_layer.update()

    lo, hi, center = _bbox([lower, upper])
    radius = max((hi - lo).length / 2, 1.0)

    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    target = bpy.data.objects.new("Target", None)
    target.location = center
    bpy.context.scene.collection.objects.link(target)
    constraint = cam.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    light_data = bpy.data.lights.new("Sun", type="SUN")
    light_data.energy = 2.5
    light = bpy.data.objects.new("Sun", light_data)
    light.rotation_euler = (math.radians(50), math.radians(20), math.radians(30))
    bpy.context.scene.collection.objects.link(light)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1300
    scene.render.resolution_y = 1000
    try:
        scene.display.shading.light = "STUDIO"
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "BOTH"
        scene.display.shading.color_type = "MATERIAL"
    except Exception:
        pass

    dist = radius * 2.8
    views = [("stack_threequarter", 38, 20), ("stack_front", 0, 8), ("stack_side", 90, 8)]
    for name, azimuth, elevation in views:
        az = math.radians(azimuth)
        el = math.radians(elevation)
        cam.location = (
            center.x + dist * math.cos(el) * math.sin(az),
            center.y - dist * math.cos(el) * math.cos(az),
            center.z + dist * math.sin(el),
        )
        scene.render.filepath = str(out_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")

    bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / "stack_preview.blend"))
    print(f"Wrote {out_dir / 'stack_preview.blend'}")


if __name__ == "__main__":
    main()
