# Component-model workflow: photos → parametric STL

Turn reference photos of a rectilinear or rotational object (stand, shelf, dock,
organizer) into a watertight, parametric STL — without writing any per-object code.

The idea: **images supply measurements and design intent only; the geometry is a
hand-editable JSON plan of primitives** built deterministically in Blender. The JSON
is the model. Editing a dimension means editing a number and rebuilding.

This works with nothing but the two generic scripts below and a text editor. (There
is also a Claude Code skill, `.claude/skills/component-model/SKILL.md`, which is this
same workflow with the plan-authoring step done by the AI — the mechanism is
identical.)

## Requirements

- Blender 4/5 on PATH (`brew install blender`)
- The project venv: `python -m venv venv && venv/bin/pip install pillow opencv-python numpy trimesh`

## The loop

```
photos -> measure proportions -> write plan.json -> build STL + renders
              ^                                           |
              +------- compare renders to photos ---------+
```

### 1. Get views

Ideal input: front, right, and top photos of the object on a light background
(orthographic-ish, minimal perspective). A single front view is enough for
rotationally symmetric objects. If you have one grid image with multiple views,
split it first:

```bash
venv/bin/python scripts/split_views.py sheet.png --out-dir views --grid 2x2
```

### 2. Measure

```bash
venv/bin/python scripts/measure_views.py \
    front=views/front.png right=views/right.png top=views/top.png \
    --width-mm 250 --output measurements.json
```

Labels are free-form, but `front`/`right`/`top` unlock mm estimates. `--width-mm`
anchors the scale with one real dimension; everything else is derived by silhouette
proportion. Segmentation uses the alpha channel when present, else assumes a dark
object on a light background (`--threshold` to adjust).

### 3. Write the plan

Create `plan.json` (schema `component-plan/v0`):

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

Rules:

- `size` is full extent `[X, Y, Z]`; `center` is the solid's centroid.
- Axes: X = width, Y = depth, Z = height. Front photo maps to XZ, top to XY,
  right to YZ. Boxes are axis-aligned; cylinders point along `axis` (default `z`).
- `components` are unioned in order, then each entry in `cuts` is subtracted.
- `bevel` (mm) rounds all edges at the end; keep under ~1% of the smallest overall
  dimension. The result is auto-shifted so its bottom sits at Z=0.
- Extra documentation keys (`source_images`, `measurements`, notes) are ignored by
  the builder — include them liberally.
- Decompose like a woodworker: name the parts ("top slab", "left leg", "rim lip"),
  size each from the measured proportions.

### 4. Build

```bash
blender --background --python scripts/blender_build_components.py -- \
    plan.json model.stl --obj model.obj --blend model.blend --render-dir renders
```

Produces the STL/OBJ/.blend plus four renders (front, right, top, threequarter).

### 5. Compare and iterate

Put `renders/front.png` next to your front photo (repeat per view). Look for missing
parts, wrong proportions, misplaced features. Fix numbers in `plan.json`, rebuild.
Two or three rounds is typical.

### 6. Verify printability

```bash
venv/bin/python -c "import trimesh; m = trimesh.load('model.stl'); \
print('watertight:', m.is_watertight, '| bodies:', m.body_count, '| extents:', m.extents)"
```

If it is not watertight (Blender 5.x booleans occasionally leave a few boundary
edges even with clean input), run the voxel-remesh finishing pass, which guarantees
a watertight manifold:

```bash
blender --background --python scripts/blender_finish.py -- \
    model.stl model_printready.stl --res 384
```

For a fuller report — floating bodies, overhang area beyond 45°, bed-contact /
tip-over risk, bed fit:

```bash
venv/bin/python scripts/check_printability.py model.stl [--bed-mm 256 256 256]
```

### 7. Split into printable parts (schema v1 `assembly`)

When the checker warns (heavy overhangs, floating pieces, doesn't fit the bed),
split the model into separately printed parts that assemble with printed peg/socket
joints, instead of accepting supports. Add an `assembly` block to the plan:

```json
"assembly": {
  "parts": [
    {"name": "base", "components": ["base_disc", "post_left", "post_right"]},
    {"name": "tray", "components": ["tray_body"], "cuts": ["tray_recess"],
     "rotate_deg": [0, 0, 0]}
  ],
  "joints": [
    {"type": "peg", "name": "peg_left", "male": "base", "female": "tray", "clearance": 0.3,
     "cylinder": {"radius": 4, "depth": 12, "center": [-108, 0, 143], "axis": "z"}}
  ]
}
```

- Each part is the union of its `components` minus its `cuts`. The `male` part
  unions each joint cylinder as a peg; the `female` part subtracts it grown by
  `clearance` (0.3 mm snug, 0.35 mm easy).
- Joint cylinders are authored in **assembled coordinates** and must straddle the
  interface: root ≥3 mm inside the male part, reach ≥5 mm into the female, with
  ≥3 mm of wall left around the socket. Two or more pegs per interface prevent
  rotation.
- Split at natural component boundaries; pick each part's `rotate_deg` so its
  largest flat face prints down.
- Build with `--parts-dir out/parts`: exports `part_<name>.stl` per part (rotated,
  dropped to the bed) plus per-part renders and an `assembled_*` preview render.
  Re-run the checker on every part.

Worked example: `outputs/circular_shelf_poc/plan.json` — as one piece the shelf has
19.8% of its surface in >45° overhang (the tray hanging over the posts); split into
`base` (posts up, pegs on top) and `tray` (flat, sockets underneath) both parts
check out at ~0% overhang with no supports needed.

## Hard-won rules

- **Overlap, never kiss.** Touching components must interpenetrate by ≥0.4 mm;
  coplanar faces make Blender's EXACT boolean produce slivers. Cutters must poke
  ≥1 mm past every face they pierce.
- Depth measured from a top photo beats depth from a side photo (foreshortening);
  `measure_views.py` blends them 0.8/0.2 when both exist.
- Perspective inflates the nearer dimension a few percent. Two real dimensions from
  the user beat silhouette ratios.
- Keep cylinder `vertices` at 96–128; more only bloats the booleans.
- Mating parts (clips, sockets, stacking feet) need 0.25–0.35 mm clearance per side.
  See `scripts/blender_build_link_clip.py` for a ready-made connector clip.

## Scope

Expressible today: anything decomposable into axis-aligned boxes and axis-aligned
cylinders — which covers rectilinear furniture-like objects and rotational ones
(discs, trays, posts, drums). Not expressible: angled parts, lofts, organic
surfaces — those go through the AI-mesh path instead (image-to-3D model, then
`scripts/blender_finish.py` to rescue the mesh; see the project notes).

## Worked examples

- `outputs/component_mug_shelf_stackable_poc/stand_plan.json` — 12-component mug
  shelf with wells, side sockets, and stacking feet, from three photos
  (`examples/sample_images/stand_multiview/`).
- `outputs/circular_shelf_poc/plan.json` — rotational two-tier round shelf from a
  single 2×2 AI-generated view sheet (`examples/sample_images/circular_shelf_3dprint.png`).
