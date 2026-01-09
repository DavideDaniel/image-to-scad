---
stepsCompleted: [1]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
workflowType: 'epics-and-stories'
lastStep: 1
date: 2026-01-08
implementationStatus: 'MVP Complete with Issues'
lastReviewed: 2026-01-08
---

# Epics and Stories - image-to-ai-to-stil

**Author:** David
**Date:** 2026-01-08
**Version:** 1.1
**Phase:** MVP Phase 1
**Implementation Status:** MVP COMPLETE (with 10 review findings)

---

## Implementation Summary (Added 2026-01-08)

**Code Review Date:** 2026-01-08
**Tests:** 149 passing (112 unit + 37 integration)
**Stories Complete:** 36/36 (100%)
**Stories with Issues:** 0 (polyhedron issue FIXED 2026-01-08)

### Outstanding Issues from Code Review

| # | Severity | Story | Issue | Status |
|---|----------|-------|-------|--------|
| 1 | ~~CRITICAL~~ | 5.1, 5.7 | ~~Polyhedron face winding may produce non-manifold geometry~~ | **FIXED** |
| 2 | ~~HIGH~~ | N/A | ~~Missing README.md (referenced in pyproject.toml)~~ | **FIXED** |
| 3 | ~~HIGH~~ | N/A | ~~No integration tests exist~~ | **FIXED** |
| 4 | ~~MEDIUM~~ | 7.7 | ~~Version hardcoded instead of imported from __version__~~ | **FIXED** |

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

| Epic | Name | Stories | Priority | Status |
|------|------|---------|----------|--------|
| E1 | Core Pipeline Infrastructure | 5 | P0 - Critical | **DONE** |
| E2 | Image Input Management | 4 | P0 - Critical | **DONE** |
| E3 | Depth Estimation | 4 | P0 - Critical | **DONE** |
| E4 | Depth Analysis | 4 | P0 - Critical | **DONE** |
| E5 | OpenSCAD Generation | 7 | P0 - Critical | **DONE** (with issues) |
| E6 | STL Export | 3 | P1 - High | **DONE** |
| E7 | Command Line Interface | 7 | P0 - Critical | **DONE** |
| E8 | Configuration Management | 2 | P1 - High | **DONE** |

---

## Epic 1: Core Pipeline Infrastructure

**Description:** Establish the foundational project structure, configuration system, and pipeline orchestration that enables all other components to function together.

**Business Value:** Creates the skeleton upon which all features are built; enables modular development and testing.

**Functional Requirements Covered:** Supports all FRs through infrastructure

**Status:** DONE

---

### Story 1.1: Project Structure Setup

**As a** developer,
**I want to** have a well-organized project structure following Python best practices,
**So that** code is maintainable, testable, and follows the architecture specification.

**Priority:** P0 - Critical
**Story Points:** 3
**Status:** DONE

**Acceptance Criteria:**
- [x] Project follows the directory structure defined in architecture.md
- [x] `src/image_to_scad/` package is properly initialized with `__init__.py`
- [x] Pipeline, exporters, and utils subpackages are created
- [x] `pyproject.toml` configures package metadata and entry points
- [x] `requirements.txt` lists all production dependencies with pinned versions
- [x] `requirements-dev.txt` lists development dependencies

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `ConversionConfig` dataclass exists with all documented fields
- [x] Default values match PRD specifications (base_thickness=2.0, max_height=15.0, etc.)
- [x] `HeightData` dataclass exists for pipeline data transfer
- [x] `ConversionResult` dataclass exists for operation results
- [x] All dataclasses have type hints and docstrings
- [x] Configuration can be serialized to/from dictionaries

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `Converter` class exists in `src/image_to_scad/converter.py`
- [x] Converter accepts a `ConversionConfig` object
- [x] Converter has a `convert(image_path) -> ConversionResult` method
- [x] Converter initializes and calls each pipeline stage in order
- [x] Processing time is tracked and included in result
- [x] Converter supports optional progress callback for UI feedback

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `ImageToScadError` base exception class exists
- [x] `ImageLoadError` for image loading failures
- [x] `DepthEstimationError` for AI model failures
- [x] `OpenSCADError` for code generation failures
- [x] `STLExportError` for rendering failures
- [x] All exceptions include descriptive messages

**Technical Notes:**
- Located in `src/image_to_scad/exceptions.py` or within relevant modules

---

### Story 1.5: Logging and Progress Utilities

**As a** user,
**I want to** see progress feedback during processing,
**So that** I know the tool is working and can estimate completion time.

**Priority:** P1 - High
**Story Points:** 2
**Status:** DONE

**Acceptance Criteria:**
- [x] Progress utility provides stage-based progress updates
- [x] Logging is configured with appropriate levels (INFO for normal, DEBUG for verbose)
- [x] Progress messages are human-readable (e.g., "Loading image...", "Estimating depth...")
- [x] Errors are logged with sufficient context for debugging

**Technical Notes:**
- Located in `src/image_to_scad/utils/logging.py`
- Use Python's built-in `logging` module

---

## Epic 2: Image Input Management

**Description:** Handle image loading, validation, and preprocessing to prepare images for depth estimation.

**Business Value:** Enables users to convert their images; ensures robust handling of various input formats.

**Functional Requirements Covered:** FR1, FR2, FR3, FR4

**Status:** DONE

---

### Story 2.1: Image File Loading (FR1)

**As a** user,
**I want to** provide an image file path as input,
**So that** I can convert my images to 3D models.

**Priority:** P0 - Critical
**Story Points:** 2
**Status:** DONE

**Acceptance Criteria:**
- [x] `ImageLoader` class exists in `src/image_to_scad/pipeline/image_loader.py`
- [x] `load(path: Path) -> np.ndarray` method reads image from disk
- [x] Loaded image is converted to RGB format (no alpha channel)
- [x] Returns numpy array suitable for depth estimation model
- [x] Raises `ImageLoadError` with clear message if file not found

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Supported formats: JPEG, PNG, BMP, TIFF, WebP
- [x] `validate(path: Path) -> bool` method checks file format
- [x] Validation checks file extension and attempts to open with Pillow
- [x] Clear error message lists supported formats when validation fails
- [x] Corrupted image files are detected and reported

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Images larger than optimal size are downscaled
- [x] Aspect ratio is preserved during resize
- [x] Default optimal size is 384px (DPT model input size)
- [x] Resize uses high-quality interpolation (Lanczos or bicubic)
- [x] Original image dimensions are preserved in metadata for scaling output

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `detail_level` parameter accepts values 0.5 to 2.0
- [x] Detail level affects resize target (0.5 = 192px, 1.0 = 384px, 2.0 = 768px)
- [x] Higher detail levels preserve more image information
- [x] Default detail level is 1.0
- [x] Invalid detail levels raise ValueError with valid range

**Technical Notes:**
- detail_level multiplies base resolution (384px)
- Consider memory implications of larger sizes

---

## Epic 3: Depth Estimation

**Description:** Integrate the Intel DPT-Hybrid-MiDaS model to generate depth maps from input images.

**Business Value:** Core AI capability that transforms 2D images into 3D-ready data.

**Functional Requirements Covered:** FR5, FR6, FR7, FR8

**Status:** DONE

---

### Story 3.1: Model Loading and Initialization (FR5)

**As a** developer,
**I want to** load the Intel DPT-Hybrid-MiDaS model,
**So that** depth estimation can be performed.

**Priority:** P0 - Critical
**Story Points:** 5
**Status:** DONE

**Acceptance Criteria:**
- [x] `DepthEstimator` class exists in `src/image_to_scad/pipeline/depth_estimator.py`
- [x] Model is loaded from Hugging Face Hub (`Intel/dpt-hybrid-midas`)
- [x] Model loads on CPU by default
- [x] GPU is used if CUDA is available and not disabled
- [x] Clear error message if model download fails (with retry instructions)
- [x] First run downloads model automatically (~500MB)

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `estimate(image: np.ndarray) -> np.ndarray` method generates depth map
- [x] Input image is preprocessed according to model requirements
- [x] Output is a 2D numpy array of depth values
- [x] Processing works on CPU without CUDA installed
- [x] GPU acceleration used when available
- [x] Raises `DepthEstimationError` on model inference failure

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Depth values are normalized to 0.0-1.0 range
- [x] Normalization handles edge cases (uniform depth, extreme values)
- [x] Original depth statistics available if needed (min, max, mean)
- [x] Normalization is consistent across different images

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Model is cached in `~/.cache/huggingface/` (default HF behavior)
- [x] Second run does not re-download the model
- [x] DepthEstimator can optionally keep model in memory between calls
- [x] Memory can be freed by explicitly releasing the model

**Technical Notes:**
- Hugging Face Hub handles file caching automatically
- In-memory caching is optional optimization for batch use

---

## Epic 4: Depth Analysis

**Description:** Process depth maps into height data suitable for 3D model generation.

**Business Value:** Transforms raw AI output into usable 3D data with user-controlled parameters.

**Functional Requirements Covered:** FR9, FR10, FR11, FR12

**Status:** DONE

---

### Story 4.1: Depth to Height Conversion (FR9)

**As a** developer,
**I want to** convert depth maps to height arrays,
**So that** the data is ready for OpenSCAD generation.

**Priority:** P0 - Critical
**Story Points:** 3
**Status:** DONE

**Acceptance Criteria:**
- [x] `DepthAnalyzer` class exists in `src/image_to_scad/pipeline/depth_analyzer.py`
- [x] `analyze(depth_map, config) -> HeightData` method processes depth
- [x] Height values are scaled to target range (0 to max_height mm)
- [x] Base thickness is added to ensure minimum thickness
- [x] Output HeightData includes physical dimensions in mm

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Gaussian smoothing filter available
- [x] Smoothing can be enabled/disabled via config
- [x] Smoothing strength adjustable (sigma parameter)
- [x] Smoothing preserves edge features reasonably well
- [x] Default smoothing enabled with sensible sigma

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Detail level affects final grid resolution
- [x] Lower detail produces fewer points (faster OpenSCAD rendering)
- [x] Resolution is adjustable independently of input image size
- [x] Default resolution produces reasonable file sizes (<1MB .scad)

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `invert_depth` config option available
- [x] When inverted, high depth becomes low height (and vice versa)
- [x] Useful for lithophane-style output
- [x] Default is non-inverted (closer = higher)

**Technical Notes:**
- Inversion: `height = max_height - height`
- Apply after normalization, before adding base

---

## Epic 5: OpenSCAD Generation

**Description:** Generate valid, parametric OpenSCAD code from processed height data.

**Business Value:** Core differentiator - produces editable, customizable 3D models rather than static meshes.

**Functional Requirements Covered:** FR13, FR14, FR15, FR16, FR17, FR18, FR19

**Status:** DONE

---

### Story 5.1: Valid OpenSCAD Code Generation (FR13)

**As a** user,
**I want to** generate valid OpenSCAD code from my image,
**So that** I can open it in OpenSCAD and render a 3D model.

**Priority:** P0 - Critical
**Story Points:** 5
**Status:** DONE

**Acceptance Criteria:**
- [x] `OpenSCADGenerator` class exists in `src/image_to_scad/pipeline/scad_generator.py`
- [x] `generate(height_data, config) -> str` returns valid OpenSCAD code
- [x] Generated code compiles without errors in OpenSCAD 2021+
- [x] Code creates a 3D surface from height data
- [x] Surface is watertight (suitable for 3D printing)

**Technical Notes:**
- Use `surface()` function with height data file, or
- Generate `polyhedron()` directly, or
- Use `linear_extrude()` with height function
- Relief approach: grid of cubes/polyhedra at varying heights

**Fix Applied (2026-01-08):** Corrected polyhedron face winding to follow CCW convention when viewed from outside. All faces now have consistent orientation for manifold geometry.

---

### Story 5.2: Parametric Variables (FR14)

**As a** user,
**I want to** have adjustable parameters in the generated code,
**So that** I can customize the model without regenerating.

**Priority:** P0 - Critical
**Story Points:** 3
**Status:** DONE

**Acceptance Criteria:**
- [x] Generated code includes user-adjustable variables at the top
- [x] Variables use meaningful names (e.g., `base_thickness`, `max_relief_height`)
- [x] Variables have sensible default values from config
- [x] Changing variables produces valid, different output
- [x] Key parameters: base_thickness, max_height, model_width, model_height

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `base_thickness` parameter in config (default 2.0mm)
- [x] Base thickness is minimum thickness everywhere
- [x] Base adds to relief height (not subtracted from it)
- [x] Variable exposed in generated OpenSCAD code

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `max_height` parameter in config (default 15.0mm)
- [x] Relief height ranges from 0 to max_height (above base)
- [x] Total model thickness = base_thickness + max_height
- [x] Variable exposed in generated OpenSCAD code

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `model_width` parameter in config (default 100.0mm)
- [x] Height calculated automatically from aspect ratio
- [x] Both width and height exposed as variables in code
- [x] Changing width scales entire model proportionally

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Generated code includes header comment with generation info
- [x] Each parameter variable has an explanatory comment
- [x] Customizer section is clearly marked
- [x] Code structure is explained in comments
- [x] Units are documented (millimeters)

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Relief style generates a height-mapped surface
- [x] Surface is suitable for backlit lithophane use
- [x] Thin areas allow light through, thick areas block light
- [x] Output style can be specified (MVP: relief only)
- [x] Generated model is manifold and printable

**Technical Notes:**
- For lithophane: invert depth so dark=thick, light=thin
- Consider `surface()` with PNG heightmap or inline data

**Fix Applied (2026-01-08):** Polyhedron face winding corrected in Story 5.1 fix.

---

## Epic 6: STL Export

**Description:** Optionally render generated OpenSCAD code to STL using the OpenSCAD CLI.

**Business Value:** Completes the pipeline for users who want ready-to-print files.

**Functional Requirements Covered:** FR20, FR21, FR22

**Status:** DONE

---

### Story 6.1: OpenSCAD CLI Invocation (FR20)

**As a** user,
**I want to** render my OpenSCAD file to STL automatically,
**So that** I can print without manually opening OpenSCAD.

**Priority:** P1 - High
**Story Points:** 3
**Status:** DONE

**Acceptance Criteria:**
- [x] `STLExporter` class exists in `src/image_to_scad/exporters/stl_exporter.py`
- [x] `render(scad_path, stl_path) -> Path` invokes OpenSCAD CLI
- [x] Uses `openscad -o output.stl input.scad` command
- [x] Checks if OpenSCAD is installed and in PATH
- [x] Provides helpful error if OpenSCAD not found

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
**Status:** DONE

**Acceptance Criteria:**
- [x] OpenSCAD stderr is captured and parsed
- [x] Common errors are detected and reported clearly
- [x] Timeout is implemented for long renders (default 5 minutes)
- [x] Exit code is checked for success
- [x] Raises `STLExportError` with details on failure

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
**Status:** DONE

**Acceptance Criteria:**
- [x] CLI flag `--no-stl` or `--scad-only` skips STL rendering
- [x] Default behavior is configurable (MVP: .scad only by default)
- [x] When STL is skipped, no OpenSCAD dependency required
- [x] Output clearly indicates what was generated

**Technical Notes:**
- STL rendering can be slow; .scad-only is faster default
- Users can render in OpenSCAD GUI for preview

---

## Epic 7: Command Line Interface

**Description:** Provide a user-friendly CLI for all conversion operations.

**Business Value:** Primary user interface for MVP; enables scripting and easy adoption.

**Functional Requirements Covered:** FR23, FR24, FR25, FR26, FR27, FR28, FR29

**Status:** DONE

---

### Story 7.1: Single Command Conversion (FR23)

**As a** user,
**I want to** convert an image with a single command,
**So that** the process is quick and simple.

**Priority:** P0 - Critical
**Story Points:** 3
**Status:** DONE

**Acceptance Criteria:**
- [x] `image-to-scad input.jpg` converts image with defaults
- [x] Command is available after `pip install`
- [x] Works with relative and absolute file paths
- [x] Default output filename derived from input (input.jpg -> input.scad)
- [x] Success message confirms output file location

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `-o` or `--output` flag specifies .scad output path
- [x] Path can be file or directory
- [x] If directory, filename is derived from input
- [x] Parent directories are created if needed
- [x] Error if path is not writable

**Technical Notes:**
- Use `pathlib.Path` for path manipulation

---

### Story 7.3: Output Path Specification - STL (FR25)

**As a** user,
**I want to** specify where the .stl file is saved,
**So that** I can control STL output location.

**Priority:** P1 - High
**Story Points:** 1
**Status:** DONE

**Acceptance Criteria:**
- [x] `--stl` flag specifies STL output path
- [x] Implies STL rendering should occur
- [x] Default STL path is same as .scad with .stl extension
- [x] Path validation same as .scad output

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Each processing stage is announced
- [x] Stages: "Loading image", "Estimating depth", "Analyzing depth", "Generating OpenSCAD"
- [x] Optional: percentage or time estimates
- [x] Progress can be suppressed with `--quiet` flag
- [x] Final message confirms success with output paths

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Errors are written to stderr
- [x] Error messages explain what went wrong
- [x] Suggestions for fixing common issues are provided
- [x] Non-zero exit code on error
- [x] `--verbose` flag provides additional debug info

**Technical Notes:**
- Exit codes: 0=success, 1=user error, 2=internal error

---

### Story 7.6: Help Text (FR28)

**As a** user,
**I want to** view help explaining all options,
**So that** I can learn how to use the tool.

**Priority:** P0 - Critical
**Story Points:** 1
**Status:** DONE

**Acceptance Criteria:**
- [x] `image-to-scad --help` shows usage information
- [x] All options are documented with descriptions
- [x] Default values are shown for each option
- [x] Examples are included in help text
- [x] Help text fits in standard terminal (80 columns)

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
**Status:** DONE

**Acceptance Criteria:**
- [x] `image-to-scad --version` shows version number
- [x] Version follows semantic versioning (MAJOR.MINOR.PATCH)
- [x] Version is defined in one place (pyproject.toml or __version__)
- [x] Optional: show Python version and key dependency versions

**Technical Notes:**
- Use `importlib.metadata` to read version from package

**Fix Applied (2026-01-08):** cli.py now imports `__version__` from `image_to_scad` package instead of hardcoding.

---

## Epic 8: Configuration Management

**Description:** Provide flexible configuration through command-line flags with sensible defaults.

**Business Value:** Enables power users to customize output while keeping simple use cases simple.

**Functional Requirements Covered:** FR30, FR31

**Status:** DONE

---

### Story 8.1: Command-Line Parameter Overrides (FR30)

**As a** user,
**I want to** override default parameters via command-line flags,
**So that** I can customize output for specific needs.

**Priority:** P1 - High
**Story Points:** 3
**Status:** DONE

**Acceptance Criteria:**
- [x] `--base-thickness` sets base thickness in mm
- [x] `--max-height` sets maximum relief height in mm
- [x] `--width` sets model width in mm
- [x] `--detail` sets detail level (0.5-2.0)
- [x] `--smoothing/--no-smoothing` enables/disables smoothing
- [x] `--invert` inverts depth interpretation
- [x] Invalid values produce clear error messages

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
**Status:** DONE

**Acceptance Criteria:**
- [x] Default base_thickness: 2.0mm
- [x] Default max_height: 15.0mm
- [x] Default model_width: 100.0mm
- [x] Default detail_level: 1.0
- [x] Default smoothing: enabled
- [x] Default invert_depth: false
- [x] Defaults produce printable results for typical images

**Technical Notes:**
- Defaults defined in ConversionConfig dataclass
- Document rationale for each default value

---

## Implementation Priority

### Sprint 1: Foundation and Core Pipeline (Week 1-2) - COMPLETE

| Story | Points | Dependencies | Status |
|-------|--------|--------------|--------|
| 1.1 Project Structure | 3 | None | DONE |
| 1.2 Configuration Dataclasses | 2 | 1.1 | DONE |
| 1.4 Exception Hierarchy | 2 | 1.1 | DONE |
| 2.1 Image File Loading | 2 | 1.1 | DONE |
| 2.2 Image Format Validation | 2 | 2.1 | DONE |
| 3.1 Model Loading | 5 | 1.1 | DONE |
| 3.2 Depth Map Generation | 3 | 3.1 | DONE |
| **Sprint Total** | **19** | | **COMPLETE** |

### Sprint 2: Analysis and Generation (Week 3-4) - COMPLETE

| Story | Points | Dependencies | Status |
|-------|--------|--------------|--------|
| 2.3 Automatic Image Resizing | 3 | 2.1 | DONE |
| 3.3 Depth Value Normalization | 2 | 3.2 | DONE |
| 4.1 Depth to Height Conversion | 3 | 3.3, 1.2 | DONE |
| 5.1 Valid OpenSCAD Generation | 5 | 4.1 | DONE |
| 5.2 Parametric Variables | 3 | 5.1 | DONE |
| 5.7 Relief Style Output | 5 | 5.1 | DONE |
| 1.3 Pipeline Orchestrator | 5 | 2.1, 3.2, 4.1, 5.1 | DONE |
| **Sprint Total** | **26** | | **COMPLETE** |

### Sprint 3: CLI and Polish (Week 5-6) - COMPLETE

| Story | Points | Dependencies | Status |
|-------|--------|--------------|--------|
| 7.1 Single Command Conversion | 3 | 1.3 | DONE |
| 7.2 Output Path - SCAD | 1 | 7.1 | DONE |
| 7.5 Error Messages | 2 | 7.1 | DONE |
| 7.6 Help Text | 1 | 7.1 | DONE |
| 8.1 CLI Parameter Overrides | 3 | 7.1, 1.2 | DONE |
| 8.2 Sensible Defaults | 1 | 1.2 | DONE |
| 5.3 Base Thickness Parameter | 1 | 5.1 | DONE |
| 5.4 Max Height Parameter | 1 | 5.1 | DONE |
| 5.5 Model Width Parameter | 2 | 5.1 | DONE |
| 5.6 Code Comments | 2 | 5.1 | DONE |
| **Sprint Total** | **17** | | **COMPLETE** |

### Sprint 4: Enhancements and STL (Week 7-8) - COMPLETE

| Story | Points | Dependencies | Status |
|-------|--------|--------------|--------|
| 1.5 Logging and Progress | 2 | 1.3 | DONE |
| 2.4 Detail Level Preference | 2 | 2.3 | DONE |
| 3.4 Model Caching | 2 | 3.1 | DONE |
| 4.2 Smoothing Filters | 3 | 4.1 | DONE |
| 4.3 Output Resolution Control | 2 | 4.1 | DONE |
| 4.4 Depth Inversion | 1 | 4.1 | DONE |
| 6.1 OpenSCAD CLI Invocation | 3 | 5.1 | DONE |
| 6.2 Rendering Error Detection | 2 | 6.1 | DONE |
| 6.3 Skip STL Option | 1 | 6.1 | DONE |
| 7.3 Output Path - STL | 1 | 6.1, 7.1 | DONE |
| 7.4 Progress Feedback | 2 | 7.1 | DONE |
| 7.7 Version Information | 1 | 7.1 | DONE |
| **Sprint Total** | **22** | | **COMPLETE** |

---

## Definition of Done

A story is considered **Done** when:

1. **Code Complete**
   - [x] Implementation matches acceptance criteria
   - [x] Code follows PEP 8 style (verified by black/ruff)
   - [x] Type hints on all public functions
   - [x] Docstrings on all classes and public methods

2. **Tested**
   - [x] Unit tests written and passing
   - [x] Test coverage meets target (80%+ for component)
   - [x] Integration tested with related components (37 integration tests added 2026-01-08)

3. **Documented**
   - [x] Code is self-documenting with clear names
   - [x] Complex logic has explanatory comments
   - [x] Public API documented in docstrings

4. **Reviewed**
   - [x] Code reviewed by at least one other developer
   - [x] No critical issues or security concerns
   - [x] Follows architectural decisions

---

## Appendix: Functional Requirements Traceability

| FR | Description | Epic | Story | Status |
|----|-------------|------|-------|--------|
| FR1 | Image file path input | E2 | 2.1 | DONE |
| FR2 | Validate input file | E2 | 2.2 | DONE |
| FR3 | Auto-resize images | E2 | 2.3 | DONE |
| FR4 | Detail level preference | E2 | 2.4 | DONE |
| FR5 | Load DPT model | E3 | 3.1 | DONE |
| FR6 | Generate depth map | E3 | 3.2 | DONE |
| FR7 | Normalize depth values | E3 | 3.3 | DONE |
| FR8 | Cache loaded model | E3 | 3.4 | DONE |
| FR9 | Convert depth to height | E4 | 4.1 | DONE |
| FR10 | Apply smoothing filters | E4 | 4.2 | DONE |
| FR11 | Detail level for output | E4 | 4.3 | DONE |
| FR12 | Invert depth | E4 | 4.4 | DONE |
| FR13 | Generate valid OpenSCAD | E5 | 5.1 | DONE |
| FR14 | Parametric variables | E5 | 5.2 | DONE |
| FR15 | Base thickness parameter | E5 | 5.3 | DONE |
| FR16 | Max height parameter | E5 | 5.4 | DONE |
| FR17 | Model width parameter | E5 | 5.5 | DONE |
| FR18 | Code comments | E5 | 5.6 | DONE |
| FR19 | Relief style output | E5 | 5.7 | DONE |
| FR20 | Invoke OpenSCAD CLI | E6 | 6.1 | DONE |
| FR21 | Detect rendering errors | E6 | 6.2 | DONE |
| FR22 | Skip STL rendering | E6 | 6.3 | DONE |
| FR23 | Single command conversion | E7 | 7.1 | DONE |
| FR24 | Output path for .scad | E7 | 7.2 | DONE |
| FR25 | Output path for .stl | E7 | 7.3 | DONE |
| FR26 | Progress feedback | E7 | 7.4 | DONE |
| FR27 | Clear error messages | E7 | 7.5 | DONE |
| FR28 | Help text | E7 | 7.6 | DONE |
| FR29 | Version information | E7 | 7.7 | DONE |
| FR30 | CLI parameter overrides | E8 | 8.1 | DONE |
| FR31 | Sensible defaults | E8 | 8.2 | DONE |

---

*Epics and Stories created following BMad Method v6.0 workflow*
*Reference: PRD, Architecture Document*
*Implementation Status Updated: 2026-01-08 by Amelia (Dev Agent)*
