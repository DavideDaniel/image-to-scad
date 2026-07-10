"""Build a mesh from an editable component plan using Blender.

Usage:
    blender --background --python scripts/blender_build_components.py -- \
        <plan.json> <output.stl> [--blend output.blend] [--obj output.obj] \
        [--render-dir dir] [--parts-dir dir]

Plans use schema component-plan/v0 (single solid) or /v1, which may add an
optional `model.assembly` block that splits the model into separately printable
parts joined by peg/socket pairs:

    "assembly": {
      "parts": [
        {"name": "tray", "components": ["tray_body"], "cuts": ["tray_recess"],
         "rotate_deg": [0, 0, 0]}
      ],
      "joints": [
        {"type": "peg", "name": "post_peg_left", "male": "base", "female": "tray",
         "cylinder": {"radius": 4, "depth": 11, "center": [0, 0, 143], "axis": "z"},
         "clearance": 0.3}
      ]
    }

A joint's cylinder is authored in assembled coordinates and must straddle the
part interface (root a few mm inside the male part). The male part unions the
cylinder as a peg; the female part subtracts it expanded by `clearance`.
With --parts-dir, each part is built, rotated by `rotate_deg`, dropped to Z=0,
and exported as part_<name>.stl (+ render); an assembled preview render is also
produced. The monolithic outputs are still written either way.
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
        "parts_dir": None,
    }
    i = 2
    while i < len(argv):
        if argv[i] == "--blend":
            opts["blend"] = argv[i + 1]
        elif argv[i] == "--obj":
            opts["obj"] = argv[i + 1]
        elif argv[i] == "--render-dir":
            opts["render_dir"] = argv[i + 1]
        elif argv[i] == "--parts-dir":
            opts["parts_dir"] = argv[i + 1]
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


def _make_primitive(spec: dict, kind: str) -> bpy.types.Object:
    if spec["type"] == "box":
        return _cube(spec["name"], spec["size"], spec["center"])
    if spec["type"] == "cylinder":
        return _cylinder(
            spec["name"],
            float(spec["radius"]),
            float(spec["depth"]),
            spec["center"],
            int(spec.get("vertices", 128)),
            str(spec.get("axis", "z")),
        )
    raise SystemExit(f"unsupported {kind} type: {spec['type']}")


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


def _bbox(objs: list[bpy.types.Object]) -> tuple[Vector, Vector, Vector]:
    corners = [obj.matrix_world @ Vector(c) for obj in objs for c in obj.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return lo, hi, (lo + hi) / 2


def _render_views(objs: list[bpy.types.Object], render_dir: str, prefix: str = "") -> None:
    out = Path(render_dir)
    out.mkdir(parents=True, exist_ok=True)

    lo, hi, center = _bbox(objs)
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
        scene.render.filepath = str(out / f"{prefix}{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")

    for leftover in (cam, target, sun):
        bpy.data.objects.remove(leftover, do_unlink=True)


def _joint_cylinder(joint: dict, name: str, grow: float = 0.0) -> bpy.types.Object:
    cyl = joint["cylinder"]
    return _cylinder(
        name,
        float(cyl["radius"]) + grow,
        float(cyl["depth"]) + 2 * grow,
        cyl["center"],
        int(cyl.get("vertices", 96)),
        str(cyl.get("axis", "z")),
    )


def _build_solid(
    material: bpy.types.Material,
    components: list[dict],
    cuts: list[dict],
    joints_male: list[dict],
    joints_female: list[dict],
    bevel: float,
    name: str,
) -> bpy.types.Object:
    objects = [_make_primitive(spec, "component") for spec in components]
    for obj in objects:
        obj.data.materials.append(material)

    combined = objects[0]
    for obj in objects[1:]:
        combined = _boolean_union(combined, obj)

    for joint in joints_male:
        combined = _boolean_union(combined, _joint_cylinder(joint, f"peg_{joint['name']}"))

    for cut in cuts:
        combined = _boolean_difference(combined, _make_primitive(cut, "cut"))

    for joint in joints_female:
        socket = _joint_cylinder(joint, f"socket_{joint['name']}", grow=float(joint.get("clearance", 0.3)))
        combined = _boolean_difference(combined, socket)

    _add_bevel(combined, bevel)
    _repair_mesh(combined)
    combined.name = name
    return combined


def _export(obj: bpy.types.Object, stl_path: str, obj_path: str | None = None) -> None:
    Path(stl_path).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
    print(f"Wrote {stl_path}")
    if obj_path:
        bpy.ops.wm.obj_export(filepath=obj_path, export_selected_objects=True)
        print(f"Wrote {obj_path}")


def _drop_to_bed(obj: bpy.types.Object) -> None:
    lo, _, _ = _bbox([obj])
    obj.location.z -= lo.z
    bpy.context.view_layer.update()


def main() -> None:
    opts = _parse_args()
    plan = json.loads(Path(str(opts["plan"])).read_text())
    model = plan["model"]
    bevel = float(model.get("bevel", 0.0))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    material = bpy.data.materials.new("neutral_gray")
    material.diffuse_color = (0.48, 0.49, 0.47, 1.0)

    # Monolithic build (v0 behavior, always produced).
    combined = _build_solid(
        material,
        model["components"],
        model.get("cuts", []),
        [],
        [],
        bevel,
        model.get("name", "component_model"),
    )
    _drop_to_bed(combined)
    _export(combined, str(opts["stl"]), opts["obj"])

    if opts["blend"]:
        bpy.ops.wm.save_as_mainfile(filepath=str(opts["blend"]))
        print(f"Wrote {opts['blend']}")

    if opts["render_dir"]:
        _render_views([combined], str(opts["render_dir"]))

    assembly = model.get("assembly")
    if opts["parts_dir"] and assembly:
        combined.hide_render = True
        parts_dir = Path(str(opts["parts_dir"]))
        parts_dir.mkdir(parents=True, exist_ok=True)
        by_name = {c["name"]: c for c in model["components"]}
        cuts_by_name = {c["name"]: c for c in model.get("cuts", [])}
        joints = assembly.get("joints", [])

        assembled_preview = []
        for part in assembly["parts"]:
            comp_specs = [by_name[n] for n in part["components"]]
            cut_specs = [cuts_by_name[n] for n in part.get("cuts", [])]
            male = [j for j in joints if j["male"] == part["name"]]
            female = [j for j in joints if j["female"] == part["name"]]
            solid = _build_solid(material, comp_specs, cut_specs, male, female, bevel, f"part_{part['name']}")

            # Keep an assembled-pose copy for the preview render (hidden until then).
            preview = solid.copy()
            preview.data = solid.data.copy()
            preview.hide_render = True
            bpy.context.scene.collection.objects.link(preview)
            assembled_preview.append(preview)

            rot = part.get("rotate_deg", [0, 0, 0])
            if any(rot):
                solid.rotation_euler = tuple(math.radians(a) for a in rot)
                bpy.ops.object.select_all(action="DESELECT")
                solid.select_set(True)
                bpy.context.view_layer.objects.active = solid
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            _drop_to_bed(solid)

            _export(solid, str(parts_dir / f"part_{part['name']}.stl"))
            _render_views([solid], str(parts_dir / "renders"), prefix=f"part_{part['name']}_")
            bpy.data.objects.remove(solid, do_unlink=True)

        for obj in assembled_preview:
            obj.hide_render = False
        _render_views(assembled_preview, str(parts_dir / "renders"), prefix="assembled_")
        for obj in assembled_preview:
            bpy.data.objects.remove(obj, do_unlink=True)


if __name__ == "__main__":
    main()
