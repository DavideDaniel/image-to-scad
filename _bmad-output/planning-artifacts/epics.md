---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
---

# image-to-ai-to-stil - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for image-to-ai-to-stil, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**Image Input Management**
- FR1: User can provide an image file path as input to the conversion process
- FR2: System can validate that input file exists and is a supported image format
- FR3: System can automatically resize images to optimal dimensions for processing
- FR4: User can specify input image resolution/detail level preference

**Depth Estimation**
- FR5: System can load and initialize the Intel DPT-Hybrid-MiDaS depth estimation model
- FR6: System can generate a depth map from any supported input image
- FR7: System can normalize depth values to a consistent range
- FR8: System can cache the loaded model to avoid re-initialization

**Depth Analysis**
- FR9: System can convert depth map to height array suitable for 3D generation
- FR10: System can apply smoothing filters to reduce noise in depth data
- FR11: User can specify detail level to control output resolution
- FR12: System can invert depth interpretation (foreground vs background)

**OpenSCAD Generation**
- FR13: System can generate valid OpenSCAD code from processed depth data
- FR14: Generated code includes parametric variables for customization
- FR15: User can specify base thickness for generated models
- FR16: User can specify maximum height for relief features
- FR17: User can specify overall model width/scale
- FR18: Generated code includes comments explaining parameters
- FR19: System can generate relief/lithophane style output

**STL Export**
- FR20: System can invoke OpenSCAD CLI to render STL from generated code
- FR21: System can detect and report OpenSCAD rendering errors
- FR22: User can skip STL rendering and receive only .scad output

**Command Line Interface**
- FR23: User can convert image to OpenSCAD with single command
- FR24: User can specify output file path for generated .scad file
- FR25: User can specify output file path for rendered .stl file
- FR26: System displays progress feedback during processing
- FR27: System displays clear error messages for failure conditions
- FR28: User can view help text explaining available options
- FR29: User can view version information

**Configuration**
- FR30: User can override default parameters via command-line flags
- FR31: System uses sensible defaults when parameters not specified

### NonFunctional Requirements

**Performance**
- NFR1: Depth estimation completes in <20 seconds on CPU (Intel i5 or equivalent)
- NFR2: OpenSCAD code generation completes in <5 seconds
- NFR3: Total end-to-end processing <30 seconds (excluding STL rendering)
- NFR4: Memory usage stays below 4GB during processing
- NFR5: GPU acceleration available as optional enhancement (target <5s total)

**Reliability**
- NFR6: System gracefully handles malformed or unsupported input images
- NFR7: System provides meaningful error messages for all failure modes
- NFR8: Generated OpenSCAD code compiles successfully >95% of the time
- NFR9: Generated STL files are valid manifold meshes >95% of the time

**Usability**
- NFR10: Installation requires <5 commands for typical Python user
- NFR11: First successful conversion achievable in <5 minutes from install
- NFR12: All command-line options documented in --help output
- NFR13: README provides clear quickstart instructions

**Maintainability**
- NFR14: Codebase follows PEP 8 style guidelines
- NFR15: Core modules have unit test coverage >80%
- NFR16: Public API has docstring documentation
- NFR17: Dependencies pinned to specific versions

**Portability**
- NFR18: Runs on macOS, Linux, and Windows
- NFR19: Works with Python 3.9, 3.10, 3.11, 3.12
- NFR20: CPU-only mode works without CUDA installation
- NFR21: GPU mode works with CUDA 11.x and 12.x

**Security**
- NFR22: No data transmitted to external services
- NFR23: No telemetry or usage tracking
- NFR24: Model downloaded from official Hugging Face repository only

### Additional Requirements

**From Architecture - Project Setup**
- Use Python 3.9+ as primary implementation language
- Follow exact project structure defined in Architecture (src/image_to_scad/ layout)
- Use pyproject.toml for PEP 517 package configuration
- Set up GitHub Actions CI pipeline

**From Architecture - Design Patterns**
- Implement modular pipeline architecture with independent, composable modules
- Use Python dataclasses for all configuration objects
- Define Protocol classes for pipeline stage interfaces
- Implement custom exception hierarchy (ImageToScadError base class)

**From Architecture - Data Models**
- Implement ConversionConfig dataclass with all parameters
- Implement HeightData dataclass for pipeline communication
- Implement ConversionResult dataclass for output

**From Architecture - Dependencies**
- PyTorch 2.0+, Transformers 4.35+, Pillow 10.0+, OpenCV 4.8+, NumPy 1.24+
- Use huggingface_hub for model downloading/caching
- Development tools: pytest, black, mypy, ruff

**From Architecture - Testing**
- Use pytest for all test levels
- Create test fixtures with small images (64x64, 128x128)
- Maintain golden output files for regression testing
- Target 90% coverage for pipeline stages

**From Architecture - Code Style**
- PEP 8 formatting with black
- Type hints on all public functions
- Docstrings on all classes and public methods
- Maximum line length: 100 characters

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 1 | Image file path input |
| FR2 | Epic 1 | File validation |
| FR3 | Epic 1 | Auto-resize images |
| FR4 | Epic 2 | Resolution/detail preference |
| FR5 | Epic 1 | Load DPT-MiDaS model |
| FR6 | Epic 1 | Generate depth map |
| FR7 | Epic 1 | Normalize depth values |
| FR8 | Epic 1 | Cache loaded model |
| FR9 | Epic 1 | Convert depth to height array |
| FR10 | Epic 2 | Smoothing filters |
| FR11 | Epic 2 | Detail level control |
| FR12 | Epic 2 | Invert depth option |
| FR13 | Epic 1 | Generate valid OpenSCAD |
| FR14 | Epic 2 | Parametric variables |
| FR15 | Epic 2 | Base thickness parameter |
| FR16 | Epic 2 | Max height parameter |
| FR17 | Epic 2 | Model width/scale |
| FR18 | Epic 2 | Code comments |
| FR19 | Epic 1 | Relief/lithophane style |
| FR20 | Epic 4 | OpenSCAD CLI for STL |
| FR21 | Epic 4 | Detect rendering errors |
| FR22 | Epic 4 | Skip STL option |
| FR23 | Epic 1 | Single command conversion |
| FR24 | Epic 3 | .scad output path |
| FR25 | Epic 3 | .stl output path |
| FR26 | Epic 3 | Progress feedback |
| FR27 | Epic 3 | Error messages |
| FR28 | Epic 3 | Help text |
| FR29 | Epic 3 | Version info |
| FR30 | Epic 2 | Override defaults via flags |
| FR31 | Epic 1 | Sensible defaults |

## Epic List

### Epic 1: Image to OpenSCAD Core
Users can convert any image to a basic OpenSCAD relief model with a single command. This epic delivers the fundamental value proposition - turning an image into parametric 3D code.

**FRs covered:** FR1, FR2, FR3, FR5, FR6, FR7, FR8, FR9, FR13, FR19, FR23, FR31

---

### Epic 2: Customizable 3D Output
Users can fine-tune their 3D models with parameters like height, thickness, detail level, and depth inversion. This enables artistic experimentation and educational exploration.

**FRs covered:** FR4, FR10, FR11, FR12, FR14, FR15, FR16, FR17, FR18, FR30

---

### Epic 3: Complete CLI Experience
Users have a polished command-line experience with help documentation, progress feedback, custom output paths, and version info. New users can discover features and track conversion progress.

**FRs covered:** FR24, FR25, FR26, FR27, FR28, FR29

---

### Epic 4: STL Export & Printing
Users can export print-ready STL files directly, completing the full image-to-print workflow. The tool validates meshes and reports any rendering errors.

**FRs covered:** FR20, FR21, FR22

---

## Epic 1: Image to OpenSCAD Core

Users can convert any image to a basic OpenSCAD relief model with a single command. This epic delivers the fundamental value proposition - turning an image into parametric 3D code.

### Story 1.1: Project Setup and Package Structure

As a **developer**,
I want **the project initialized with the correct package structure, dependencies, and configuration**,
So that **I have a solid foundation to build the image-to-scad functionality**.

**Acceptance Criteria:**

**Given** I have cloned the repository
**When** I run `pip install -e .`
**Then** the package installs successfully with all dependencies
**And** the following structure exists:
- `src/image_to_scad/__init__.py`
- `src/image_to_scad/cli.py`
- `src/image_to_scad/converter.py`
- `src/image_to_scad/config.py`
- `src/image_to_scad/pipeline/` directory
- `src/image_to_scad/utils/` directory

**Given** the package is installed
**When** I run `image-to-scad --version`
**Then** the version number is displayed

**Given** pyproject.toml exists
**When** I inspect the dependencies
**Then** PyTorch, Transformers, Pillow, OpenCV, NumPy are specified with minimum versions

---

### Story 1.2: Image Loading and Validation

As a **user**,
I want **to provide an image file and have it validated and prepared for processing**,
So that **I get clear feedback if my image is unsupported before processing begins**.

**Acceptance Criteria:**

**Given** I provide a valid image path (JPEG, PNG, BMP, TIFF, or WebP)
**When** the ImageLoader processes it
**Then** the image is loaded as an RGB numpy array
**And** the image is resized to optimal dimensions (max 512px on longest side for MVP)

**Given** I provide a path to a non-existent file
**When** the ImageLoader attempts to load it
**Then** a FileNotFoundError is raised with the file path in the message

**Given** I provide a path to an unsupported file type (e.g., .txt, .pdf)
**When** the ImageLoader attempts to load it
**Then** an ImageLoadError is raised with supported formats listed

**Given** I provide a valid image smaller than 64x64 pixels
**When** the ImageLoader processes it
**Then** a warning is logged about potentially low quality output

---

### Story 1.3: Depth Estimation Pipeline

As a **user**,
I want **my image converted to a depth map using AI**,
So that **the system understands the 3D structure of my image**.

**Acceptance Criteria:**

**Given** I have a loaded RGB image array
**When** the DepthEstimator processes it
**Then** a depth map (2D numpy array) is returned with normalized values (0.0 to 1.0)

**Given** I run depth estimation for the first time
**When** the model is not cached locally
**Then** the Intel DPT-Hybrid-MiDaS model downloads from Hugging Face
**And** progress is indicated during download

**Given** I run depth estimation after the model is cached
**When** the DepthEstimator initializes
**Then** the cached model loads without re-downloading
**And** initialization completes in <5 seconds

**Given** depth estimation is running on CPU
**When** processing a 512x512 image
**Then** estimation completes in <20 seconds (NFR1)

**Given** the model is loaded once
**When** I process multiple images in sequence
**Then** the model remains cached in memory and is reused

---

### Story 1.4: Depth to Height Conversion

As a **user**,
I want **the depth map converted to height values**,
So that **the 3D relief has appropriate physical dimensions**.

**Acceptance Criteria:**

**Given** I have a normalized depth map
**When** the DepthAnalyzer processes it with default config
**Then** a HeightData object is returned containing:
- heights: 2D numpy array with values in millimeters
- width_mm: physical width (default 100mm)
- height_mm: physical height (proportional)
- resolution: grid dimensions

**Given** default conversion configuration
**When** height conversion completes
**Then** height values range from base_thickness (2mm) to max_height (15mm)

**Given** a depth map with varying values
**When** converted to heights
**Then** darker depth values become lower heights (closer to base)
**And** lighter depth values become higher heights (raised relief)

---

### Story 1.5: OpenSCAD Code Generation

As a **user**,
I want **valid OpenSCAD code generated from my height data**,
So that **I can open it in OpenSCAD and render a 3D model**.

**Acceptance Criteria:**

**Given** I have HeightData from the analyzer
**When** the OpenSCADGenerator processes it
**Then** valid OpenSCAD code is returned as a string
**And** the code compiles without errors in OpenSCAD 2021+

**Given** generated OpenSCAD code
**When** I inspect the output
**Then** it contains parametric variables at the top:
- `base_thickness`
- `max_height`
- `model_width`
**And** each parameter has a comment explaining its purpose

**Given** generated OpenSCAD code
**When** rendered in OpenSCAD
**Then** it produces a relief/lithophane style 3D model
**And** the model has a solid base with raised surface features

**Given** the generator processes height data
**When** code generation completes
**Then** it takes <5 seconds (NFR2)

---

### Story 1.6: Basic CLI Command

As a **user**,
I want **to convert an image with a single command**,
So that **I can quickly generate OpenSCAD code without complex setup**.

**Acceptance Criteria:**

**Given** I have installed image-to-scad
**When** I run `image-to-scad input.jpg`
**Then** a file `input.scad` is created in the current directory
**And** the file contains valid OpenSCAD code

**Given** I run `image-to-scad photo.png`
**When** the conversion completes successfully
**Then** a success message is displayed with the output file path

**Given** I run `image-to-scad nonexistent.jpg`
**When** the file does not exist
**Then** an error message is displayed: "Error: File not found: nonexistent.jpg"
**And** the exit code is non-zero

**Given** I run `image-to-scad` with no arguments
**When** the command executes
**Then** a usage message is displayed explaining required arguments

---

## Epic 2: Customizable 3D Output

Users can fine-tune their 3D models with parameters like height, thickness, detail level, and depth inversion. This enables artistic experimentation and educational exploration.

### Story 2.1: Depth Analysis Enhancements

As a **user**,
I want **to control how the depth map is processed with smoothing, detail level, and inversion options**,
So that **I can fine-tune the 3D output to match my artistic vision**.

**Acceptance Criteria:**

**Given** I have a depth map with noise artifacts
**When** smoothing is enabled (default: True)
**Then** a Gaussian smoothing filter is applied to reduce noise
**And** the output has smoother height transitions

**Given** I want a more detailed output
**When** I set detail_level to 2.0
**Then** the output resolution is doubled (more height samples)
**And** finer details from the original image are preserved

**Given** I want a faster, coarser output
**When** I set detail_level to 0.5
**Then** the output resolution is halved
**And** processing is faster with fewer height samples

**Given** my image has the subject in the foreground appearing darker in depth
**When** I enable invert_depth
**Then** the depth interpretation is flipped
**And** foreground subjects become raised instead of recessed

**Given** default settings
**When** I process an image without specifying options
**Then** smoothing is enabled, detail_level is 1.0, invert_depth is False

---

### Story 2.2: Full Parametric Code Generation

As a **user**,
I want **the generated OpenSCAD code to include all customizable parameters with clear documentation**,
So that **I can easily modify my 3D model after generation without re-running the tool**.

**Acceptance Criteria:**

**Given** generated OpenSCAD code
**When** I open it in a text editor
**Then** I see a parameters section at the top with:
- `base_thickness` (mm) - minimum model thickness
- `max_height` (mm) - maximum relief height
- `model_width` (mm) - overall model width
- `detail_level` - resolution multiplier
- `smoothing` - whether smoothing was applied
- `invert_depth` - whether depth was inverted

**Given** each parameter in the generated code
**When** I read its comment
**Then** I understand what the parameter controls
**And** I see the valid range or expected values

**Given** I modify `max_height` from 15 to 25 in the .scad file
**When** I re-render in OpenSCAD
**Then** the relief features are taller
**And** no other changes are needed to the code

**Given** I modify `model_width` from 100 to 150 in the .scad file
**When** I re-render in OpenSCAD
**Then** the entire model scales proportionally wider
**And** the aspect ratio is preserved

**Given** generated code includes parameter documentation
**When** I review the header comments
**Then** I see the original image filename
**And** I see the generation timestamp
**And** I see the tool version used

---

### Story 2.3: CLI Parameter Flags

As a **user**,
I want **to specify all conversion parameters via command-line flags**,
So that **I can customize my output without editing code afterward**.

**Acceptance Criteria:**

**Given** I want a thicker base
**When** I run `image-to-scad input.jpg --base-thickness 5`
**Then** the generated model has a 5mm base thickness

**Given** I want taller relief features
**When** I run `image-to-scad input.jpg --max-height 25`
**Then** the generated model has relief up to 25mm height

**Given** I want a smaller model
**When** I run `image-to-scad input.jpg --width 50`
**Then** the generated model is 50mm wide

**Given** I want higher detail output
**When** I run `image-to-scad input.jpg --detail 2.0`
**Then** the output has doubled resolution

**Given** I want to disable smoothing
**When** I run `image-to-scad input.jpg --no-smoothing`
**Then** no smoothing filter is applied to the depth data

**Given** I want inverted depth
**When** I run `image-to-scad input.jpg --invert`
**Then** the depth interpretation is inverted

**Given** I want to combine multiple options
**When** I run `image-to-scad input.jpg --width 80 --max-height 20 --detail 1.5 --invert`
**Then** all specified parameters are applied correctly

**Given** I specify an invalid parameter value (e.g., --detail -1)
**When** the command executes
**Then** an error message explains the valid range
**And** the exit code is non-zero

---

## Epic 3: Complete CLI Experience

Users have a polished command-line experience with help documentation, progress feedback, custom output paths, and version info. New users can discover features and track conversion progress.

### Story 3.1: Custom Output Paths

As a **user**,
I want **to specify where my output files are saved**,
So that **I can organize my generated files in my preferred directory structure**.

**Acceptance Criteria:**

**Given** I want to save the .scad file to a specific location
**When** I run `image-to-scad input.jpg -o /path/to/output.scad`
**Then** the generated OpenSCAD file is saved to `/path/to/output.scad`

**Given** I want to save the .scad file with a custom name
**When** I run `image-to-scad input.jpg -o my-model.scad`
**Then** the file `my-model.scad` is created in the current directory

**Given** I specify an output path for STL (for Epic 4)
**When** I run `image-to-scad input.jpg --stl-output /path/to/model.stl`
**Then** the STL output path is stored in configuration for later use
**And** a message indicates STL export requires Epic 4 functionality

**Given** I specify an output directory that doesn't exist
**When** the command executes
**Then** the parent directories are created automatically
**And** the file is saved successfully

**Given** I specify an output path without write permissions
**When** the command attempts to save
**Then** an error message explains the permission issue
**And** the exit code is non-zero

**Given** I don't specify an output path
**When** I run `image-to-scad input.jpg`
**Then** the output is saved as `input.scad` in the current directory (default behavior from Epic 1)

---

### Story 3.2: Progress Feedback and Error Messages

As a **user**,
I want **to see progress during conversion and receive clear error messages when things go wrong**,
So that **I know the tool is working and can troubleshoot issues easily**.

**Acceptance Criteria:**

**Given** I start a conversion
**When** the tool begins processing
**Then** I see progress indicators for each stage:
- "Loading image..."
- "Estimating depth..." (with percentage if possible)
- "Generating OpenSCAD code..."
- "Saving output..."

**Given** the depth model is downloading for the first time
**When** download is in progress
**Then** I see download progress (percentage or progress bar)
**And** I see the estimated file size

**Given** processing completes successfully
**When** the output is saved
**Then** I see a summary message:
- Output file path
- Processing time
- Model dimensions

**Given** an error occurs during image loading
**When** the error is displayed
**Then** the message includes:
- What went wrong (e.g., "Unsupported image format")
- The file that caused the error
- Suggested resolution (e.g., "Supported formats: JPEG, PNG, BMP, TIFF, WebP")

**Given** an error occurs during depth estimation
**When** the error is displayed
**Then** the message includes:
- The stage that failed
- Potential causes (e.g., "Insufficient memory")
- Suggested resolution (e.g., "Try reducing image size or closing other applications")

**Given** I want minimal output
**When** I run `image-to-scad input.jpg --quiet`
**Then** only errors are displayed
**And** successful completion shows only the output path

---

### Story 3.3: Help and Version Information

As a **user**,
I want **comprehensive help documentation and version information**,
So that **I can discover all available options and report issues accurately**.

**Acceptance Criteria:**

**Given** I want to see all available options
**When** I run `image-to-scad --help`
**Then** I see:
- Usage synopsis
- Description of the tool
- All available flags with descriptions
- Default values for each option
- Example commands

**Given** the --help output
**When** I review the options section
**Then** each option includes:
- Short flag (e.g., `-o`)
- Long flag (e.g., `--output`)
- Description of what it does
- Default value (if applicable)
- Valid range (if applicable)

**Given** I want to check the installed version
**When** I run `image-to-scad --version`
**Then** I see the version number in format `image-to-scad X.Y.Z`

**Given** I need to report a bug
**When** I run `image-to-scad --version`
**Then** I also see:
- Python version
- Key dependency versions (PyTorch, Transformers)
- Platform information

**Given** I run an invalid command
**When** the command fails
**Then** the error message suggests running `--help` for usage information

**Given** the help output
**When** I look for examples
**Then** I see at least 3 example commands:
- Basic usage: `image-to-scad photo.jpg`
- With output path: `image-to-scad photo.jpg -o model.scad`
- With parameters: `image-to-scad photo.jpg --width 80 --max-height 20`

---

## Epic 4: STL Export & Printing

Users can export print-ready STL files directly, completing the full image-to-print workflow. The tool validates meshes and reports any rendering errors.

### Story 4.1: OpenSCAD CLI Integration

As a **user**,
I want **the tool to automatically render my .scad file to STL using OpenSCAD**,
So that **I can go directly from image to printable file without manual steps**.

**Acceptance Criteria:**

**Given** I have OpenSCAD installed and in my PATH
**When** I run `image-to-scad input.jpg --render-stl`
**Then** the tool generates `input.scad` AND `input.stl`
**And** both files are saved to the output directory

**Given** OpenSCAD is installed
**When** STL rendering begins
**Then** I see progress: "Rendering STL with OpenSCAD..."
**And** the rendering completes successfully

**Given** I specify a custom STL output path
**When** I run `image-to-scad input.jpg --render-stl --stl-output model.stl`
**Then** the STL is saved to `model.stl`

**Given** OpenSCAD is NOT installed or not in PATH
**When** I run with `--render-stl`
**Then** an error message is displayed: "OpenSCAD not found. Please install OpenSCAD and ensure it's in your PATH."
**And** the .scad file is still generated successfully
**And** the exit code indicates partial success

**Given** STL rendering is requested
**When** the OpenSCAD CLI is invoked
**Then** the quiet flag (`-q`) is used to suppress OpenSCAD's verbose output
**And** only relevant progress/error information is shown to the user

---

### Story 4.2: STL Export with Error Handling

As a **user**,
I want **clear feedback when STL rendering fails and the option to skip STL generation**,
So that **I can troubleshoot issues or choose to render manually in OpenSCAD**.

**Acceptance Criteria:**

**Given** OpenSCAD encounters an error during rendering
**When** the rendering fails
**Then** the error message includes:
- The OpenSCAD error output
- The .scad file path (so user can debug manually)
- Suggestion: "Try opening the .scad file in OpenSCAD GUI to diagnose"

**Given** OpenSCAD times out (takes >5 minutes)
**When** the timeout is reached
**Then** the rendering is cancelled
**And** an error message suggests reducing detail level or model complexity

**Given** I only want the .scad file
**When** I run `image-to-scad input.jpg` (without --render-stl)
**Then** only the .scad file is generated
**And** no STL rendering is attempted (default behavior)

**Given** I explicitly want to skip STL even when it might be default
**When** I run `image-to-scad input.jpg --no-stl`
**Then** STL rendering is skipped regardless of other settings

**Given** STL rendering completes successfully
**When** the output is saved
**Then** I see confirmation with the STL file path
**And** I see the STL file size

**Given** the generated .scad has syntax errors (edge case)
**When** OpenSCAD attempts to render
**Then** the syntax error is captured and displayed
**And** the error message identifies this as an internal tool error
**And** the user is asked to report the issue

