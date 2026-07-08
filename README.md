# image → 3D → STL

Turn images into printable, watertight 3D models — fully local, no cloud, no API fees.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Two complementary pipelines, both backed by headless Blender:

## 1. Component-model track (functional objects)

For stands, shelves, docks, organizers — anything decomposable into boxes and
cylinders, including rotational shapes (discs, posts, trays). Reference photos supply
**measurements and design intent only**; the model itself is a hand-editable JSON plan
of primitives, built deterministically into an STL. Parametric by construction: change
a dimension by editing a number and rebuilding.

```bash
# 1. Measure silhouette proportions (anchor one real dimension)
venv/bin/python scripts/measure_views.py front=front.png top=top.png --width-mm 250

# 2. Write plan.json (boxes + cylinders; see docs), then build:
blender --background --python scripts/blender_build_components.py -- \
    plan.json model.stl --render-dir renders
```

**[Full workflow guide → docs/component-model-workflow.md](docs/component-model-workflow.md)**

Why this beats AI mesh generation for functional parts: crisp faces, true dimensions,
guaranteed-clean geometry, and features like recesses, sockets, and stacking feet are
just more entries in the plan. Worked examples: a stackable 12-component mug shelf
(`outputs/component_mug_shelf_stackable_poc/stand_plan.json`) and a circular two-tier
shelf built from a single AI-generated view sheet (`outputs/circular_shelf_poc/plan.json`).

## 2. AI-mesh track (organic shapes)

For figures and freeform objects that can't be decomposed into primitives:
photo(s) → **Hunyuan3D-2.1** (local, MPS/CUDA) → watertight finishing → STL.

```bash
./Hunyuan3D-2.1-mac/.venv/bin/python image_to_stl.py photo.png -o out --size-mm 120
```

**[Setup and usage → docs/IMAGE_TO_STL.md](docs/IMAGE_TO_STL.md)**

Broken-but-detailed meshes (e.g. TRELLIS output) are rescued by
`scripts/blender_finish.py` — an OpenVDB voxel remesh that produces a watertight
manifold while preserving the detail that conventional mesh repair destroys.

## Requirements

- Python 3.11+, `python -m venv venv && venv/bin/pip install -r requirements.txt`
- [Blender](https://www.blender.org/) on PATH (`brew install blender`)
- AI-mesh track only: see `docs/IMAGE_TO_STL.md` (separate venv + model weights)

## History

This repo began as **image-to-scad**, a depth-map → OpenSCAD relief generator. That
tool was retired in July 2026 in favor of the pipelines above, which realize the same
goal — images to parametric, editable, printable models — more completely. The old
code lives in git history.

## License

MIT
