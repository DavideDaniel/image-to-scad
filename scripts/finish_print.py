"""Turn a raw AI-generated mesh (e.g. TRELLIS output) into a watertight,
manifold, real-world-scaled STL ready for slicing.

Two repair methods:
  --method voxel    (default) Voxelize at high resolution, morphologically seal
                    holes, fill interior, marching-cubes back to a guaranteed
                    watertight manifold. Robust on messy meshes and preserves
                    features down to the voxel size. Slightly rounds sharp edges.
  --method meshfix  PyMeshFix (MeshFix algorithm). Faster, but can flatten fine
                    surface detail on noisy AI meshes.

Pipeline: load -> drop tiny components -> repair -> scale to mm -> verify -> STL.
"""
import argparse
from pathlib import Path

import numpy as np
import trimesh


def _diag(mesh: trimesh.Trimesh) -> str:
    e = mesh.edges_sorted
    _, c = np.unique(e, axis=0, return_counts=True)
    return (
        f"verts={len(mesh.vertices):,} faces={len(mesh.faces):,} "
        f"watertight={mesh.is_watertight} bodies={mesh.body_count} "
        f"boundary_edges={int((c == 1).sum()):,} nonmanifold_edges={int((c > 2).sum()):,}"
    )


def _drop_tiny(mesh, frac):
    comps = mesh.split(only_watertight=False)
    if len(comps) <= 1:
        return mesh
    sizes = np.array([len(c.faces) for c in comps])
    kept = [c for c, k in zip(comps, sizes >= sizes.max() * frac) if k]
    print(f"  components: {len(comps)} -> kept {len(kept)} "
          f"(dropped {len(comps) - len(kept)} fragments)")
    return trimesh.util.concatenate(kept)


def _repair_voxel(mesh, res, close_iter):
    """Voxel remesh: surface voxelize -> close -> fill -> marching cubes."""
    import scipy.ndimage as ndi
    from skimage import measure

    pitch = float(mesh.extents.max()) / res
    vox = mesh.voxelized(pitch=pitch)
    mat = np.asarray(vox.matrix, dtype=bool)
    # seal small gaps from open boundaries, then flood-fill the interior
    if close_iter > 0:
        mat = ndi.binary_closing(mat, iterations=close_iter)
    mat = ndi.binary_fill_holes(mat)
    # pad so marching cubes closes faces touching the volume border
    mat = np.pad(mat, 1, mode="constant", constant_values=False)
    verts, faces, _, _ = measure.marching_cubes(mat.astype(np.float32), level=0.5)
    verts = (verts - 1) * pitch  # undo pad, back to model units
    out = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    trimesh.repair.fix_normals(out)
    print(f"  voxel: pitch={pitch:.3f} grid={tuple(vox.matrix.shape)} close_iter={close_iter}")
    return out


def _repair_poisson(mesh, depth, density_quantile):
    """Screened Poisson reconstruction: fit a smooth watertight surface to the
    mesh's geometry. Patches holes and removes non-manifold edges while keeping
    surfaces smooth (unlike voxel remesh). Slightly rounds sharp edges."""
    import open3d as o3d

    m = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(np.asarray(mesh.vertices)),
        o3d.utility.Vector3iVector(np.asarray(mesh.faces)),
    )
    # Sample a dense point cloud and compute globally-consistent normals from
    # the point geometry (the source winding is inconsistent, so we ignore it).
    n_pts = max(400_000, len(mesh.vertices))
    pcd = m.sample_points_uniformly(number_of_points=n_pts)
    diag = float(np.linalg.norm(mesh.extents))
    pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=diag * 0.01, max_nn=30))
    pcd.orient_normals_consistent_tangent_plane(30)

    rec, dens = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=depth, linear_fit=True
    )
    dens = np.asarray(dens)
    # Poisson balloons past the data; drop the lowest-confidence vertices and
    # crop back to the input's bounding box.
    rec.remove_vertices_by_mask(dens < np.quantile(dens, density_quantile))
    rec = rec.crop(m.get_axis_aligned_bounding_box())
    for fn in ("remove_degenerate_triangles", "remove_duplicated_triangles",
               "remove_duplicated_vertices", "remove_non_manifold_edges"):
        getattr(rec, fn)()
    out = trimesh.Trimesh(np.asarray(rec.vertices), np.asarray(rec.triangles), process=True)
    trimesh.repair.fix_normals(out)
    print(f"  poisson: depth={depth} pts={n_pts:,} density_q={density_quantile}")
    return out


def _repair_gentle(mesh):
    """Minimal, non-destructive repair for already-clean meshes (e.g. Hunyuan
    SDF output): merge/dedupe, drop the few faces causing non-manifold edges,
    fill the tiny holes that leaves, fix normals. Preserves all surface detail."""
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()

    for _ in range(3):
        e = mesh.edges_sorted
        eu, c = np.unique(e, axis=0, return_counts=True)
        bad = eu[c > 2]
        if len(bad) == 0:
            break
        drop = set()
        for v0, v1 in bad:
            fi = np.where(np.any(mesh.faces == v0, axis=1) & np.any(mesh.faces == v1, axis=1))[0]
            drop.update(int(i) for i in fi[2:])  # keep first two faces on the edge
        if not drop:
            break
        keep = np.ones(len(mesh.faces), bool)
        keep[list(drop)] = False
        mesh.update_faces(keep)
        mesh.remove_unreferenced_vertices()
        trimesh.repair.fill_holes(mesh)

    # Close any residual boundary holes (trimesh.fill_holes only handles simple
    # ones). Prefer pymeshlab's robust hole-closer when available.
    if not mesh.is_watertight:
        try:
            import pymeshlab
            ms = pymeshlab.MeshSet()
            ms.add_mesh(pymeshlab.Mesh(np.asarray(mesh.vertices), np.asarray(mesh.faces)))
            ms.meshing_repair_non_manifold_edges()
            ms.meshing_close_holes(maxholesize=300)
            m = ms.current_mesh()
            mesh = trimesh.Trimesh(m.vertex_matrix(), m.face_matrix(), process=True)
        except Exception as e:
            print(f"  (pymeshlab close-holes unavailable: {e}); trimesh fill only")
            for _ in range(3):
                if mesh.is_watertight:
                    break
                trimesh.repair.fill_holes(mesh)

    trimesh.repair.fix_normals(mesh)
    return mesh


def _repair_meshfix(mesh):
    import pymeshfix
    mf = pymeshfix.MeshFix(mesh.vertices, mesh.faces)
    mf.repair(joincomp=True, remove_smallest_components=True)
    out = trimesh.Trimesh(vertices=mf.points, faces=mf.faces, process=True)
    trimesh.repair.fix_normals(out)
    return out


def _base_cut(mesh, face, mm):
    """Slice `mm` off one face and cap the cut — gives a flat print-bed seating
    surface and lops off thin tendrils that hang below that plane. `face` is one
    of x-,x+,y-,y+,z-,z+ (the face that rests on the print bed), or 'auto' = the
    flat 'back' slab of a relief/nameplate (thinnest axis, most outward flat area)."""
    if face == "auto":
        # Thinnest axis = depth (letters vs back). The print-bed "back" is the
        # FLATTER side: its outward-facing surface sits at a more consistent
        # depth than the relief/letter side. Pick the side whose outward faces
        # have the lower depth spread.
        axis = int(np.argmin(mesh.extents))
        fc = mesh.triangles_center[:, axis]
        fn = mesh.face_normals[:, axis]

        def spread(mask):
            pos = fc[mask]
            return float(pos.std()) if len(pos) > 10 else np.inf
        lo_spread = spread(fn < -0.7)   # faces pointing -axis (the -side surface)
        hi_spread = spread(fn > 0.7)    # faces pointing +axis (the +side surface)
        sign = "-" if lo_spread <= hi_spread else "+"
        face = "xyz"[axis] + sign
    axis = {"x": 0, "y": 1, "z": 2}[face[0]]
    sign = face[1]
    normal = np.zeros(3)
    if sign == "-":
        normal[axis] = 1.0          # keep the +axis side
        origin = mesh.bounds[0].copy(); origin[axis] += mm
    else:
        normal[axis] = -1.0         # keep the -axis side
        origin = mesh.bounds[1].copy(); origin[axis] -= mm
    cut = mesh.slice_plane(origin, normal, cap=True)
    print(f"  base-cut: sliced {mm} mm off {face} face")
    return cut


def finish(input_path, output_path, target_mm, min_component_frac, method, res, close_iter,
           poisson_depth=10, density_quantile=0.03, base_cut="none", base_cut_mm=1.0):
    print(f"Loading: {input_path}")
    mesh = trimesh.load(input_path, force="mesh")
    print(f"  raw:      {_diag(mesh)}")

    mesh = _drop_tiny(mesh, min_component_frac)
    print(f"  cleaned:  {_diag(mesh)}")

    if method == "voxel":
        mesh = _repair_voxel(mesh, res, close_iter)
    elif method == "poisson":
        mesh = _repair_poisson(mesh, poisson_depth, density_quantile)
    elif method == "gentle":
        mesh = _repair_gentle(mesh)
    else:
        mesh = _repair_meshfix(mesh)
    print(f"  repaired: {_diag(mesh)}")

    # Drop any stray bodies the repair introduced (each is independently
    # watertight after voxel remesh, so keeping the largest stays watertight).
    if mesh.body_count > 1:
        mesh = max(mesh.split(only_watertight=False), key=lambda c: len(c.faces))
        print(f"  largest body: {_diag(mesh)}")

    if target_mm and target_mm > 0:
        mesh.apply_scale(target_mm / float(mesh.extents.max()))
        print(f"  scaled:   longest axis -> {target_mm} mm (size = {np.round(mesh.extents, 2)} mm)")

    if base_cut and base_cut != "none":
        mesh = _base_cut(mesh, base_cut, base_cut_mm)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    stl_path = out.with_suffix(".stl")
    mesh.export(stl_path)
    mesh.export(out.with_suffix(".obj"))

    ok = mesh.is_watertight and mesh.is_winding_consistent
    print(f"\nFinal: {_diag(mesh)}")
    print(f"volume={mesh.volume:.1f} mm^3  PRINT-READY={'YES' if ok else 'NO (check above)'}")
    print(f"Wrote: {stl_path}")
    return ok


def main():
    p = argparse.ArgumentParser(description="Finish an AI mesh into a print-ready STL")
    p.add_argument("input", help="Input mesh (OBJ/GLB/PLY/STL)")
    p.add_argument("-o", "--output", required=True, help="Output path (.stl)")
    p.add_argument("--target-mm", type=float, default=100.0,
                   help="Scale longest axis to this many mm (default: 100; 0 = none)")
    p.add_argument("--min-component-frac", type=float, default=0.02,
                   help="Drop components smaller than this fraction of the largest (default: 0.02)")
    p.add_argument("--method", choices=["gentle", "poisson", "voxel", "meshfix"], default="gentle",
                   help="Repair method (default: gentle = non-destructive, for clean SDF meshes)")
    p.add_argument("--res", type=int, default=400,
                   help="[voxel] resolution along longest axis (default: 400)")
    p.add_argument("--close-iter", type=int, default=2,
                   help="[voxel] morphological close iterations (default: 2)")
    p.add_argument("--poisson-depth", type=int, default=10,
                   help="[poisson] octree depth; higher = more detail (default: 10)")
    p.add_argument("--density-quantile", type=float, default=0.03,
                   help="[poisson] trim this fraction of lowest-confidence verts (default: 0.03)")
    p.add_argument("--base-cut", choices=["none", "auto", "x-", "x+", "y-", "y+", "z-", "z+"],
                   default="none",
                   help="Slice a sliver off one face to form a flat print base (also trims "
                        "tendrils below it). 'auto' = the flat 'back' of a relief/nameplate "
                        "(default: none)")
    p.add_argument("--base-cut-mm", type=float, default=1.0,
                   help="How much to slice off the --base-cut face, in mm (default: 1.0)")
    args = p.parse_args()
    ok = finish(args.input, args.output, args.target_mm, args.min_component_frac,
                args.method, args.res, args.close_iter,
                args.poisson_depth, args.density_quantile, args.base_cut, args.base_cut_mm)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
