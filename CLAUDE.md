# CLAUDE.md - Project Guidelines for AI Assistants

## Project Overview

This project turns **images into printable 3D models (STL), fully locally**, via two
complementary pipelines. There is no cloud dependency, no telemetry, and no data ever
leaves the machine.

> **History note:** the repo began as *image-to-scad*, a depth-map → OpenSCAD relief
> CLI (`src/image_to_scad/`). That product was removed in July 2026 after the tracks
> below proved to be the better realization of the same goal ("images → parametric,
> editable models"). Its code, tests, and BMAD planning artifacts live in git history
> before that removal — do not resurrect them or "fix" references to them.

## The Two Tracks (route by object type)

1. **Component-model track — PREFERRED for functional objects** (stands, shelves,
   docks, organizers): anything decomposable into axis-aligned boxes and cylinders,
   including rotational shapes (discs, posts, trays, drums).
   Photos supply *measurements and design intent only*; the model is an editable
   `component-plan/v0` JSON built deterministically into an STL by headless Blender.
   - Docs: `docs/component-model-workflow.md` (human) and
     `.claude/skills/component-model/SKILL.md` (agent skill — use it).
   - Scripts: `scripts/measure_views.py`, `scripts/blender_build_components.py`,
     `scripts/split_views.py`, plus modular extras (`blender_build_link_clip.py`,
     `blender_preview_stack.py`).

2. **AI-mesh track — for organic/sculptural shapes only** (figures, freeform objects):
   image(s) → Hunyuan3D-2.1 (or TRELLIS) → mesh finishing → STL.
   - Docs: `docs/IMAGE_TO_STL.md`; entry point `image_to_stl.py` (run with the
     Hunyuan venv, not the project venv).
   - Finishing: clean Hunyuan meshes → `scripts/finish_print.py --method gentle`;
     broken-but-detailed meshes (TRELLIS) → `scripts/blender_finish.py`.

## Architecture Decisions

### ADR-001: Blender is the geometry backend (settled 2026-07)
CSG assembly (`scripts/blender_build_components.py`) and mesh repair
(`scripts/blender_finish.py`, OpenVDB voxel remesh) run in headless Blender. Chosen
after head-to-head tests over OpenSCAD CSG (unusably slow with many primitives) and
over trimesh/pymeshlab repair (`poisson`/`voxel`/`meshfix` destroy detail — a TRELLIS
mug holder that Blender rescued cleanly, 60K boundary edges → 72 with detail intact,
came out a melted blob from every trimesh path). The trimesh repair experiments were
deleted; do not reintroduce them. Requires `blender` on PATH (`brew install blender`).
Exception: clean Hunyuan SDF meshes need only `finish_print.py --method gentle`.

### ADR-002: Component-plan JSON is the parametric model format
Component-track models are defined by an editable `component-plan/v0` JSON
(axis-aligned boxes + cylinders; components unioned in order, then cuts subtracted).
Images are never reconstructed into geometry directly — they only anchor measurements.
**Never write per-object generator Python** — author or edit the plan JSON.
(`scripts/component_plan_from_stand_images.py` predates this decision; it is kept
only as a worked example of one object class.)

## Environments

- **Project venv `venv/`** — Pillow, OpenCV, numpy, trimesh, scipy
  (`requirements.txt`). Used by `measure_views.py`, `split_views.py`, and mesh
  verification one-liners. The system `python3` does NOT have these.
- **Blender** (`brew install blender`) — runs all `scripts/blender_*.py` headless.
- **AI-mesh venvs** — `Hunyuan3D-2.1-mac/.venv` and `trellis-mac/.venv` (git-ignored,
  fetched per `docs/IMAGE_TO_STL.md`; heavy deps in `requirements-shape.txt`).

## Common Commands

```bash
# Measure object proportions from photos (anchor one real dimension)
venv/bin/python scripts/measure_views.py front=f.png top=t.png --width-mm 250

# Build a plan JSON into STL/OBJ/blend + QA renders
blender --background --python scripts/blender_build_components.py -- \
    plan.json model.stl --render-dir renders

# Verify printability
venv/bin/python -c "import trimesh; m=trimesh.load('model.stl'); \
print(m.is_watertight, m.body_count, m.extents)"

# Rescue a broken-but-detailed AI mesh
blender --background --python scripts/blender_finish.py -- in.obj out.stl --res 384

# AI-mesh generation (organic shapes; slow, ~15-20 min on MPS)
./Hunyuan3D-2.1-mac/.venv/bin/python image_to_stl.py photo.png -o out --size-mm 120
```

## Hard Constraints

- **DO NOT** write per-object geometry generators — the plan JSON is the model (ADR-002).
- **DO NOT** reintroduce trimesh/pymeshlab mesh repair (ADR-001).
- **DO NOT** transmit any data externally; everything runs locally.
- **DO** overlap touching plan components by ≥0.4 mm (coplanar faces → boolean
  slivers, worse on Blender 5.x); cutters must poke ≥1 mm past pierced faces.
- **DO** keep generated artifacts out of git — `outputs/` is git-ignored except
  hand-picked example plan JSONs (`git add -f`).

## Worked Examples

- `outputs/component_mug_shelf_stackable_poc/stand_plan.json` — 12-component mug
  shelf with wells, side sockets, stacking feet (photos in
  `examples/sample_images/stand_multiview/`).
- `outputs/circular_shelf_poc/plan.json` — rotational two-tier shelf from one
  AI-generated 2×2 view sheet (`examples/sample_images/circular_shelf_3dprint.png`).
