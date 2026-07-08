"""Build a mesh from an editable component plan using Blender.

Usage:
    blender --background --python scripts/blender_build_components.py -- \
        <plan.json> <output.stl> [--blend output.blend] [--obj output.obj] [--render-dir dir]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _argv() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _parse_args() -> dict[str, str | None]:
    argv = _argv()
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    opts: dict[str, str | None] = {
        "plan": argv[0],
        "stl": argv[1],
        "blend": None,
        "obj": None,
        "render_dir": None,
    }
    i = 2
    while i < len(argv):
        if argv[i] == "--blend":
            opts["blend"] = argv[i + 1]
        elif argv[i] == "--obj":
            opts["obj"] = argv[i + 1]
        elif argv[i] == "--render-dir":
            opts["render_dir"] = argv[i + 1]
        else:
            raise SystemExit(f"unknown option: {argv[i]}")
        i += 2
    return opts


def _cube(name: str, size: list[float], center: list[float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def _cylinder(
    name: str,
    radius: float,
    depth: float,
    center: list[float],
    vertices: int = 96,
    axis: str = "z",
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=center)
    obj = bpy.context.object
    obj.name = name
    if axis == "x":
        obj.rotation_euler = (0.0, math.radians(90), 0.0)
    elif axis == "y":
        obj.rotation_euler = (math.radians(90), 0.0, 0.0)
    elif axis != "z":
        raise SystemExit(f"unsupported cylinder axis: {axis}")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return obj


def _boolean_union(base: bpy.types.Object, other: bpy.types.Object) -> bpy.types.Object:
    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    modifier = base.modifiers.new(name=f"union_{other.name}", type="BOOLEAN")
    modifier.operation = "UNION"
    modifier.object = other
    try:
        modifier.solver = "EXACT"
    except Exception:
        pass
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(other, do_unlink=True)
    return base


def _boolean_difference(base: bpy.types.Object, cutter: bpy.types.Object) -> bpy.types.Object:
    bpy.context.view_layer.objects.active = base
    base.select_set(True)
    modifier = base.modifiers.new(name=f"cut_{cutter.name}", type="BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter
    try:
        modifier.solver = "EXACT"
    except Exception:
        pass
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return base


def _add_bevel(obj: bpy.types.Object, amount: float) -> None:
    if amount <= 0:
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bevel = obj.modifiers.new(name="small_edge_bevel", type="BEVEL")
    bevel.width = amount
    bevel.segments = 2
    bevel.affect = "EDGES"
    bevel.harden_normals = True
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.object.shade_flat()


def _repair_mesh(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.fill_holes(sides=0)
    bpy.ops.object.mode_set(mode="OBJECT")


def _bbox(obj: bpy.types.Object) -> tuple[Vector, Vector, Vector]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi, (lo + hi) / 2


def _render_views(obj: bpy.types.Object, render_dir: str) -> None:
    out = Path(render_dir)
    out.mkdir(parents=True, exist_ok=True)

    lo, hi, center = _bbox(obj)
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

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 2.5
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(30))
    bpy.context.scene.collection.objects.link(sun)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 850
    try:
        scene.display.shading.light = "STUDIO"
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "BOTH"
        scene.display.shading.color_type = "SINGLE"
        scene.display.shading.single_color = (0.55, 0.56, 0.54)
    except Exception:
        pass

    dist = radius * 2.7
    views = [
        ("front", 0, 8),
        ("right", 90, 8),
        ("top", 0, 88),
        ("threequarter", 45, 24),
    ]
    for name, azimuth, elevation in views:
        az = math.radians(azimuth)
        el = math.radians(elevation)
        cam.location = (
            center.x + dist * math.cos(el) * math.sin(az),
            center.y - dist * math.cos(el) * math.cos(az),
            center.z + dist * math.sin(el),
        )
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")


def main() -> None:
    opts = _parse_args()
    plan = json.loads(Path(str(opts["plan"])).read_text())
    model = plan["model"]

    bpy.ops.wm.read_factory_settings(use_empty=True)

    material = bpy.data.materials.new("neutral_gray")
    material.diffuse_color = (0.48, 0.49, 0.47, 1.0)

    objects = []
    for component in model["components"]:
        if component["type"] == "box":
            obj = _cube(component["name"], component["size"], component["center"])
        elif component["type"] == "cylinder":
            obj = _cylinder(
                component["name"],
                float(component["radius"]),
                float(component["depth"]),
                component["center"],
                int(component.get("vertices", 128)),
                str(component.get("axis", "z")),
            )
        else:
            raise SystemExit(f"unsupported component type: {component['type']}")
        obj.data.materials.append(material)
        objects.append(obj)

    combined = objects[0]
    for obj in objects[1:]:
        combined = _boolean_union(combined, obj)
    combined.name = model.get("name", "component_model")

    for cut in model.get("cuts", []):
        if cut["type"] == "cylinder":
            cutter = _cylinder(
                cut["name"],
                float(cut["radius"]),
                float(cut["depth"]),
                cut["center"],
                int(cut.get("vertices", 128)),
                str(cut.get("axis", "z")),
            )
        elif cut["type"] == "box":
            cutter = _cube(cut["name"], cut["size"], cut["center"])
        else:
            raise SystemExit(f"unsupported cut type: {cut['type']}")
        combined = _boolean_difference(combined, cutter)

    _add_bevel(combined, float(model.get("bevel", 0.0)))
    _repair_mesh(combined)

    # Move the model so the bottom sits on Z=0 after beveling.
    lo, _, _ = _bbox(combined)
    combined.location.z -= lo.z
    bpy.context.view_layer.update()

    stl_path = str(opts["stl"])
    Path(stl_path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    combined.select_set(True)
    bpy.context.view_layer.objects.active = combined
    bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
    print(f"Wrote {stl_path}")

    if opts["obj"]:
        bpy.ops.wm.obj_export(filepath=str(opts["obj"]), export_selected_objects=True)
        print(f"Wrote {opts['obj']}")

    if opts["blend"]:
        bpy.ops.wm.save_as_mainfile(filepath=str(opts["blend"]))
        print(f"Wrote {opts['blend']}")

    if opts["render_dir"]:
        _render_views(combined, str(opts["render_dir"]))


if __name__ == "__main__":
    main()
