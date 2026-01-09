# AI-Powered Image to OpenSCAD Converter
## Strategic Project Plan

---

## 1. Project Vision

**Goal:** Create an open-source tool that transforms 2D images into parametric, editable 3D models (OpenSCAD code) suitable for 3D printing, using AI-powered depth estimation.

**Key Differentiator:** Unlike basic heightmap-to-STL converters that produce static meshes, this tool generates intelligent, parametric OpenSCAD code that users can modify and customize.

---

## 2. Problem Statement

### Current Pain Points
- Basic image-to-STL tools produce low-quality, non-editable meshes
- Heightmap approaches lack true 3D understanding
- CAD software has steep learning curves
- Existing AI solutions are paid services or require API fees

### Solution Approach
- Use open-source AI depth estimation (Intel MiDaS/DPT)
- Generate parametric OpenSCAD code (not static meshes)
- Provide local processing (no cloud dependencies)
- Enable customization through parameters

---

## 3. Technical Architecture Overview

### Input â†’ Processing â†’ Output Flow

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Input     â”‚ --> â”‚ Depth Estimation â”‚ --> â”‚ Geometry        â”‚ --> â”‚   Output     â”‚
â”‚   Image     â”‚     â”‚ (MiDaS/DPT)      â”‚     â”‚ Analysis        â”‚     â”‚              â”‚
â”‚ (JPG/PNG)   â”‚     â”‚                  â”‚     â”‚                 â”‚     â”‚ - .scad file â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â”‚ - .stl file  â”‚
                                                    â”‚                â”‚ - preview    â”‚
                                                    v                â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                            â”‚ OpenSCAD Code   â”‚
                                            â”‚ Generator       â”‚
                                            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| Depth Estimator | Extract 3D depth from 2D image | Intel DPT/MiDaS (open source) |
| Depth Analyzer | Extract geometric features | OpenCV, NumPy, SciPy |
| OpenSCAD Generator | Create parametric code | Python templating |
| STL Exporter | Render final mesh | OpenSCAD CLI |
| Preview System | Visual feedback | Matplotlib, Open3D |

---

## 4. Open Source Models Available

### Primary Option: Intel DPT/MiDaS
| Model | Parameters | Speed | Quality | License |
|-------|------------|-------|---------|---------|
| dpt-swinv2-tiny-256 | ~25M | Fast | Good | MIT |
| dpt-hybrid-midas | ~123M | Medium | Better | MIT |
| dpt-large | ~343M | Slow | Best | MIT |

### Alternative: Depth Anything V2
| Model | Parameters | License | Notes |
|-------|------------|---------|-------|
| Small | 24.8M | Apache 2.0 | Commercial OK |
| Base | 97.5M | CC-BY-NC-4.0 | Non-commercial |
| Large | 335.3M | CC-BY-NC-4.0 | Non-commercial |

### Input Requirements
- **Format:** RGB images (JPG, PNG, BMP, TIFF)
- **Resolution:** Any (resized internally to model requirements)
- **Content:** Any subject - objects, scenes, people, products
- **No text input** - image-only models

---

## 5. Feature Roadmap

### Phase 1: Core Pipeline (MVP)
- [ ] Image input handling (single image)
- [ ] Depth estimation using Intel DPT
- [ ] Basic depth map analysis
- [ ] Simple OpenSCAD code generation
- [ ] STL export via OpenSCAD CLI
- [ ] Command-line interface

### Phase 2: Enhanced Analysis
- [ ] Multi-object detection and separation
- [ ] Edge detection and boundary refinement
- [ ] Shape classification (cylinders, cubes, spheres)
- [ ] Depth layer segmentation
- [ ] Configurable parameters (height, scale, detail)

### Phase 3: Smart OpenSCAD Generation
- [ ] Parametric module generation
- [ ] CSG operations (union, difference, intersection)
- [ ] Variable declarations for customization
- [ ] Multiple output styles (relief, full 3D, layered)
- [ ] Support for hollowing/infill patterns

### Phase 4: User Experience
- [ ] Web interface (Gradio or Streamlit)
- [ ] Real-time preview
- [ ] Parameter adjustment UI
- [ ] Batch processing
- [ ] Project save/load

### Phase 5: Advanced Features (Future)
- [ ] Text-to-image integration (generate source image from description)
- [ ] Multi-view 3D reconstruction
- [ ] Texture/color preservation
- [ ] Direct slicer integration

---

## 6. Technical Specifications

### Supported Input Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tif, .tiff)
- WebP (.webp)

### Output Formats
- OpenSCAD source code (.scad)
- STL mesh (.stl)
- Depth map visualization (.png)
- Analysis report (.json)

### Dependencies
```
torch >= 2.0.0
transformers >= 4.35.0
opencv-python >= 4.8.0
numpy >= 1.24.0
Pillow >= 10.0.0
open3d >= 0.18.0
matplotlib >= 3.7.0
scipy >= 1.11.0
timm >= 0.9.0
```

### External Requirements
- OpenSCAD (for STL rendering)
- Python 3.10+
- CUDA (optional, for GPU acceleration)

---

## 7. OpenSCAD Generation Strategy

### Approach 1: Relief/Lithophane Style
- Convert depth map to surface height
- Best for: photos, artwork, logos
- Output: Single surface with varying height

### Approach 2: Object Extraction
- Detect distinct objects in depth map
- Generate separate primitives for each
- Best for: product photos, isolated objects
- Output: Multiple combined shapes

### Approach 3: Layered Contours
- Slice depth map into discrete levels
- Stack 2D profiles at different heights
- Best for: terrain, complex shapes
- Output: Layer-based construction

### Parametric Variables to Expose
```openscad
// User-adjustable parameters
base_thickness = 2;      // mm
max_height = 15;         // mm
model_width = 100;       // mm
detail_level = 1;        // 0.5 to 2.0
smoothing = true;        // Enable smoothing
invert_depth = false;    // Flip relief direction
```

---

## 8. Quality Considerations

### Depth Estimation Limitations
- Relative depth only (not metric/absolute)
- May struggle with: reflective surfaces, transparent objects, repetitive patterns
- Best results with: good lighting, clear subjects, moderate complexity

### Recommended Image Guidelines
- Clear subject with distinct foreground/background
- Good contrast and lighting
- Minimal motion blur
- Resolution: 512px - 2048px recommended

### Post-Processing Options
- Smoothing/denoising depth maps
- Edge enhancement
- Hole filling
- Resolution adjustment

---

## 9. Use Cases

| Use Case | Input Example | Output Style |
|----------|---------------|--------------|
| Photo lithophane | Portrait photo | Relief surface |
| Product prototype | Product image | Extracted 3D shape |
| Logo/emblem | Company logo | Extruded relief |
| Terrain model | Landscape photo | Layered contours |
| Art piece | Artwork image | Stylized relief |
| Custom figurine | Character image | Multi-object |

---

## 10. Development Milestones

### Milestone 1: Proof of Concept
- Single script demonstrating full pipeline
- Hardcoded parameters
- Basic OpenSCAD output
- **Deliverable:** Working prototype

### Milestone 2: Modular Architecture
- Separated components (estimator, analyzer, generator)
- Configuration file support
- Error handling and logging
- **Deliverable:** Refactored codebase

### Milestone 3: CLI Tool
- Argument parsing
- Multiple input/output options
- Progress feedback
- **Deliverable:** Installable CLI tool

### Milestone 4: Documentation & Testing
- User documentation
- API documentation
- Unit tests
- Example gallery
- **Deliverable:** Release-ready package

---

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Depth quality insufficient | Medium | High | Offer multiple models, preprocessing options |
| OpenSCAD complexity | Low | Medium | Start simple, iterate |
| Performance issues | Medium | Medium | GPU support, batch processing |
| Model licensing changes | Low | High | Pin versions, document alternatives |

---

## 12. Success Criteria

### Technical
- [ ] Process image in under 30 seconds (CPU)
- [ ] Generate valid OpenSCAD code for 90%+ of test images
- [ ] Produce printable STL files

### User Experience
- [ ] Single command to convert image to STL
- [ ] Clear error messages
- [ ] Customizable output parameters

### Quality
- [ ] Recognizable 3D representation of input
- [ ] Parametric code that can be modified
- [ ] Clean, readable generated code

---

## 13. Next Steps

### Immediate Actions
1. Finalize technology choices (confirm MiDaS/DPT model selection)
2. Create detailed technical specifications
3. Build proof-of-concept prototype
4. Test with sample images

### Documents to Generate
- [ ] **PRD (Product Requirements Document):** Detailed feature requirements
- [ ] **HLD (High-Level Design):** Architecture and component design
- [ ] **API Specification:** Interface definitions
- [ ] **Test Plan:** Quality assurance strategy

---

## 14. Questions for Further Refinement

### Technical Decisions
- Preferred depth model size (speed vs. quality tradeoff)?
- Target platform (local only, or web deployment)?
- GPU requirement (optional or required)?

### Feature Priorities
- Which output style is primary (relief, extracted objects, layered)?
- Importance of preview/visualization?
- Need for batch processing?

### Integration
- Standalone tool or library for integration?
- MCP server for Claude Code integration?
- Plugin for other tools (Blender, FreeCAD)?

---

*This plan serves as the foundation for developing detailed PRD and HLD documents with your input and direction.*