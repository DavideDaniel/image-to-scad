---
name: component-model
description: Build a parametric, printable 3D model (STL) of a rectilinear object from reference photos by authoring a component-plan JSON and iterating with visual feedback — no per-object code. Use when the user wants to turn photos/images of a boxy or functional object (stand, shelf, bracket, dock, organizer, holder) into an editable 3D model or STL, or asks to "model this from photos", "make a printable version of this", or to tweak dimensions of a previously component-modeled object. ALSO use when a model has printability problems (floating parts, heavy overhangs, cantilevers, exceeds the bed), when the user asks to split a model into printable components that assemble, or to "componentize" an existing plan or idea — converting a v0 plan to a v1 assembly (regrouping components into parts, splitting oversized components into halves at a joint, reassigning cuts, choosing per-part print orientations) is plan editing, not code; check_printability.py supplies the evidence. NOT for organic/curvy subjects (figures, animals, sculpted shapes) — route those to the AI-mesh path (Hunyuan3D/TRELLIS + scripts/blender_finish.py).
---

# Component model from images

Turn reference photos of a **rectilinear object** into a watertight, parametric STL.
The core idea: images supply *measurements and design intent only*; the geometry is a
hand-editable JSON plan of primitives built deterministically in Blender. You (Claude)
are the plan author — no per-object Python is ever written.

## Pipeline

```
photos -> measure proportions -> author plan.json -> build STL + renders
              ^                                            |
              +--------- visually compare, edit JSON ------+
```

Two generic scripts do all the work (repo root = this project):

```bash
# 1. Measure silhouettes (labels front/right/top unlock mm estimates)
venv/bin/python scripts/measure_views.py front=f.png right=r.png top=t.png \
    --width-mm <real width> --output plan_dir/measurements.json

# 2. Build plan -> STL/OBJ/blend + 4 renders (front, right, top, threequarter)
blender --background --python scripts/blender_build_components.py -- \
    plan_dir/plan.json plan_dir/model.stl --obj plan_dir/model.obj \
    --blend plan_dir/model.blend --render-dir plan_dir/renders
```

## The loop

1. **Route.** Is the object decomposable into axis-aligned boxes and cylinders?
   Yes -> continue. No (organic, sculpted, freeform-curved) -> use the AI-mesh path
   (`scripts/blender_finish.py` on Hunyuan3D/TRELLIS output) instead; say so and stop.
2. **Anchor scale.** Ask the user for ONE real dimension (usually overall width in mm)
   if not provided. Everything else is derived by proportion.
3. **Measure.** Run `measure_views.py` on whatever labeled views exist. It needs
   dark-object-on-light-background images; pass `--threshold` if segmentation fails.
   Fewer views = more guessing; front + top (or front + right) is the useful minimum.
4. **Decompose by looking.** Study the photos and name the parts like a woodworker
   would ("top slab", "left leg", "back wall", "cable hole"). Convert the measured
   proportions into per-part mm sizes. Write the plan JSON (schema below).
5. **Build** with the Blender command above.
6. **Compare.** Read the produced renders next to the source photos, view by view.
   Look for: missing parts, wrong proportions, features in the wrong place, missing
   holes/recesses. Fix by editing numbers in the JSON — never by writing code — and
   rebuild. Two or three rounds is typical.
7. **Verify printability**:
   ```bash
   venv/bin/python -c "import trimesh; m=trimesh.load('plan_dir/model.stl'); \
   print('watertight:', m.is_watertight, '| bodies:', m.body_count, '| extents:', m.extents)"
   ```
   If not watertight (Blender boolean slivers), run the finishing pass:
   `blender --background --python scripts/blender_finish.py -- model.stl model_printready.stl --res 384`
8. **Functional features on request**: mug wells, sockets + `scripts/blender_build_link_clip.py`
   connector clips, stacking feet/pockets — all are just more components/cuts in the plan.
   For fit between parts use 0.25–0.35 mm clearance per side.
9. **Split into printable parts when the checker says so.** Run
   `venv/bin/python scripts/check_printability.py model.stl` — it flags floating
   bodies, overhang % beyond 45°, tip-over risk, and bed overflow. On FAIL/WARN,
   add an `assembly` block (schema v1, below) instead of accepting supports. Decide
   the split like a product designer, not mechanically:
   - **Split at natural interfaces** (where distinct named components already meet),
     never through the middle of a component.
   - Each part must print well alone: pick `rotate_deg` so its largest flat face is
     down and its own overhang ≈ 0. Re-run the checker on every part STL.
   - **Joints**: peg/socket cylinders authored in assembled coordinates, straddling
     the interface — root ≥3 mm inside the male part, enter ≥5 mm into the female,
     leave ≥3 mm of wall around the socket. Radius ≈ 40–55% of the smaller mating
     dimension. Clearance 0.3 mm (snug) to 0.35 (easy). Use ≥2 pegs per interface
     to lock rotation unless the assembly is indexed anyway.
   - Build with `--parts-dir out/parts`: per-part STLs + renders plus an
     `assembled_*` preview render — read it to confirm the parts register correctly.
10. **Bed fit and post-print fit belong to the `print-fit` skill.** Never rescale
    STLs in the slicer for a model with an assembly — clearances are absolute;
    `scripts/scale_plan.py` rescales the plan keeping tolerances fixed, and the
    print-fit skill covers the design-rule re-review and clearance calibration.

## Plan schema (component-plan/v0; /v1 adds `assembly`)

```json
{
  "schema": "component-plan/v0",
  "units": "mm",
  "model": {
    "name": "my_object",
    "bevel": 0.8,
    "components": [
      {"name": "base", "type": "box", "size": [80, 60, 12], "center": [0, 0, 6]},
      {"name": "post", "type": "cylinder", "radius": 6, "depth": 40,
       "center": [0, 0, 32], "axis": "z", "vertices": 128}
    ],
    "cuts": [
      {"name": "cable_hole", "type": "cylinder", "radius": 5, "depth": 30,
       "center": [0, -20, 6], "axis": "y"}
    ]
  }
}
```

Schema v1 may add `model.assembly` for split-for-print (built with `--parts-dir`):

```json
"assembly": {
  "parts": [
    {"name": "base", "components": ["base_disc", "post_left"], "cuts": [], "rotate_deg": [0, 0, 0]},
    {"name": "tray", "components": ["tray_body"], "cuts": ["tray_recess"]}
  ],
  "joints": [
    {"type": "peg", "name": "peg_left", "male": "base", "female": "tray", "clearance": 0.3,
     "cylinder": {"radius": 4, "depth": 12, "center": [-108, 0, 143], "axis": "z"}}
  ]
}
```

Each part = union of its `components` minus its `cuts`; the male part unions each
joint cylinder as a peg, the female part subtracts it grown by `clearance`. Parts are
rotated by `rotate_deg`, dropped to Z=0, and exported as `part_<name>.stl` with
per-part renders plus an assembled preview. The monolithic STL is still produced.
Worked example: `outputs/circular_shelf_poc/plan.json` (19.8% overhang as one piece
→ two parts at ~0%).

- `size` is full extent `[X, Y, Z]`; `center` is the solid's centroid. Boxes are
  axis-aligned; cylinders point along `axis` (`"x"|"y"|"z"`, default `"z"`).
- All `components` are unioned in order, then every entry in `cuts` is subtracted.
- `bevel` (mm) is applied to all edges at the end; keep it under ~1% of the smallest
  overall dimension. The final solid is auto-shifted so its bottom sits at Z=0.
- Extra keys (e.g. a `source_images` or `measurements` block) are ignored by the
  builder — include them; they document where numbers came from.

## Hard-won rules

- **Overlap, never kiss.** Touching components must interpenetrate by ≥0.4 mm;
  coplanar faces make Blender's EXACT boolean produce slivers and non-manifold edges.
  Same for cuts: cutters must poke ≥1 mm past the faces they pierce.
- **Convention:** X = width (front view horizontal), Y = depth (front view into the
  screen), Z = height. Front photo maps to XZ, top photo to XY, right photo to YZ.
- The raw STL can come out slicer-tolerable-but-not-watertight on Blender 5.x even
  with clean input (a handful of boundary edges). Don't chase it in the plan — the
  `blender_finish.py` voxel pass (step 7) guarantees watertight.
- Depth estimated from a top photo beats depth from a side photo (foreshortening);
  when both exist `measure_views.py` already blends them 0.8/0.2.
- Photos with perspective inflate the nearer dimension a few percent. If the user can
  give two real dimensions, trust those over silhouette ratios.
- Keep cylinder `vertices` at 96–128; more just bloats the boolean.

## Worked example

`examples/sample_images/stand_multiview/` + `outputs/component_mug_shelf_stackable_poc/stand_plan.json`
is a complete real case: a 12-component mug shelf with wells, side sockets, and
stacking feet, authored from three photos. Read that plan when unsure how to
structure a decomposition. (`scripts/component_plan_from_stand_images.py` is the
legacy hardcoded author for that one object class — do not extend it; author JSON
directly instead.)
