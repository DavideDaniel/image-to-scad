"""Finish an AI mesh into a watertight, manifold, real-world-scaled STL using
Blender's OpenVDB voxel remesh as the repair backend.

This is the Blender-backed counterpart to scripts/finish_print.py. It is the
strongest option for meshes that are DETAILED BUT TOPOLOGICALLY BROKEN (e.g.
TRELLIS output: many holes / non-manifold edges / disconnected bodies), where
the trimesh voxel/poisson/meshfix paths either flatten detail or leave gaps.

Pipeline: import -> merge-by-distance -> voxel remesh (guaranteed watertight
manifold) -> optional adaptivity (keeps faces where curvature is high, sheds
them on flat areas) -> optional Laplacian smooth -> optional decimate -> scale
to mm -> report manifold stats -> export STL + OBJ.

Run headless:
    blender --background --python scripts/blender_finish.py -- \
        <input.obj|glb|stl> <output.stl> [--res N] [--adaptivity A] \
        [--smooth-iters K] [--decimate-ratio R] [--target-mm MM]

Defaults are tuned for rescuing a broken-but-detailed mesh while preserving
relief. Lower --res for chunkier/faster, raise it for finer detail.
"""
import sys
import bmesh
import bpy
from mathutils import Vector


def _parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    if len(argv) < 2:
        print("Usage: blender --background --python scripts/blender_finish.py -- "
              "<input> <output.stl> [--res N] [--adaptivity A] [--smooth-iters K] "
              "[--decimate-ratio R] [--target-mm MM]")
        sys.exit(1)
    opts = {
        "input": argv[0],
        "output": argv[1],
        "res": 256,            # voxels along the longest axis
        "adaptivity": 0.0,     # 0 = uniform; up to ~voxel_size sheds flat-area faces
        "smooth_iters": 0,     # Laplacian smooth passes after remesh
        "decimate_ratio": 1.0, # 1.0 = no decimation; e.g. 0.5 = halve face count
        "target_mm": 100.0,    # scale longest axis to this; 0 = leave as-is
    }
    i = 2
    flag_map = {
        "--res": ("res", int),
        "--adaptivity": ("adaptivity", float),
        "--smooth-iters": ("smooth_iters", int),
        "--decimate-ratio": ("decimate_ratio", float),
        "--target-mm": ("target_mm", float),
    }
    while i < len(argv):
        key, cast = flag_map[argv[i]]
        opts[key] = cast(argv[i + 1])
        i += 2
    return opts


def _import(path):
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext in ("glb", "gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.wm.stl_import(filepath=path)
    return [o for o in bpy.context.selected_objects if o.type == "MESH"][0]


def _diag(obj, label):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nonmanifold = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    nv, nf = len(bm.verts), len(bm.faces)
    bm.free()
    watertight = boundary == 0 and nonmanifold == 0
    print(f"  {label:<9} verts={nv:,} faces={nf:,} watertight={watertight} "
          f"boundary_edges={boundary:,} nonmanifold_edges={nonmanifold:,}")
    return watertight


def _longest_axis_mm(obj):
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    dims = [max(v[i] for v in bb) - min(v[i] for v in bb) for i in range(3)]
    return max(dims), dims


def main():
    o = _parse_args()
    print(f"Loading: {o['input']}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = _import(o["input"])
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    _diag(obj, "raw:")

    # weld coincident verts so the voxelizer sees a single coherent surface
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.object.mode_set(mode="OBJECT")

    # --- OpenVDB voxel remesh: the watertight-manifold guarantee ---
    longest, _ = _longest_axis_mm(obj)
    voxel = longest / o["res"]
    me = obj.data
    me.remesh_voxel_size = voxel
    me.remesh_voxel_adaptivity = o["adaptivity"]
    me.use_remesh_fix_poles = True
    bpy.ops.object.voxel_remesh()
    print(f"  voxel:    size={voxel:.4f} (res={o['res']} along longest axis) "
          f"adaptivity={o['adaptivity']}")
    _diag(obj, "remeshed:")

    # close any residual boundary holes the remesh left (usually a handful of
    # tiny gaps at thin features) so the result is fully watertight
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.fill_holes(sides=0)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # --- optional Laplacian smooth (volume-preserving) ---
    if o["smooth_iters"] > 0:
        m = obj.modifiers.new(name="Smooth", type="LAPLACIANSMOOTH")
        m.iterations = o["smooth_iters"]
        m.lambda_factor = 1.0
        m.lambda_border = 1.0
        m.use_volume_preserve = True
        m.use_normalized = True
        bpy.ops.object.modifier_apply(modifier=m.name)
        print(f"  smooth:   {o['smooth_iters']} Laplacian iters (volume-preserving)")

    # --- optional decimate to drop the remesh's polycount ---
    if o["decimate_ratio"] < 1.0:
        m = obj.modifiers.new(name="Decimate", type="DECIMATE")
        m.decimate_type = "COLLAPSE"
        m.ratio = o["decimate_ratio"]
        bpy.ops.object.modifier_apply(modifier=m.name)
        print(f"  decimate: ratio={o['decimate_ratio']}")
        _diag(obj, "decimated:")

    # --- scale longest axis to target mm ---
    if o["target_mm"] and o["target_mm"] > 0:
        longest, _ = _longest_axis_mm(obj)
        s = o["target_mm"] / longest
        obj.scale = (s, s, s)
        bpy.ops.object.transform_apply(scale=True)
        _, dims = _longest_axis_mm(obj)
        print(f"  scaled:   longest axis -> {o['target_mm']} mm "
              f"(size = {tuple(round(d, 2) for d in dims)} mm)")

    watertight = _diag(obj, "final:")

    # --- export ---
    out = o["output"]
    stl = out if out.lower().endswith(".stl") else out + ".stl"
    obj_out = stl[:-4] + ".obj"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=stl, export_selected_objects=True)
    bpy.ops.wm.obj_export(filepath=obj_out, export_selected_objects=True)
    print(f"\nPRINT-READY={'YES' if watertight else 'NO (check above)'}")
    print(f"Wrote: {stl}")
    print(f"Wrote: {obj_out}")
    print("DONE")


if __name__ == "__main__":
    main()
