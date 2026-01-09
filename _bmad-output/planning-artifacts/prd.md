---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-image-to-ai-to-stil-2026-01-08.md
  - docs/PROJECT_PLAN.md
workflowType: 'prd'
lastStep: 11
date: 2026-01-08
---

# Product Requirements Document - image-to-ai-to-stil

**Author:** David
**Date:** 2026-01-08
**Version:** 1.0

---

## Executive Summary

**image-to-ai-to-stil** is an open-source AI-powered tool that transforms 2D images into parametric, editable 3D models (OpenSCAD code) suitable for 3D printing.

### Vision Statement
Democratize 3D model creation by enabling anyone to convert images into customizable, printable 3D models without CAD expertise or cloud dependencies.

### Core Value Proposition
Unlike existing solutions that produce static, non-editable meshes, this tool generates intelligent OpenSCAD code with adjustable parameters, enabling users to customize their 3D prints after generation.

### Key Differentiators
1. **Parametric Output** - Generated code is customizable, not static
2. **Local Processing** - No cloud, no API fees, no privacy concerns
3. **AI-Powered** - True depth understanding via Intel MiDaS/DPT
4. **Open Source** - MIT-licensed, community-driven

---

## Success Criteria

### Primary Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Conversion Success Rate | >90% | Valid OpenSCAD output from test images |
| Processing Time (CPU) | <30 seconds | End-to-end image to .scad |
| STL Printability | 100% | Generated STLs pass mesh validation |
| User Time to First Print | <5 minutes | New user installation to STL |

### Quality Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Visual Fidelity | Recognizable | User survey: "Does output represent input?" |
| Code Readability | Self-documenting | Generated code has meaningful variable names |
| Parameter Clarity | Intuitive | Users understand parameters without docs |

### Adoption Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| GitHub Stars (6 months) | 500+ | GitHub metrics |
| Community Contributions | 10+ PRs | GitHub contributions |
| Documentation Coverage | 100% features | Doc audit |

---

## User Journeys

### Journey 1: Maya the Maker - Photo to Lithophane

**Scenario:** Maya wants to create a 3D-printed lithophane from a family photo as a gift.

**Steps:**
1. Maya discovers image-to-ai-to-stil through Reddit's r/3Dprinting
2. Installs via `pip install image-to-scad` (2 minutes)
3. Downloads the AI model on first run (automatic, 1 minute)
4. Runs `image-to-scad family-photo.jpg --style relief`
5. Opens generated .scad file in OpenSCAD
6. Adjusts `max_height` parameter from 15mm to 10mm for her printer
7. Renders STL and slices in her usual slicer
8. Prints the lithophane successfully
9. **Aha Moment:** "I can tweak the code to change the result!"

**Success Outcome:** Maya creates personalized gifts and shares on social media

### Journey 2: Chris the Artist - Artwork to Sculpture

**Scenario:** Chris wants to turn digital illustrations into physical relief art.

**Steps:**
1. Chris finds the tool mentioned in a digital art forum
2. Exports artwork as high-resolution PNG
3. Runs conversion with default settings to test
4. Opens .scad file and modifies `detail_level` parameter
5. Experiments with `invert_depth` for different artistic effects
6. Renders multiple STL variations
7. Prints selected version for art exhibition
8. **Aha Moment:** "The parametric code lets me iterate quickly"

**Success Outcome:** Chris incorporates 3D prints into art practice

### Journey 3: Eva the Educator - Teaching 3D Concepts

**Scenario:** Eva wants to teach students about 3D modeling using familiar images.

**Steps:**
1. Eva searches for accessible 3D modeling tools
2. Installs tool on classroom computers
3. Has students draw simple shapes on paper and photograph them
4. Students convert their drawings to 3D models
5. Students modify parameters to understand depth/height relationships
6. Class prints models on school's 3D printer
7. **Aha Moment:** "Students understand 3D through hands-on experimentation"

**Success Outcome:** Eva uses tool as standard part of curriculum

---

## Domain Requirements

### 3D Printing Domain

- Generated STL files must be manifold (watertight meshes)
- Models must have configurable base thickness (minimum 1mm recommended)
- Output must be compatible with standard slicer software (Cura, PrusaSlicer, etc.)
- File sizes should be reasonable for typical 3D printing workflows

### Image Processing Domain

- Support standard image formats (JPEG, PNG, BMP, TIFF, WebP)
- Handle various image resolutions (512px to 4096px input range)
- Graceful handling of problematic images (low contrast, blur)
- No image data transmitted externally (local processing only)

### CAD/OpenSCAD Domain

- Generated code must compile without errors in OpenSCAD 2021+
- Code should be human-readable with meaningful variable names
- Parameters should use standard units (millimeters)
- Generated code should follow OpenSCAD best practices

---

## Functional Requirements

### Image Input Management

- FR1: User can provide an image file path as input to the conversion process
- FR2: System can validate that input file exists and is a supported image format
- FR3: System can automatically resize images to optimal dimensions for processing
- FR4: User can specify input image resolution/detail level preference

### Depth Estimation

- FR5: System can load and initialize the Intel DPT-Hybrid-MiDaS depth estimation model
- FR6: System can generate a depth map from any supported input image
- FR7: System can normalize depth values to a consistent range
- FR8: System can cache the loaded model to avoid re-initialization

### Depth Analysis

- FR9: System can convert depth map to height array suitable for 3D generation
- FR10: System can apply smoothing filters to reduce noise in depth data
- FR11: User can specify detail level to control output resolution
- FR12: System can invert depth interpretation (foreground vs background)

### OpenSCAD Generation

- FR13: System can generate valid OpenSCAD code from processed depth data
- FR14: Generated code includes parametric variables for customization
- FR15: User can specify base thickness for generated models
- FR16: User can specify maximum height for relief features
- FR17: User can specify overall model width/scale
- FR18: Generated code includes comments explaining parameters
- FR19: System can generate relief/lithophane style output

### STL Export

- FR20: System can invoke OpenSCAD CLI to render STL from generated code
- FR21: System can detect and report OpenSCAD rendering errors
- FR22: User can skip STL rendering and receive only .scad output

### Command Line Interface

- FR23: User can convert image to OpenSCAD with single command
- FR24: User can specify output file path for generated .scad file
- FR25: User can specify output file path for rendered .stl file
- FR26: System displays progress feedback during processing
- FR27: System displays clear error messages for failure conditions
- FR28: User can view help text explaining available options
- FR29: User can view version information

### Configuration

- FR30: User can override default parameters via command-line flags
- FR31: System uses sensible defaults when parameters not specified

---

## Non-Functional Requirements

### Performance

- NFR1: Depth estimation completes in <20 seconds on CPU (Intel i5 or equivalent)
- NFR2: OpenSCAD code generation completes in <5 seconds
- NFR3: Total end-to-end processing <30 seconds (excluding STL rendering)
- NFR4: Memory usage stays below 4GB during processing
- NFR5: GPU acceleration available as optional enhancement (target <5s total)

### Reliability

- NFR6: System gracefully handles malformed or unsupported input images
- NFR7: System provides meaningful error messages for all failure modes
- NFR8: Generated OpenSCAD code compiles successfully >95% of the time
- NFR9: Generated STL files are valid manifold meshes >95% of the time

### Usability

- NFR10: Installation requires <5 commands for typical Python user
- NFR11: First successful conversion achievable in <5 minutes from install
- NFR12: All command-line options documented in --help output
- NFR13: README provides clear quickstart instructions

### Maintainability

- NFR14: Codebase follows PEP 8 style guidelines
- NFR15: Core modules have unit test coverage >80%
- NFR16: Public API has docstring documentation
- NFR17: Dependencies pinned to specific versions

### Portability

- NFR18: Runs on macOS, Linux, and Windows
- NFR19: Works with Python 3.9, 3.10, 3.11, 3.12
- NFR20: CPU-only mode works without CUDA installation
- NFR21: GPU mode works with CUDA 11.x and 12.x

### Security

- NFR22: No data transmitted to external services
- NFR23: No telemetry or usage tracking
- NFR24: Model downloaded from official Hugging Face repository only

---

## Technical Constraints

### Required Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Runtime |
| PyTorch | 2.0+ | Deep learning framework |
| Transformers | 4.35+ | Model loading |
| OpenCV | 4.8+ | Image processing |
| NumPy | 1.24+ | Array operations |
| Pillow | 10.0+ | Image I/O |

### External Requirements

| Requirement | Purpose | Notes |
|-------------|---------|-------|
| OpenSCAD | STL rendering | Must be installed and in PATH |
| Internet | Model download | One-time download only |

### Model Requirements

| Model | Size | License |
|-------|------|---------|
| Intel DPT-Hybrid-MiDaS | ~500MB | MIT |

---

## Out of Scope (MVP)

The following features are explicitly NOT included in the MVP:

- Web interface (Gradio/Streamlit)
- Multi-object detection and separation
- Shape classification (cylinders, cubes, spheres)
- CSG operations (union, difference, intersection)
- Real-time preview
- Batch processing of multiple images
- Text-to-image integration
- Multi-view 3D reconstruction
- Texture/color preservation
- Direct slicer integration

These may be considered for future phases.

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Depth estimation quality insufficient for some images | Medium | High | Document image guidelines, offer multiple models |
| OpenSCAD generation too slow for large/detailed models | Medium | Medium | Configurable detail levels, optimization |
| Model licensing changes | Low | High | Pin model version, document alternatives |
| OpenSCAD CLI compatibility issues | Low | Medium | Test on multiple OS versions |

---

## Glossary

| Term | Definition |
|------|------------|
| Depth Map | 2D image where pixel values represent distance from camera |
| DPT | Dense Prediction Transformer - architecture for depth estimation |
| Lithophane | 3D-printed translucent panel that reveals image when backlit |
| MiDaS | "Mixing Datasets for Zero-shot Cross-dataset Transfer" depth model |
| OpenSCAD | Open-source script-based 3D CAD modeler |
| Parametric | Design that can be modified by changing parameter values |
| Relief | Sculptural technique where forms project from flat background |
| STL | STereoLithography file format for 3D printing |

---

*PRD created following BMad Method v6.0 workflow*
*Reference: Product Brief, PROJECT_PLAN.md*
