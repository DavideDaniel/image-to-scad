---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - docs/PROJECT_PLAN.md
  - docs/SETUP.md
date: 2026-01-08
author: David
---

# Product Brief: image-to-ai-to-stil

## Executive Summary

**image-to-ai-to-stil** is an open-source AI-powered tool that transforms 2D images into parametric, editable 3D models using OpenSCAD code. Unlike existing solutions that produce static, non-editable meshes, this tool generates intelligent, customizable OpenSCAD code suitable for 3D printing.

The project leverages Intel's open-source MiDaS/DPT depth estimation models to extract 3D information from single 2D images, enabling local processing without cloud dependencies or API fees.

---

## Core Vision

### Problem Statement

Creating 3D printable models from 2D images is currently painful:
- Basic image-to-STL tools produce low-quality, non-editable meshes
- Heightmap approaches lack true 3D understanding
- CAD software has steep learning curves
- Existing AI solutions require paid services or API fees
- Results are static and cannot be customized without starting over

### Problem Impact

- **Hobbyists and makers** cannot easily convert artwork, logos, or photos into 3D prints
- **Small businesses** cannot afford enterprise CAD solutions for custom merchandise
- **Educators** lack accessible tools for teaching 3D design concepts
- **Artists** cannot bridge their 2D work into the physical 3D printing world

### Why Existing Solutions Fall Short

| Solution | Limitation |
|----------|------------|
| Basic heightmap converters | No depth understanding, just brightness-to-height |
| Online image-to-3D services | Require payment, upload privacy concerns, no customization |
| Professional CAD software | Steep learning curve, expensive licenses |
| AI-based services (commercial) | API costs, cloud dependency, non-parametric output |

### Proposed Solution

An open-source Python tool that:
1. **Accepts any image** (JPG, PNG, BMP, TIFF, WebP)
2. **Estimates depth** using Intel DPT/MiDaS AI models
3. **Analyzes geometry** to understand shapes and surfaces
4. **Generates parametric OpenSCAD code** with customizable variables
5. **Exports STL files** ready for 3D printing
6. **Runs locally** - no cloud, no API fees, no privacy concerns

### Key Differentiators

1. **Parametric Output** - Generated OpenSCAD code can be modified after generation
2. **Open Source** - MIT-licensed, community-driven
3. **Local Processing** - No cloud dependencies or data privacy concerns
4. **AI-Powered Depth** - True depth understanding, not just heightmap conversion
5. **Multiple Output Styles** - Relief/lithophane, object extraction, layered contours
6. **Customizable Parameters** - Base thickness, height, scale, detail level all adjustable

---

## Target Users

### Primary Users

**1. Maker "Maya" - The DIY Enthusiast**
- Age 28-45, owns a 3D printer, active on maker communities
- **Pain:** Wants to convert favorite images into 3D prints but lacks CAD skills
- **Goal:** Create custom lithophanes, relief art, and personalized gifts
- **Use Case:** Convert family photos to lithophanes, logos to 3D badges
- **Success:** "I can finally turn my images into 3D prints without learning CAD!"

**2. Creative "Chris" - The Digital Artist**
- Professional or hobbyist digital artist
- **Pain:** Bridge gap between 2D digital art and physical objects
- **Goal:** Turn artwork into 3D sculptures, merchandise, or prototypes
- **Use Case:** Convert illustrations to relief sculptures for art shows
- **Success:** "My digital art now exists in the physical world"

**3. Educator "Eva" - The STEM Teacher**
- K-12 or higher education instructor with 3D printing resources
- **Pain:** Needs accessible tools to demonstrate 3D concepts
- **Goal:** Teach 3D modeling concepts without complex CAD software
- **Use Case:** Have students convert drawings to 3D prints
- **Success:** "Students understand 3D modeling through hands-on image conversion"

### Secondary Users

**Small Business Owners** - Creating custom merchandise, promotional items
**Prototypers** - Quick concept visualization from sketches
**Accessibility Users** - Creating tactile representations of images for visually impaired

### User Journey

1. **Discovery:** Find tool through maker communities, GitHub, or 3D printing forums
2. **Onboarding:** Simple pip install, download model once, ready to use
3. **First Use:** Convert a simple image with default settings, get immediate STL
4. **Aha Moment:** Realize they can edit the OpenSCAD code to adjust the output
5. **Power Use:** Tweak parameters, try different output styles, batch process
6. **Advocacy:** Share prints online, contribute to project, recommend to others

---

## Success Metrics

### Technical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing Time | < 30 seconds (CPU) | Time from image input to OpenSCAD output |
| Success Rate | > 90% valid OpenSCAD | Generated code compiles without errors |
| STL Quality | Printable without repair | Mesh is manifold and sliceable |

### User Experience Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to First Print | < 5 minutes | New user to STL output |
| Customization Success | > 80% | Users who modify generated parameters |
| Documentation Coverage | 100% | All features documented with examples |

### Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Visual Fidelity | Recognizable | Output visually represents input image |
| Code Readability | Self-documenting | Generated code is readable and commented |
| Parameter Clarity | Self-explanatory | Users understand what each parameter does |

---

## MVP Scope

### Core Features (MVP - Phase 1)

1. **Image Input Handler**
   - Accept JPG, PNG, BMP, TIFF, WebP formats
   - Automatic resizing for model requirements
   - Basic validation and error handling

2. **Depth Estimation Module**
   - Intel DPT-Hybrid-MiDaS integration
   - Hugging Face model loading
   - Depth map generation and normalization

3. **Basic Depth Analyzer**
   - Depth map to height array conversion
   - Basic smoothing and filtering
   - Resolution/detail level control

4. **Simple OpenSCAD Generator**
   - Surface/relief generation from depth map
   - Parametric variables (base_thickness, max_height, model_width)
   - Clean, commented code output

5. **STL Export**
   - OpenSCAD CLI integration
   - Automatic STL rendering
   - Basic error handling

6. **Command-Line Interface**
   - Single command conversion: `image-to-scad input.jpg output.scad`
   - Parameter flags for customization
   - Progress feedback

### Out of Scope for MVP

- Web interface (Gradio/Streamlit) - Phase 4
- Multi-object detection and separation - Phase 2
- Shape classification (cylinders, cubes, spheres) - Phase 2
- CSG operations (union, difference, intersection) - Phase 3
- Real-time preview - Phase 4
- Batch processing - Phase 4
- Text-to-image integration - Phase 5
- Multi-view 3D reconstruction - Phase 5
- Texture/color preservation - Phase 5

### MVP Success Criteria

1. **Functional:** Convert any supported image to valid OpenSCAD code
2. **Quality:** Generated STL is 3D-printable without mesh repair
3. **Usable:** Single command execution with clear output
4. **Documented:** README with installation, usage, and examples
5. **Parametric:** Output code has adjustable parameters

---

## Future Vision

### Phase 2: Enhanced Analysis
- Multi-object detection with separate primitives
- Edge detection and boundary refinement
- Shape classification for better modeling
- Depth layer segmentation

### Phase 3: Smart OpenSCAD Generation
- Full parametric modules
- CSG operations for complex shapes
- Multiple output styles (relief, full 3D, layered)
- Hollowing and infill patterns

### Phase 4: User Experience
- Web interface with real-time preview
- Interactive parameter adjustment
- Batch processing capability
- Project save/load functionality

### Phase 5: Advanced Capabilities
- Text-to-image integration (generate source from description)
- Multi-view 3D reconstruction
- Texture and color preservation
- Direct slicer integration

### Long-term Vision (2-3 years)
- MCP server integration for AI assistant workflows
- Plugin ecosystem for specialized domains (medical, architectural, artistic)
- Cloud-optional processing for resource-constrained users
- Integration with popular CAD tools (Blender, FreeCAD)

---

## Technical Constraints

### Platform Requirements
- Python 3.9+
- PyTorch 2.0+ (CPU or CUDA)
- OpenSCAD installed (for STL rendering)

### Model Requirements
- Intel DPT-Hybrid-MiDaS (~123M parameters)
- Approximately 500MB model download
- ~2GB RAM for inference

### Performance Targets
- CPU inference: < 30 seconds per image
- GPU inference (optional): < 5 seconds per image
- Memory footprint: < 4GB peak

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Depth quality insufficient | Medium | High | Offer multiple models, preprocessing options |
| OpenSCAD complexity | Low | Medium | Start simple, iterate on generation |
| Performance issues | Medium | Medium | GPU support, batch processing |
| Model licensing changes | Low | High | Pin versions, document alternatives |

---

## Next Steps

1. **Create PRD** - Detailed functional and non-functional requirements
2. **Architecture Design** - System components and interfaces
3. **Epic Breakdown** - Implementable stories for Phase 1
4. **Implementation** - Sprint planning and development

---

*Product Brief created following BMad Method v6.0 workflow*
*Reference: docs/PROJECT_PLAN.md*
