---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief-image-to-ai-to-stil-2026-01-08.md
workflowType: 'architecture'
lastStep: 8
date: 2026-01-08
---

# Architecture Document - image-to-ai-to-stil

**Author:** David
**Date:** 2026-01-08
**Version:** 1.0

---

## Executive Summary

This document defines the system architecture for **image-to-ai-to-stil**, an AI-powered image-to-OpenSCAD converter. The architecture prioritizes simplicity, modularity, and extensibility while meeting the MVP requirements for local-first, parametric 3D model generation.

### Architecture Goals

1. **Modularity** - Clear separation of concerns for testability and extensibility
2. **Simplicity** - Minimal dependencies, straightforward data flow
3. **Performance** - Efficient processing pipeline with caching support
4. **Extensibility** - Easy to add new output styles, models, or interfaces

---

## System Context

### External Systems

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Environment                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌─────────────────────┐     ┌──────────────┐ │
│  │  Input   │────▶│  image-to-ai-to-stil │────▶│   Output     │ │
│  │  Image   │     │      (CLI Tool)      │     │  .scad/.stl  │ │
│  └──────────┘     └─────────────────────┘     └──────────────┘ │
│                             │                                    │
│                             │ Uses                               │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  External Dependencies                    │   │
│  ├─────────────────┬───────────────────┬───────────────────┤   │
│  │  Hugging Face   │   Intel DPT       │    OpenSCAD       │   │
│  │  Hub (download) │   MiDaS Model     │    CLI            │   │
│  └─────────────────┴───────────────────┴───────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Overview

```
Input Image ──▶ Image Loader ──▶ Depth Estimator ──▶ Depth Analyzer
     │                                                      │
     │                                                      ▼
     │                                              OpenSCAD Generator
     │                                                      │
     │                                                      ▼
     │                                               STL Exporter
     │                                                      │
     └──────────────────────────────────────────────────────┘
                              Output Files
```

---

## Architectural Decisions

### ADR-001: Python as Primary Language

**Decision:** Use Python 3.9+ as the primary implementation language.

**Context:** Need to integrate with PyTorch-based AI models, provide cross-platform support, and enable rapid development.

**Rationale:**
- Native PyTorch and Transformers library support
- Excellent image processing libraries (Pillow, OpenCV)
- Cross-platform compatibility
- Strong NumPy/SciPy ecosystem for numerical operations
- Easy packaging and distribution via pip

**Consequences:**
- Performance may be slower than compiled languages (mitigated by PyTorch's C++ backend)
- Runtime dependency on Python interpreter

### ADR-002: Intel DPT-Hybrid-MiDaS for Depth Estimation

**Decision:** Use Intel's DPT-Hybrid-MiDaS model (~123M parameters) as the primary depth estimation model.

**Context:** Need accurate depth estimation from single images without requiring cloud APIs.

**Rationale:**
- MIT license allows commercial and open-source use
- Good balance of quality and speed
- Well-supported through Hugging Face Transformers
- Active maintenance and documentation
- Reasonable model size (~500MB)

**Alternatives Considered:**
- dpt-swinv2-tiny-256: Too low quality
- dpt-large: Too slow for typical use, ~1.4GB
- Depth Anything V2: Non-commercial license for better models

**Consequences:**
- Requires ~2GB RAM for inference
- One-time model download on first use

### ADR-003: Modular Pipeline Architecture

**Decision:** Implement processing as a pipeline of independent, composable modules.

**Context:** Need to support different processing stages that may evolve independently.

**Rationale:**
- Each stage can be tested independently
- Easy to swap implementations (different depth models, output styles)
- Clear interfaces between components
- Supports future extension (new analyzers, generators)

**Pattern:**
```python
# Pipeline stages are independent classes with consistent interfaces
class DepthEstimator:
    def estimate(self, image: np.ndarray) -> np.ndarray: ...

class DepthAnalyzer:
    def analyze(self, depth_map: np.ndarray, config: AnalysisConfig) -> HeightData: ...

class OpenSCADGenerator:
    def generate(self, height_data: HeightData, config: GeneratorConfig) -> str: ...
```

**Consequences:**
- Slightly more boilerplate than monolithic approach
- Need to define clear interfaces between stages

### ADR-004: Configuration via Dataclasses

**Decision:** Use Python dataclasses for configuration objects.

**Context:** Need structured configuration that can be validated and easily modified.

**Rationale:**
- Type hints provide IDE support and documentation
- Default values define sensible defaults
- Easy serialization to/from dictionaries
- No external dependency (built into Python 3.7+)

**Example:**
```python
@dataclass
class ConversionConfig:
    base_thickness: float = 2.0  # mm
    max_height: float = 15.0      # mm
    model_width: float = 100.0    # mm
    detail_level: float = 1.0     # 0.5 to 2.0
    smoothing: bool = True
    invert_depth: bool = False
```

### ADR-005: OpenSCAD CLI for STL Rendering

**Decision:** Use OpenSCAD's command-line interface for STL rendering rather than implementing mesh generation directly.

**Context:** Need to convert generated .scad files to .stl files.

**Rationale:**
- OpenSCAD is the standard tool for .scad files
- Avoids complex mesh generation code
- Leverages OpenSCAD's proven rendering engine
- Users likely already have OpenSCAD installed

**Consequences:**
- External dependency on OpenSCAD installation
- STL rendering time depends on OpenSCAD (not optimizable)
- Must handle OpenSCAD CLI errors gracefully

### ADR-006: Hugging Face Hub for Model Distribution

**Decision:** Use Hugging Face Hub for model downloading and caching.

**Context:** Need to distribute ~500MB model without bundling in package.

**Rationale:**
- Industry standard for ML model distribution
- Built-in caching prevents re-downloads
- Handles model versioning
- No need to host model files ourselves

**Consequences:**
- Requires internet for first run
- Users' models stored in ~/.cache/huggingface/

---

## Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Runtime | Python | 3.9+ | Application runtime |
| ML Framework | PyTorch | 2.0+ | Deep learning operations |
| Model Loading | Transformers | 4.35+ | Load DPT model |
| Image I/O | Pillow | 10.0+ | Read/write images |
| Image Processing | OpenCV | 4.8+ | Image transformations |
| Numerical | NumPy | 1.24+ | Array operations |
| CLI | argparse | stdlib | Command-line parsing |
| Model Cache | huggingface_hub | 0.20+ | Model downloading |

### External Tools

| Tool | Purpose | Required |
|------|---------|----------|
| OpenSCAD | STL rendering | Yes (for STL output) |

### Development Tools

| Tool | Purpose |
|------|---------|
| pytest | Unit and integration testing |
| black | Code formatting |
| mypy | Type checking |
| ruff | Linting |

---

## Component Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          image_to_scad                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐   ┌─────────────────┐   ┌─────────────────────┐   │
│  │    CLI      │──▶│   Converter     │──▶│      Config         │   │
│  │  (main.py)  │   │   (Pipeline)    │   │   (dataclasses)     │   │
│  └─────────────┘   └─────────────────┘   └─────────────────────┘   │
│                             │                                        │
│                             │ orchestrates                           │
│                             ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Processing Pipeline                       │   │
│  ├──────────────┬──────────────┬──────────────┬───────────────┤   │
│  │ ImageLoader  │DepthEstimator│DepthAnalyzer │OpenSCADGen    │   │
│  │              │              │              │               │   │
│  │ - load()    │ - estimate() │ - analyze()  │ - generate()  │   │
│  │ - validate()│ - cache model│ - smooth()   │ - format()    │   │
│  │ - resize()  │              │ - normalize()│               │   │
│  └──────────────┴──────────────┴──────────────┴───────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      Utilities                               │   │
│  ├──────────────────┬──────────────────┬───────────────────────┤   │
│  │   STLExporter    │   FileUtils      │      Logging          │   │
│  │                  │                  │                       │   │
│  │ - render()      │ - save_scad()    │ - progress()          │   │
│  │ - validate()    │ - save_stl()     │ - error()             │   │
│  └──────────────────┴──────────────────┴───────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### ImageLoader
- Load image files from disk
- Validate image format and dimensions
- Resize images to optimal processing dimensions
- Convert to RGB format for model input

#### DepthEstimator
- Initialize and cache the DPT model
- Preprocess images for model input
- Run depth estimation inference
- Post-process depth map output

#### DepthAnalyzer
- Convert depth map to height array
- Apply smoothing and filtering
- Handle depth inversion
- Normalize values to target height range

#### OpenSCADGenerator
- Generate parametric OpenSCAD code
- Apply relief/surface generation algorithms
- Format code with comments and parameters
- Support multiple output styles (future)

#### STLExporter
- Invoke OpenSCAD CLI for rendering
- Handle CLI errors and timeouts
- Validate generated STL files

#### Converter (Pipeline Orchestrator)
- Coordinate pipeline stages
- Handle configuration
- Provide progress callbacks
- Manage errors and cleanup

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
image-to-ai-to-stil/
├── README.md                    # Project documentation
├── LICENSE                      # MIT License
├── pyproject.toml              # Package configuration (PEP 517)
├── setup.py                    # Backward compatibility
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .gitignore                  # Git ignore rules
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
│
├── src/
│   └── image_to_scad/
│       ├── __init__.py         # Package exports
│       ├── __main__.py         # Entry point for python -m
│       ├── cli.py              # Command-line interface
│       ├── converter.py        # Pipeline orchestration
│       ├── config.py           # Configuration dataclasses
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── image_loader.py      # Image loading and validation
│       │   ├── depth_estimator.py   # DPT model integration
│       │   ├── depth_analyzer.py    # Depth map processing
│       │   └── scad_generator.py    # OpenSCAD code generation
│       │
│       ├── exporters/
│       │   ├── __init__.py
│       │   └── stl_exporter.py      # OpenSCAD CLI integration
│       │
│       ├── templates/
│       │   └── relief.scad.j2       # OpenSCAD code templates
│       │
│       └── utils/
│           ├── __init__.py
│           ├── file_utils.py        # File I/O helpers
│           └── logging.py           # Logging configuration
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_cli.py             # CLI tests
│   ├── test_converter.py       # Integration tests
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_image_loader.py
│   │   ├── test_depth_analyzer.py
│   │   └── test_scad_generator.py
│   │
│   ├── fixtures/
│   │   ├── images/             # Test input images
│   │   │   ├── simple_shape.png
│   │   │   ├── photo.jpg
│   │   │   └── logo.png
│   │   └── expected/           # Expected outputs
│   │       └── simple_shape.scad
│   │
│   └── integration/
│       └── test_full_pipeline.py
│
├── docs/
│   ├── PROJECT_PLAN.md         # Original project plan
│   ├── SETUP.md                # Setup instructions
│   └── examples/               # Usage examples
│       └── basic_usage.md
│
├── examples/
│   ├── sample_images/          # Sample input images
│   └── sample_outputs/         # Sample generated outputs
│
├── scripts/
│   └── download_model.py       # Model download script
│
├── _bmad/                      # BMAD framework (git-ignored optional)
├── _bmad-output/               # BMAD artifacts
│   ├── planning-artifacts/
│   └── implementation-artifacts/
│
└── venv/                       # Virtual environment (git-ignored)
```

### Architectural Boundaries

**API Boundaries:**
- CLI is the only public interface (MVP)
- All user interaction through command-line arguments
- Output via files (.scad, .stl) and stdout (progress, errors)

**Component Boundaries:**
- Pipeline components communicate via typed data objects
- No direct dependencies between pipeline stages
- Converter orchestrates all pipeline interactions

**Data Boundaries:**
- Input: Image files (PIL Image -> numpy array)
- Intermediate: numpy arrays (depth map, height data)
- Output: String (OpenSCAD code), files (.scad, .stl)

### Requirements to Structure Mapping

| Functional Requirement | Component | Location |
|----------------------|-----------|----------|
| FR1-FR4: Image input | ImageLoader | src/image_to_scad/pipeline/image_loader.py |
| FR5-FR8: Depth estimation | DepthEstimator | src/image_to_scad/pipeline/depth_estimator.py |
| FR9-FR12: Depth analysis | DepthAnalyzer | src/image_to_scad/pipeline/depth_analyzer.py |
| FR13-FR19: OpenSCAD generation | OpenSCADGenerator | src/image_to_scad/pipeline/scad_generator.py |
| FR20-FR22: STL export | STLExporter | src/image_to_scad/exporters/stl_exporter.py |
| FR23-FR31: CLI | CLI module | src/image_to_scad/cli.py |

---

## Data Models

### Core Data Structures

```python
@dataclass
class ConversionConfig:
    """User-configurable conversion parameters."""
    base_thickness: float = 2.0      # mm - minimum thickness
    max_height: float = 15.0         # mm - maximum relief height
    model_width: float = 100.0       # mm - output model width
    detail_level: float = 1.0        # 0.5-2.0 multiplier
    smoothing: bool = True           # apply smoothing filter
    invert_depth: bool = False       # flip depth interpretation
    output_style: str = "relief"     # output style (MVP: relief only)

@dataclass
class HeightData:
    """Processed height data ready for OpenSCAD generation."""
    heights: np.ndarray              # 2D array of height values (mm)
    width_mm: float                  # physical width in mm
    height_mm: float                 # physical height in mm
    resolution: Tuple[int, int]      # grid resolution (rows, cols)

@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    scad_code: str                   # generated OpenSCAD code
    scad_path: Optional[Path]        # path to saved .scad file
    stl_path: Optional[Path]         # path to rendered .stl file
    depth_map: Optional[np.ndarray]  # intermediate depth map (debug)
    processing_time: float           # total processing time in seconds
```

### Interface Contracts

```python
# Pipeline stage interfaces
class ImageLoaderProtocol(Protocol):
    def load(self, path: Path) -> np.ndarray:
        """Load and preprocess image, return RGB numpy array."""
        ...

class DepthEstimatorProtocol(Protocol):
    def estimate(self, image: np.ndarray) -> np.ndarray:
        """Estimate depth from image, return depth map array."""
        ...

class DepthAnalyzerProtocol(Protocol):
    def analyze(self, depth_map: np.ndarray, config: ConversionConfig) -> HeightData:
        """Convert depth map to height data using config parameters."""
        ...

class OpenSCADGeneratorProtocol(Protocol):
    def generate(self, height_data: HeightData, config: ConversionConfig) -> str:
        """Generate OpenSCAD code from height data."""
        ...
```

---

## Error Handling Strategy

### Error Categories

| Category | Example | Handling |
|----------|---------|----------|
| Input Validation | Invalid file format | Raise ValueError with clear message |
| File I/O | File not found | Raise FileNotFoundError with path |
| Model Loading | Model download failed | Raise RuntimeError with instructions |
| Processing | Image too small | Raise ValueError with requirements |
| External Tool | OpenSCAD not found | Raise RuntimeError with install instructions |

### Error Handling Pattern

```python
class ImageToScadError(Exception):
    """Base exception for all image-to-scad errors."""
    pass

class ImageLoadError(ImageToScadError):
    """Error loading or validating input image."""
    pass

class DepthEstimationError(ImageToScadError):
    """Error during depth estimation."""
    pass

class OpenSCADError(ImageToScadError):
    """Error generating or rendering OpenSCAD code."""
    pass

class STLExportError(ImageToScadError):
    """Error exporting STL file."""
    pass
```

---

## Testing Strategy

### Test Levels

| Level | Scope | Location | Tools |
|-------|-------|----------|-------|
| Unit | Individual functions | tests/unit/ | pytest, mock |
| Integration | Pipeline stages | tests/integration/ | pytest |
| End-to-End | Full CLI workflow | tests/test_cli.py | pytest, subprocess |

### Test Data Strategy

- Small, fast test images (64x64, 128x128) for unit tests
- Representative images (512x512) for integration tests
- Golden output files for regression testing
- Fixtures provide test configuration and mock data

### Coverage Targets

| Component | Target Coverage |
|-----------|-----------------|
| Pipeline stages | 90% |
| CLI | 80% |
| Utilities | 80% |
| Error handling | 100% |

---

## Deployment Architecture

### Distribution

- PyPI package: `pip install image-to-scad`
- GitHub releases with changelogs
- No Docker container (MVP) - users install Python package

### Installation Flow

```
1. pip install image-to-scad
2. First run: Model downloads automatically to ~/.cache/huggingface/
3. User runs: image-to-scad input.jpg -o output.scad
4. Optional: OpenSCAD renders STL if installed
```

### Versioning

- Semantic versioning (MAJOR.MINOR.PATCH)
- Model version pinned in code
- Dependencies pinned in requirements.txt

---

## Security Considerations

### Data Privacy
- All processing local - no data transmitted externally
- No telemetry or usage tracking
- Model downloaded from official Hugging Face only

### Dependency Security
- Pin all dependency versions
- Use dependabot for security updates
- Verify Hugging Face model checksums

### Input Validation
- Validate file types before processing
- Limit maximum input image size
- Sanitize file paths

---

## Performance Considerations

### Optimization Points

| Stage | Optimization | Impact |
|-------|-------------|--------|
| Model Loading | Lazy loading, caching | First run only |
| Depth Estimation | GPU acceleration | 4-10x speedup |
| OpenSCAD Generation | NumPy vectorization | 2-3x speedup |
| STL Rendering | OpenSCAD -q flag | Faster rendering |

### Memory Management
- Process images in-place where possible
- Release model after processing (optional)
- Use memory-efficient NumPy dtypes

---

## Future Extensibility

### Planned Extension Points

1. **Multiple Output Styles** - Add new generators (layered, object extraction)
2. **Alternative Models** - Swap DepthEstimator implementation
3. **Batch Processing** - Process multiple images with parallelization
4. **Web Interface** - Add Gradio/Streamlit frontend
5. **Plugin System** - Allow community extensions

### Extension Patterns

```python
# Style registry for multiple output styles
STYLE_REGISTRY: Dict[str, Type[OpenSCADGenerator]] = {
    "relief": ReliefGenerator,
    # Future: "layered": LayeredGenerator,
    # Future: "object": ObjectGenerator,
}

# Model registry for multiple depth models
MODEL_REGISTRY: Dict[str, Type[DepthEstimator]] = {
    "dpt-hybrid": DPTHybridEstimator,
    # Future: "depth-anything": DepthAnythingEstimator,
}
```

---

## Implementation Notes for AI Agents

### Critical Constraints

1. **DO NOT** add features not in the PRD functional requirements
2. **DO NOT** implement web UI in MVP
3. **DO NOT** add telemetry or external data transmission
4. **DO** follow the exact project structure defined above
5. **DO** use dataclasses for configuration
6. **DO** implement Protocol classes for testability

### Code Style Requirements

- PEP 8 formatting (use black)
- Type hints on all public functions
- Docstrings on all classes and public methods
- Maximum line length: 100 characters

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | depth_estimator.py |
| Classes | PascalCase | DepthEstimator |
| Functions | snake_case | estimate_depth() |
| Constants | UPPER_SNAKE | DEFAULT_HEIGHT |
| Config vars | snake_case | base_thickness |

---

*Architecture document created following BMad Method v6.0 workflow*
*Reference: PRD, Product Brief, PROJECT_PLAN.md*
