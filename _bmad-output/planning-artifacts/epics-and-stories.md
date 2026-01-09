---
stepsCompleted: [1]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
workflowType: 'epics-and-stories'
lastStep: 1
date: 2026-01-08
---

# Epics and Stories - image-to-ai-to-stil

**Author:** David
**Date:** 2026-01-08
**Version:** 1.0
**Phase:** MVP Phase 1

---

## Overview

This document breaks down the 31 Functional Requirements from the PRD into implementable Epics and User Stories for the MVP Phase 1. The focus is on delivering the core pipeline from image input to OpenSCAD output.

### MVP Phase 1 Scope

The MVP delivers a complete CLI-based workflow enabling users to:
1. Provide an image file as input
2. Generate a depth map using AI
3. Convert depth data to height information
4. Generate parametric OpenSCAD code
5. Optionally render to STL

### Epic Summary

| Epic | Name | Stories | Priority |
|------|------|---------|----------|
| E1 | Core Pipeline Infrastructure | 5 | P0 - Critical |
| E2 | Image Input Management | 4 | P0 - Critical |
| E3 | Depth Estimation | 4 | P0 - Critical |
| E4 | Depth Analysis | 4 | P0 - Critical |
| E5 | OpenSCAD Generation | 7 | P0 - Critical |
| E6 | STL Export | 3 | P1 - High |
| E7 | Command Line Interface | 7 | P0 - Critical |
| E8 | Configuration Management | 2 | P1 - High |

---

## Epic 1: Core Pipeline Infrastructure

**Description:** Establish the foundational project structure, configuration system, and pipeline orchestration that enables all other components to function together.

**Business Value:** Creates the skeleton upon which all features are built; enables modular development and testing.

**Functional Requirements Covered:** Supports all FRs through infrastructure

---

### Story 1.1: Project Structure Setup

**As a** developer,
**I want to** have a well-organized project structure following Python best practices,
**So that** code is maintainable, testable, and follows the architecture specification.

**Priority:** P0 - Critical
**Story Points:** 3

**Acceptance Criteria:**
- [ ] Project follows the directory structure defined in architecture.md
- [ ] `src/image_to_scad/` package is properly initialized with `__init__.py`
- [ ] Pipeline, exporters, and utils subpackages are created
- [ ] `pyproject.toml` configures package metadata and entry points
- [ ] `requirements.txt` lists all production dependencies with pinned versions
- [ ] `requirements-dev.txt` lists development dependencies

**Technical Notes:**
- Entry point: `image-to-scad` command maps to `cli:main`
- Use `src/` layout for proper package isolation

---

### Story 1.2: Configuration Dataclasses

**As a** developer,
**I want to** use typed configuration objects with sensible defaults,
**So that** configuration is validated, documented, and easy to modify.

**Priority:** P0 - Critical
**Story Points:** 2

**Acceptance Criteria:**
- [ ] `ConversionConfig` dataclass exists with all documented fields
- [ ] Default values match PRD specifications (base_thickness=2.0, max_height=15.0, etc.)
- [ ] `HeightData` dataclass exists for pipeline data transfer
- [ ] `ConversionResult` dataclass exists for operation results
- [ ] All dataclasses have type hints and docstrings
- [ ] Configuration can be serialized to/from dictionaries

**Technical Notes:**
- Located in `src/image_to_scad/config.py`
- Use `@dataclass` decorator from standard library

---

### Story 1.3: Pipeline Orchestrator

**As a** developer,
**I want to** have a central Converter class that orchestrates all pipeline stages,
**So that** the conversion process is coordinated and progress can be tracked.

**Priority:** P0 - Critical
**Story Points:** 5

**Acceptance Criteria:**
- [ ] `Converter` class exists in `src/image_to_scad/converter.py`
- [ ] Converter accepts a `ConversionConfig` object
- [ ] Converter has a `convert(image_path) -> ConversionResult` method
- [ ] Converter initializes and calls each pipeline stage in order
- [ ] Processing time is tracked and included in result
- [ ] Converter supports optional progress callback for UI feedback

**Technical Notes:**
- Pipeline order: ImageLoader -> DepthEstimator -> DepthAnalyzer -> OpenSCADGenerator
- Optional: STLExporter if STL output requested

---

### Story 1.4: Custom Exception Hierarchy

**As a** developer,
**I want to** have specific exception classes for different error types,
**So that** errors can be handled appropriately and users receive clear messages.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] `ImageToScadError` base exception class exists
- [ ] `ImageLoadError` for image loading failures
- [ ] `DepthEstimationError` for AI model failures
- [ ] `OpenSCADError` for code generation failures
- [ ] `STLExportError` for rendering failures
- [ ] All exceptions include descriptive messages

**Technical Notes:**
- Located in `src/image_to_scad/exceptions.py` or within relevant modules

---

### Story 1.5: Logging and Progress Utilities

**As a** user,
**I want to** see progress feedback during processing,
**So that** I know the tool is working and can estimate completion time.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Progress utility provides stage-based progress updates
- [ ] Logging is configured with appropriate levels (INFO for normal, DEBUG for verbose)
- [ ] Progress messages are human-readable (e.g., "Loading image...", "Estimating depth...")
- [ ] Errors are logged with sufficient context for debugging

**Technical Notes:**
- Located in `src/image_to_scad/utils/logging.py`
- Use Python's built-in `logging` module

---

## Epic 2: Image Input Management

**Description:** Handle image loading, validation, and preprocessing to prepare images for depth estimation.

**Business Value:** Enables users to convert their images; ensures robust handling of various input formats.

**Functional Requirements Covered:** FR1, FR2, FR3, FR4

---

### Story 2.1: Image File Loading (FR1)

**As a** user,
**I want to** provide an image file path as input,
**So that** I can convert my images to 3D models.

**Priority:** P0 - Critical
**Story Points:** 2

**Acceptance Criteria:**
- [ ] `ImageLoader` class exists in `src/image_to_scad/pipeline/image_loader.py`
- [ ] `load(path: Path) -> np.ndarray` method reads image from disk
- [ ] Loaded image is converted to RGB format (no alpha channel)
- [ ] Returns numpy array suitable for depth estimation model
- [ ] Raises `ImageLoadError` with clear message if file not found

**Technical Notes:**
- Use Pillow for image loading
- Convert RGBA to RGB by removing alpha channel or compositing on white

---

### Story 2.2: Image Format Validation (FR2)

**As a** user,
**I want to** receive clear error messages for unsupported image formats,
**So that** I know which images I can use.

**Priority:** P0 - Critical
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Supported formats: JPEG, PNG, BMP, TIFF, WebP
- [ ] `validate(path: Path) -> bool` method checks file format
- [ ] Validation checks file extension and attempts to open with Pillow
- [ ] Clear error message lists supported formats when validation fails
- [ ] Corrupted image files are detected and reported

**Technical Notes:**
- Use Pillow's `Image.open()` in a try block to verify file is valid
- Check file magic bytes if extension is ambiguous

---

### Story 2.3: Automatic Image Resizing (FR3)

**As a** user,
**I want to** have images automatically resized to optimal dimensions,
**So that** processing is efficient regardless of input resolution.

**Priority:** P0 - Critical
**Story Points:** 3

**Acceptance Criteria:**
- [ ] Images larger than optimal size are downscaled
- [ ] Aspect ratio is preserved during resize
- [ ] Default optimal size is 384px (DPT model input size)
- [ ] Resize uses high-quality interpolation (Lanczos or bicubic)
- [ ] Original image dimensions are preserved in metadata for scaling output

**Technical Notes:**
- DPT model works best with 384x384 input
- Store original dimensions to calculate correct output scale

---

### Story 2.4: Detail Level Preference (FR4)

**As a** user,
**I want to** specify my preferred detail level,
**So that** I can balance processing time against output detail.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] `detail_level` parameter accepts values 0.5 to 2.0
- [ ] Detail level affects resize target (0.5 = 192px, 1.0 = 384px, 2.0 = 768px)
- [ ] Higher detail levels preserve more image information
- [ ] Default detail level is 1.0
- [ ] Invalid detail levels raise ValueError with valid range

**Technical Notes:**
- detail_level multiplies base resolution (384px)
- Consider memory implications of larger sizes

---

## Epic 3: Depth Estimation

**Description:** Integrate the Intel DPT-Hybrid-MiDaS model to generate depth maps from input images.

**Business Value:** Core AI capability that transforms 2D images into 3D-ready data.

**Functional Requirements Covered:** FR5, FR6, FR7, FR8

---

### Story 3.1: Model Loading and Initialization (FR5)

**As a** developer,
**I want to** load the Intel DPT-Hybrid-MiDaS model,
**So that** depth estimation can be performed.

**Priority:** P0 - Critical
**Story Points:** 5

**Acceptance Criteria:**
- [ ] `DepthEstimator` class exists in `src/image_to_scad/pipeline/depth_estimator.py`
- [ ] Model is loaded from Hugging Face Hub (`Intel/dpt-hybrid-midas`)
- [ ] Model loads on CPU by default
- [ ] GPU is used if CUDA is available and not disabled
- [ ] Clear error message if model download fails (with retry instructions)
- [ ] First run downloads model automatically (~500MB)

**Technical Notes:**
- Use `transformers.pipeline("depth-estimation")` for simplicity
- Or load with `AutoProcessor` and `AutoModelForDepthEstimation`

---

### Story 3.2: Depth Map Generation (FR6)

**As a** user,
**I want to** generate a depth map from my image,
**So that** the image can be converted to 3D.

**Priority:** P0 - Critical
**Story Points:** 3

**Acceptance Criteria:**
- [ ] `estimate(image: np.ndarray) -> np.ndarray` method generates depth map
- [ ] Input image is preprocessed according to model requirements
- [ ] Output is a 2D numpy array of depth values
- [ ] Processing works on CPU without CUDA installed
- [ ] GPU acceleration used when available
- [ ] Raises `DepthEstimationError` on model inference failure

**Technical Notes:**
- Model outputs relative depth (not metric depth)
- Output depth map may have different resolution than input

---

### Story 3.3: Depth Value Normalization (FR7)

**As a** developer,
**I want to** normalize depth values to a consistent range,
**So that** downstream processing has predictable input.

**Priority:** P0 - Critical
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Depth values are normalized to 0.0-1.0 range
- [ ] Normalization handles edge cases (uniform depth, extreme values)
- [ ] Original depth statistics available if needed (min, max, mean)
- [ ] Normalization is consistent across different images

**Technical Notes:**
- Use min-max normalization: `(depth - min) / (max - min)`
- Handle division by zero for uniform images

---

### Story 3.4: Model Caching (FR8)

**As a** user,
**I want to** have the model cached after first load,
**So that** subsequent conversions are faster.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Model is cached in `~/.cache/huggingface/` (default HF behavior)
- [ ] Second run does not re-download the model
- [ ] DepthEstimator can optionally keep model in memory between calls
- [ ] Memory can be freed by explicitly releasing the model

**Technical Notes:**
- Hugging Face Hub handles file caching automatically
- In-memory caching is optional optimization for batch use

---

## Epic 4: Depth Analysis

**Description:** Process depth maps into height data suitable for 3D model generation.

**Business Value:** Transforms raw AI output into usable 3D data with user-controlled parameters.

**Functional Requirements Covered:** FR9, FR10, FR11, FR12

---

### Story 4.1: Depth to Height Conversion (FR9)

**As a** developer,
**I want to** convert depth maps to height arrays,
**So that** the data is ready for OpenSCAD generation.

**Priority:** P0 - Critical
**Story Points:** 3

**Acceptance Criteria:**
- [ ] `DepthAnalyzer` class exists in `src/image_to_scad/pipeline/depth_analyzer.py`
- [ ] `analyze(depth_map, config) -> HeightData` method processes depth
- [ ] Height values are scaled to target range (0 to max_height mm)
- [ ] Base thickness is added to ensure minimum thickness
- [ ] Output HeightData includes physical dimensions in mm

**Technical Notes:**
- Height = base_thickness + (normalized_depth * max_height)
- Physical dimensions derived from model_width and aspect ratio

---

### Story 4.2: Smoothing Filters (FR10)

**As a** user,
**I want to** have noise reduced in the depth data,
**So that** my 3D model has clean surfaces.

**Priority:** P1 - High
**Story Points:** 3

**Acceptance Criteria:**
- [ ] Gaussian smoothing filter available
- [ ] Smoothing can be enabled/disabled via config
- [ ] Smoothing strength adjustable (sigma parameter)
- [ ] Smoothing preserves edge features reasonably well
- [ ] Default smoothing enabled with sensible sigma

**Technical Notes:**
- Use `scipy.ndimage.gaussian_filter` or OpenCV
- Consider bilateral filter for edge preservation (future enhancement)

---

### Story 4.3: Output Resolution Control (FR11)

**As a** user,
**I want to** control the output resolution,
**So that** I can balance file size against model detail.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Detail level affects final grid resolution
- [ ] Lower detail produces fewer points (faster OpenSCAD rendering)
- [ ] Resolution is adjustable independently of input image size
- [ ] Default resolution produces reasonable file sizes (<1MB .scad)

**Technical Notes:**
- Resample height array to target resolution
- Typical target: 100-200 points per side for relief

---

### Story 4.4: Depth Inversion (FR12)

**As a** user,
**I want to** invert the depth interpretation,
**So that** I can choose whether foreground is raised or recessed.

**Priority:** P1 - High
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `invert_depth` config option available
- [ ] When inverted, high depth becomes low height (and vice versa)
- [ ] Useful for lithophane-style output
- [ ] Default is non-inverted (closer = higher)

**Technical Notes:**
- Inversion: `height = max_height - height`
- Apply after normalization, before adding base

---

## Epic 5: OpenSCAD Generation

**Description:** Generate valid, parametric OpenSCAD code from processed height data.

**Business Value:** Core differentiator - produces editable, customizable 3D models rather than static meshes.

**Functional Requirements Covered:** FR13, FR14, FR15, FR16, FR17, FR18, FR19

---

### Story 5.1: Valid OpenSCAD Code Generation (FR13)

**As a** user,
**I want to** generate valid OpenSCAD code from my image,
**So that** I can open it in OpenSCAD and render a 3D model.

**Priority:** P0 - Critical
**Story Points:** 5

**Acceptance Criteria:**
- [ ] `OpenSCADGenerator` class exists in `src/image_to_scad/pipeline/scad_generator.py`
- [ ] `generate(height_data, config) -> str` returns valid OpenSCAD code
- [ ] Generated code compiles without errors in OpenSCAD 2021+
- [ ] Code creates a 3D surface from height data
- [ ] Surface is watertight (suitable for 3D printing)

**Technical Notes:**
- Use `surface()` function with height data file, or
- Generate `polyhedron()` directly, or
- Use `linear_extrude()` with height function
- Relief approach: grid of cubes/polyhedra at varying heights

---

### Story 5.2: Parametric Variables (FR14)

**As a** user,
**I want to** have adjustable parameters in the generated code,
**So that** I can customize the model without regenerating.

**Priority:** P0 - Critical
**Story Points:** 3

**Acceptance Criteria:**
- [ ] Generated code includes user-adjustable variables at the top
- [ ] Variables use meaningful names (e.g., `base_thickness`, `max_relief_height`)
- [ ] Variables have sensible default values from config
- [ ] Changing variables produces valid, different output
- [ ] Key parameters: base_thickness, max_height, model_width, model_height

**Technical Notes:**
- OpenSCAD variables at file top are customizable in GUI
- Use comment to mark "Customizer" section

---

### Story 5.3: Base Thickness Parameter (FR15)

**As a** user,
**I want to** specify the base thickness,
**So that** my model has a solid base suitable for printing.

**Priority:** P0 - Critical
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `base_thickness` parameter in config (default 2.0mm)
- [ ] Base thickness is minimum thickness everywhere
- [ ] Base adds to relief height (not subtracted from it)
- [ ] Variable exposed in generated OpenSCAD code

**Technical Notes:**
- Minimum recommended: 1mm for printability
- Default 2mm provides structural integrity

---

### Story 5.4: Maximum Height Parameter (FR16)

**As a** user,
**I want to** specify the maximum relief height,
**So that** I can control the depth of 3D effect.

**Priority:** P0 - Critical
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `max_height` parameter in config (default 15.0mm)
- [ ] Relief height ranges from 0 to max_height (above base)
- [ ] Total model thickness = base_thickness + max_height
- [ ] Variable exposed in generated OpenSCAD code

**Technical Notes:**
- Higher values = more dramatic 3D effect
- Consider print bed limits (typical max ~200mm)

---

### Story 5.5: Model Width/Scale Parameter (FR17)

**As a** user,
**I want to** specify the overall model width,
**So that** my print fits my needs and printer.

**Priority:** P0 - Critical
**Story Points:** 2

**Acceptance Criteria:**
- [ ] `model_width` parameter in config (default 100.0mm)
- [ ] Height calculated automatically from aspect ratio
- [ ] Both width and height exposed as variables in code
- [ ] Changing width scales entire model proportionally

**Technical Notes:**
- Preserve aspect ratio from original image
- height = width / aspect_ratio

---

### Story 5.6: Code Comments and Documentation (FR18)

**As a** user,
**I want to** have well-commented generated code,
**So that** I understand the parameters and can modify them.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Generated code includes header comment with generation info
- [ ] Each parameter variable has an explanatory comment
- [ ] Customizer section is clearly marked
- [ ] Code structure is explained in comments
- [ ] Units are documented (millimeters)

**Technical Notes:**
- Include generation timestamp and source image name
- OpenSCAD Customizer sections use special comment format

---

### Story 5.7: Relief/Lithophane Style Output (FR19)

**As a** user,
**I want to** generate relief-style 3D output,
**So that** I can create lithophanes and decorative reliefs.

**Priority:** P0 - Critical
**Story Points:** 5

**Acceptance Criteria:**
- [ ] Relief style generates a height-mapped surface
- [ ] Surface is suitable for backlit lithophane use
- [ ] Thin areas allow light through, thick areas block light
- [ ] Output style can be specified (MVP: relief only)
- [ ] Generated model is manifold and printable

**Technical Notes:**
- For lithophane: invert depth so dark=thick, light=thin
- Consider `surface()` with PNG heightmap or inline data

---

## Epic 6: STL Export

**Description:** Optionally render generated OpenSCAD code to STL using the OpenSCAD CLI.

**Business Value:** Completes the pipeline for users who want ready-to-print files.

**Functional Requirements Covered:** FR20, FR21, FR22

---

### Story 6.1: OpenSCAD CLI Invocation (FR20)

**As a** user,
**I want to** render my OpenSCAD file to STL automatically,
**So that** I can print without manually opening OpenSCAD.

**Priority:** P1 - High
**Story Points:** 3

**Acceptance Criteria:**
- [ ] `STLExporter` class exists in `src/image_to_scad/exporters/stl_exporter.py`
- [ ] `render(scad_path, stl_path) -> Path` invokes OpenSCAD CLI
- [ ] Uses `openscad -o output.stl input.scad` command
- [ ] Checks if OpenSCAD is installed and in PATH
- [ ] Provides helpful error if OpenSCAD not found

**Technical Notes:**
- Use `subprocess.run()` with timeout
- OpenSCAD command varies slightly by OS (check common paths)

---

### Story 6.2: Rendering Error Detection (FR21)

**As a** user,
**I want to** know if OpenSCAD rendering fails,
**So that** I can troubleshoot the issue.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] OpenSCAD stderr is captured and parsed
- [ ] Common errors are detected and reported clearly
- [ ] Timeout is implemented for long renders (default 5 minutes)
- [ ] Exit code is checked for success
- [ ] Raises `STLExportError` with details on failure

**Technical Notes:**
- OpenSCAD returns non-zero on error
- Capture and log stderr for debugging

---

### Story 6.3: Skip STL Rendering Option (FR22)

**As a** user,
**I want to** skip STL rendering and get only the .scad file,
**So that** I can render manually or edit the code first.

**Priority:** P1 - High
**Story Points:** 1

**Acceptance Criteria:**
- [ ] CLI flag `--no-stl` or `--scad-only` skips STL rendering
- [ ] Default behavior is configurable (MVP: .scad only by default)
- [ ] When STL is skipped, no OpenSCAD dependency required
- [ ] Output clearly indicates what was generated

**Technical Notes:**
- STL rendering can be slow; .scad-only is faster default
- Users can render in OpenSCAD GUI for preview

---

## Epic 7: Command Line Interface

**Description:** Provide a user-friendly CLI for all conversion operations.

**Business Value:** Primary user interface for MVP; enables scripting and easy adoption.

**Functional Requirements Covered:** FR23, FR24, FR25, FR26, FR27, FR28, FR29

---

### Story 7.1: Single Command Conversion (FR23)

**As a** user,
**I want to** convert an image with a single command,
**So that** the process is quick and simple.

**Priority:** P0 - Critical
**Story Points:** 3

**Acceptance Criteria:**
- [ ] `image-to-scad input.jpg` converts image with defaults
- [ ] Command is available after `pip install`
- [ ] Works with relative and absolute file paths
- [ ] Default output filename derived from input (input.jpg -> input.scad)
- [ ] Success message confirms output file location

**Technical Notes:**
- Entry point defined in pyproject.toml
- Main CLI function in `src/image_to_scad/cli.py`

---

### Story 7.2: Output Path Specification - SCAD (FR24)

**As a** user,
**I want to** specify where the .scad file is saved,
**So that** I can organize my outputs.

**Priority:** P0 - Critical
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `-o` or `--output` flag specifies .scad output path
- [ ] Path can be file or directory
- [ ] If directory, filename is derived from input
- [ ] Parent directories are created if needed
- [ ] Error if path is not writable

**Technical Notes:**
- Use `pathlib.Path` for path manipulation

---

### Story 7.3: Output Path Specification - STL (FR25)

**As a** user,
**I want to** specify where the .stl file is saved,
**So that** I can control STL output location.

**Priority:** P1 - High
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `--stl` flag specifies STL output path
- [ ] Implies STL rendering should occur
- [ ] Default STL path is same as .scad with .stl extension
- [ ] Path validation same as .scad output

**Technical Notes:**
- `--stl output.stl` enables STL and sets path
- `--stl` alone enables STL with default path

---

### Story 7.4: Progress Feedback (FR26)

**As a** user,
**I want to** see progress during conversion,
**So that** I know the tool is working.

**Priority:** P1 - High
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Each processing stage is announced
- [ ] Stages: "Loading image", "Estimating depth", "Analyzing depth", "Generating OpenSCAD"
- [ ] Optional: percentage or time estimates
- [ ] Progress can be suppressed with `--quiet` flag
- [ ] Final message confirms success with output paths

**Technical Notes:**
- Write to stderr for progress (stdout for data)
- Consider using `rich` library for nicer output (future)

---

### Story 7.5: Error Messages (FR27)

**As a** user,
**I want to** see clear error messages when something fails,
**So that** I can fix the problem.

**Priority:** P0 - Critical
**Story Points:** 2

**Acceptance Criteria:**
- [ ] Errors are written to stderr
- [ ] Error messages explain what went wrong
- [ ] Suggestions for fixing common issues are provided
- [ ] Non-zero exit code on error
- [ ] `--verbose` flag provides additional debug info

**Technical Notes:**
- Exit codes: 0=success, 1=user error, 2=internal error

---

### Story 7.6: Help Text (FR28)

**As a** user,
**I want to** view help explaining all options,
**So that** I can learn how to use the tool.

**Priority:** P0 - Critical
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `image-to-scad --help` shows usage information
- [ ] All options are documented with descriptions
- [ ] Default values are shown for each option
- [ ] Examples are included in help text
- [ ] Help text fits in standard terminal (80 columns)

**Technical Notes:**
- Use argparse with proper help strings
- Consider epilog for examples

---

### Story 7.7: Version Information (FR29)

**As a** user,
**I want to** view the tool version,
**So that** I can report issues accurately.

**Priority:** P1 - High
**Story Points:** 1

**Acceptance Criteria:**
- [ ] `image-to-scad --version` shows version number
- [ ] Version follows semantic versioning (MAJOR.MINOR.PATCH)
- [ ] Version is defined in one place (pyproject.toml or __version__)
- [ ] Optional: show Python version and key dependency versions

**Technical Notes:**
- Use `importlib.metadata` to read version from package

---

## Epic 8: Configuration Management

**Description:** Provide flexible configuration through command-line flags with sensible defaults.

**Business Value:** Enables power users to customize output while keeping simple use cases simple.

**Functional Requirements Covered:** FR30, FR31

---

### Story 8.1: Command-Line Parameter Overrides (FR30)

**As a** user,
**I want to** override default parameters via command-line flags,
**So that** I can customize output for specific needs.

**Priority:** P1 - High
**Story Points:** 3

**Acceptance Criteria:**
- [ ] `--base-thickness` sets base thickness in mm
- [ ] `--max-height` sets maximum relief height in mm
- [ ] `--width` sets model width in mm
- [ ] `--detail` sets detail level (0.5-2.0)
- [ ] `--smoothing/--no-smoothing` enables/disables smoothing
- [ ] `--invert` inverts depth interpretation
- [ ] Invalid values produce clear error messages

**Technical Notes:**
- Use argparse with type validation
- Flags map directly to ConversionConfig fields

---

### Story 8.2: Sensible Defaults (FR31)

**As a** user,
**I want to** have sensible defaults for all parameters,
**So that** I can get good results without configuration.

**Priority:** P0 - Critical
**Story Points:** 1

**Acceptance Criteria:**
- [ ] Default base_thickness: 2.0mm
- [ ] Default max_height: 15.0mm
- [ ] Default model_width: 100.0mm
- [ ] Default detail_level: 1.0
- [ ] Default smoothing: enabled
- [ ] Default invert_depth: false
- [ ] Defaults produce printable results for typical images

**Technical Notes:**
- Defaults defined in ConversionConfig dataclass
- Document rationale for each default value

---

## Implementation Priority

### Sprint 1: Foundation and Core Pipeline (Week 1-2)

| Story | Points | Dependencies |
|-------|--------|--------------|
| 1.1 Project Structure | 3 | None |
| 1.2 Configuration Dataclasses | 2 | 1.1 |
| 1.4 Exception Hierarchy | 2 | 1.1 |
| 2.1 Image File Loading | 2 | 1.1 |
| 2.2 Image Format Validation | 2 | 2.1 |
| 3.1 Model Loading | 5 | 1.1 |
| 3.2 Depth Map Generation | 3 | 3.1 |
| **Sprint Total** | **19** | |

### Sprint 2: Analysis and Generation (Week 3-4)

| Story | Points | Dependencies |
|-------|--------|--------------|
| 2.3 Automatic Image Resizing | 3 | 2.1 |
| 3.3 Depth Value Normalization | 2 | 3.2 |
| 4.1 Depth to Height Conversion | 3 | 3.3, 1.2 |
| 5.1 Valid OpenSCAD Generation | 5 | 4.1 |
| 5.2 Parametric Variables | 3 | 5.1 |
| 5.7 Relief Style Output | 5 | 5.1 |
| 1.3 Pipeline Orchestrator | 5 | 2.1, 3.2, 4.1, 5.1 |
| **Sprint Total** | **26** | |

### Sprint 3: CLI and Polish (Week 5-6)

| Story | Points | Dependencies |
|-------|--------|--------------|
| 7.1 Single Command Conversion | 3 | 1.3 |
| 7.2 Output Path - SCAD | 1 | 7.1 |
| 7.5 Error Messages | 2 | 7.1 |
| 7.6 Help Text | 1 | 7.1 |
| 8.1 CLI Parameter Overrides | 3 | 7.1, 1.2 |
| 8.2 Sensible Defaults | 1 | 1.2 |
| 5.3 Base Thickness Parameter | 1 | 5.1 |
| 5.4 Max Height Parameter | 1 | 5.1 |
| 5.5 Model Width Parameter | 2 | 5.1 |
| 5.6 Code Comments | 2 | 5.1 |
| **Sprint Total** | **17** | |

### Sprint 4: Enhancements and STL (Week 7-8)

| Story | Points | Dependencies |
|-------|--------|--------------|
| 1.5 Logging and Progress | 2 | 1.3 |
| 2.4 Detail Level Preference | 2 | 2.3 |
| 3.4 Model Caching | 2 | 3.1 |
| 4.2 Smoothing Filters | 3 | 4.1 |
| 4.3 Output Resolution Control | 2 | 4.1 |
| 4.4 Depth Inversion | 1 | 4.1 |
| 6.1 OpenSCAD CLI Invocation | 3 | 5.1 |
| 6.2 Rendering Error Detection | 2 | 6.1 |
| 6.3 Skip STL Option | 1 | 6.1 |
| 7.3 Output Path - STL | 1 | 6.1, 7.1 |
| 7.4 Progress Feedback | 2 | 7.1 |
| 7.7 Version Information | 1 | 7.1 |
| **Sprint Total** | **22** | |

---

## Definition of Done

A story is considered **Done** when:

1. **Code Complete**
   - [ ] Implementation matches acceptance criteria
   - [ ] Code follows PEP 8 style (verified by black/ruff)
   - [ ] Type hints on all public functions
   - [ ] Docstrings on all classes and public methods

2. **Tested**
   - [ ] Unit tests written and passing
   - [ ] Test coverage meets target (80%+ for component)
   - [ ] Integration tested with related components

3. **Documented**
   - [ ] Code is self-documenting with clear names
   - [ ] Complex logic has explanatory comments
   - [ ] Public API documented in docstrings

4. **Reviewed**
   - [ ] Code reviewed by at least one other developer
   - [ ] No critical issues or security concerns
   - [ ] Follows architectural decisions

---

## Appendix: Functional Requirements Traceability

| FR | Description | Epic | Story |
|----|-------------|------|-------|
| FR1 | Image file path input | E2 | 2.1 |
| FR2 | Validate input file | E2 | 2.2 |
| FR3 | Auto-resize images | E2 | 2.3 |
| FR4 | Detail level preference | E2 | 2.4 |
| FR5 | Load DPT model | E3 | 3.1 |
| FR6 | Generate depth map | E3 | 3.2 |
| FR7 | Normalize depth values | E3 | 3.3 |
| FR8 | Cache loaded model | E3 | 3.4 |
| FR9 | Convert depth to height | E4 | 4.1 |
| FR10 | Apply smoothing filters | E4 | 4.2 |
| FR11 | Detail level for output | E4 | 4.3 |
| FR12 | Invert depth | E4 | 4.4 |
| FR13 | Generate valid OpenSCAD | E5 | 5.1 |
| FR14 | Parametric variables | E5 | 5.2 |
| FR15 | Base thickness parameter | E5 | 5.3 |
| FR16 | Max height parameter | E5 | 5.4 |
| FR17 | Model width parameter | E5 | 5.5 |
| FR18 | Code comments | E5 | 5.6 |
| FR19 | Relief style output | E5 | 5.7 |
| FR20 | Invoke OpenSCAD CLI | E6 | 6.1 |
| FR21 | Detect rendering errors | E6 | 6.2 |
| FR22 | Skip STL rendering | E6 | 6.3 |
| FR23 | Single command conversion | E7 | 7.1 |
| FR24 | Output path for .scad | E7 | 7.2 |
| FR25 | Output path for .stl | E7 | 7.3 |
| FR26 | Progress feedback | E7 | 7.4 |
| FR27 | Clear error messages | E7 | 7.5 |
| FR28 | Help text | E7 | 7.6 |
| FR29 | Version information | E7 | 7.7 |
| FR30 | CLI parameter overrides | E8 | 8.1 |
| FR31 | Sensible defaults | E8 | 8.2 |

---

*Epics and Stories created following BMad Method v6.0 workflow*
*Reference: PRD, Architecture Document*
