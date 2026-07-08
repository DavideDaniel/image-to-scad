# CLAUDE.md - Project Guidelines for AI Assistants

## Project Overview

**image-to-ai-to-stil** is an AI-powered CLI tool that converts 2D images into parametric, editable OpenSCAD code suitable for 3D printing. It uses Intel's DPT-Hybrid-MiDaS model for depth estimation.

### Key Differentiators
- **Parametric Output** - Generated OpenSCAD code is customizable, not static meshes
- **Local Processing** - No cloud dependencies, no API fees, complete privacy
- **Open Source** - MIT licensed

## Tech Stack

- **Language:** Python 3.9+
- **ML Framework:** PyTorch 2.0+
- **Model:** Intel DPT-Hybrid-MiDaS (via Hugging Face Transformers)
- **Image Processing:** Pillow, OpenCV
- **CLI:** argparse (stdlib)
- **Testing:** pytest
- **Formatting:** black, ruff, mypy

## Project Structure

```
src/image_to_scad/
├── __init__.py          # Package exports, version
├── __main__.py          # Entry point for python -m
├── cli.py               # Command-line interface
├── converter.py         # Pipeline orchestration
├── config.py            # Configuration dataclasses
├── exceptions.py        # Custom exception hierarchy
├── pipeline/
│   ├── image_loader.py      # Image loading and validation
│   ├── depth_estimator.py   # DPT model integration
│   ├── depth_analyzer.py    # Depth map processing
│   └── scad_generator.py    # OpenSCAD code generation
├── exporters/
│   └── stl_exporter.py      # OpenSCAD CLI integration
└── utils/
    ├── file_utils.py        # File I/O helpers
    └── logging.py           # Logging configuration
```

## Architecture Decisions

### ADR-001: Modular Pipeline
Processing is implemented as independent, composable modules with Protocol interfaces for testability.

### ADR-002: Dataclasses for Configuration
All configuration uses Python dataclasses with type hints and default values.

### ADR-003: Custom Exception Hierarchy
```python
ImageToScadError (base)
├── ImageLoadError
├── DepthEstimationError
├── OpenSCADError
└── STLExportError
```

### ADR-004: OpenSCAD CLI for STL
STL rendering uses OpenSCAD's CLI rather than implementing mesh generation directly.

### ADR-005: Blender is the geometry backend for the 3D tracks (settled 2026-07)
Both 3D-model tracks (see "3D Generation Tracks" below) run headless Blender:
`scripts/blender_build_components.py` for CSG assembly and `scripts/blender_finish.py`
(OpenVDB voxel remesh) for mesh repair. This was chosen after head-to-head tests over
OpenSCAD CSG (too slow for many primitives), and over trimesh/pymeshlab repair
(`poisson`/`voxel`/`meshfix` destroy detail on broken meshes — a TRELLIS mug holder
that Blender rescued cleanly came out a melted blob from every trimesh path). The
trimesh-based experiments were removed; do not reintroduce them. Requires `blender`
on PATH (`brew install blender`). Exception: clean Hunyuan meshes need only
`scripts/finish_print.py --method gentle`.

### ADR-006: Component-plan JSON is the parametric model format
Component-track models are defined by an editable `component-plan/v0` JSON (axis-aligned
boxes + cylinders; unions, then cuts) built deterministically by
`scripts/blender_build_components.py`. Reference images supply *measurements and design
intent only*. Never write per-object generator Python — author or edit the plan JSON.
(`scripts/component_plan_from_stand_images.py` predates this decision and is kept only
as a worked example.)

## 3D Generation Tracks

Besides the core depth-relief CLI (`src/image_to_scad/`), the repo has two
image→3D-model pipelines. Route by object type:

1. **Component-model track** — PREFERRED for functional objects (stands, shelves,
   docks, organizers): anything decomposable into axis-aligned boxes and cylinders,
   including rotational shapes (discs, posts, trays). Photos → measured proportions
   (`scripts/measure_views.py`) → plan JSON → Blender CSG → STL.
   Docs: `docs/component-model-workflow.md`; skill: `.claude/skills/component-model`.
2. **AI-mesh track** — for organic/sculptural shapes only. Image(s) → Hunyuan3D-2.1
   (or TRELLIS) → mesh finishing per ADR-005. Docs: `docs/IMAGE_TO_STL.md`.

## Key Data Models

```python
@dataclass
class ConversionConfig:
    base_thickness: float = 2.0      # mm
    max_height: float = 15.0         # mm
    model_width: float = 100.0       # mm
    detail_level: float = 1.0        # 0.5-2.0
    smoothing: bool = True
    invert_depth: bool = False

@dataclass
class HeightData:
    heights: np.ndarray              # 2D array (mm)
    width_mm: float
    height_mm: float
    resolution: Tuple[int, int]
```

## Code Style

- PEP 8 formatting with black
- Type hints on all public functions
- Docstrings on all classes and public methods
- Maximum line length: 100 characters
- Use Protocol classes for interfaces

## Testing

- **Unit tests:** `tests/unit/` - Test individual components with mocks
- **Integration tests:** `tests/integration/` - Test pipeline stages together
- **Fixtures:** Small test images (64x64, 128x128) in `tests/fixtures/`
- **Coverage target:** 90% for pipeline stages

Run tests:
```bash
pytest                          # All tests
pytest tests/unit/              # Unit tests only
pytest -v --tb=short            # Verbose with short tracebacks
```

## Common Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the tool
image-to-scad input.jpg                    # Basic conversion
image-to-scad input.jpg -o output.scad     # Custom output path
image-to-scad input.jpg --width 80 --max-height 20  # With parameters

# Development
black src/ tests/                # Format code
ruff check src/ tests/           # Lint
mypy src/                        # Type check
pytest                           # Run tests
```

## Planning Artifacts

Located in `_bmad-output/planning-artifacts/`:
- `prd.md` - Product Requirements (31 FRs, 24 NFRs)
- `architecture.md` - Architecture decisions and component design
- `epics.md` - Epic and story breakdown (4 epics, 14 stories)

## Implementation Status

The project has completed planning phase. Implementation should follow the epic order:
1. **Epic 1:** Image to OpenSCAD Core (6 stories) - Basic conversion pipeline
2. **Epic 2:** Customizable 3D Output (3 stories) - Parameter customization
3. **Epic 3:** Complete CLI Experience (3 stories) - Help, progress, output paths
4. **Epic 4:** STL Export & Printing (2 stories) - OpenSCAD CLI integration

## Performance Targets

- Depth estimation: <20 seconds on CPU
- Code generation: <5 seconds
- Total end-to-end: <30 seconds (excluding STL render)
- Memory: <4GB during processing

## Important Constraints

- **DO NOT** add features not in the PRD
- **DO NOT** transmit any data externally
- **DO NOT** add telemetry or tracking
- **DO** follow the exact project structure
- **DO** use dataclasses for configuration
- **DO** implement Protocol classes for testability
