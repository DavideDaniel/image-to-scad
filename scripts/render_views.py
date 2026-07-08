"""Headless Blender render of a mesh from several angles, for visual QA.

Usage:
    blender --background --python scripts/render_views.py -- <mesh> <out_dir> [n_side]
Renders front / right / three-quarter / back / bottom views as PNGs so you can
confirm geometry (e.g. hollows, cutouts) survived the repair pipeline.
"""
import sys
import math
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
mesh_path = argv[0]
out_dir = argv[1].rstrip("/")
res = int(argv[2]) if len(argv) > 2 else 900

# --- clean scene ---
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- import mesh by extension (handle Blender version differences) ---
ext = mesh_path.lower().rsplit(".", 1)[-1]
if ext == "obj":
    try:
        bpy.ops.wm.obj_import(filepath=mesh_path)
    except Exception:
        bpy.ops.import_scene.obj(filepath=mesh_path)
elif ext == "glb" or ext == "gltf":
    bpy.ops.import_scene.gltf(filepath=mesh_path)
else:
    try:
        bpy.ops.wm.stl_import(filepath=mesh_path)
    except Exception:
        bpy.ops.import_mesh.stl(filepath=mesh_path)
obj = [o for o in bpy.context.selected_objects if o.type == "MESH"][0]

# center at origin, record size
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
obj.location = (0, 0, 0)
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
lo = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
hi = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
# Aim at the mean of the geometry (center of mass), not the bbox center, so
# hollow objects (whose bbox center sits in empty space) stay framed.
verts_w = [obj.matrix_world @ v.co for v in obj.data.vertices]
center = sum(verts_w, Vector((0, 0, 0))) / len(verts_w)
radius = max((hi - lo).length / 2, 1e-4)

# smooth shading so form reads clearly
bpy.ops.object.shade_smooth()

# --- camera with track-to constraint aimed at object center ---
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
target = bpy.data.objects.new("Target", None)
target.location = center
bpy.context.scene.collection.objects.link(target)
con = cam.constraints.new(type="TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"

# --- light: a sun, plus workbench cavity for depth cues ---
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(30))
bpy.context.scene.collection.objects.link(sun)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
try:
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.color_type = "SINGLE"
    shading.single_color = (0.8, 0.8, 0.82)
except Exception:
    pass
scene.render.resolution_x = res
scene.render.resolution_y = res
scene.render.film_transparent = False

dist = radius * 2.5

# (name, azimuth_deg, elevation_deg)
views = [
    ("1_threequarter", 45, 25),
    ("2_top", 0, 88),        # top-down to read surface features (e.g. recesses)
    ("3_front", 0, 10),
    ("4_right", 90, 10),
    ("5_bottom", 25, -55),   # look up from below to check the hollow/bridge
]

for name, az, el in views:
    a, e = math.radians(az), math.radians(el)
    cam.location = (
        center.x + dist * math.cos(e) * math.sin(a),
        center.y - dist * math.cos(e) * math.cos(a),
        center.z + dist * math.sin(e),
    )
    scene.render.filepath = f"{out_dir}/view_{name}.png"
    bpy.ops.render.render(write_still=True)
    print(f"rendered {scene.render.filepath}")

print("DONE")
