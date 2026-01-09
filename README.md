# image-to-scad

Convert 2D images into parametric 3D relief models using AI depth estimation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-112%20passing-brightgreen.svg)]()

## Overview

**image-to-scad** transforms any image into editable OpenSCAD code for 3D printing. Unlike tools that produce static meshes, this generates parametric code you can customize after generation.

### Key Features

- **AI-Powered Depth Estimation** - Uses Intel DPT-Hybrid-MiDaS model for accurate depth perception
- **Parametric Output** - Generated OpenSCAD code has adjustable variables (height, width, base thickness)
- **Local Processing** - No cloud services, API fees, or privacy concerns
- **Multiple Formats** - Supports JPEG, PNG, WebP, BMP, and TIFF input
- **Optional STL Export** - Render directly to STL if OpenSCAD is installed

## Installation

### Prerequisites

- Python 3.9 or higher
- ~2GB disk space for AI model (downloaded on first run)
- [OpenSCAD](https://openscad.org/downloads.html) (optional, for STL rendering)

### Install from source

```bash
git clone https://github.com/yourusername/image-to-scad.git
cd image-to-scad
pip install -e .
```

### Install dependencies only

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```bash
# Convert image to OpenSCAD file
image-to-scad photo.jpg

# Specify output path
image-to-scad photo.jpg -o my-relief.scad

# Also generate STL (requires OpenSCAD)
image-to-scad photo.jpg --stl
```

### Customize Output

```bash
# Adjust dimensions
image-to-scad photo.jpg --width 150 --max-height 20 --base-thickness 3

# Higher detail (slower, larger file)
image-to-scad photo.jpg --detail 2.0

# Create lithophane (invert depth)
image-to-scad photo.jpg --invert

# Disable smoothing for sharper edges
image-to-scad photo.jpg --no-smoothing
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `<input>.scad` | Output file path |
| `--stl` | off | Also generate STL file |
| `--base-thickness` | 2.0 mm | Minimum model thickness |
| `--max-height` | 15.0 mm | Maximum relief height |
| `--width` | 100.0 mm | Model width (height auto-calculated) |
| `--detail` | 1.0 | Detail level (0.5 = coarse, 2.0 = fine) |
| `--no-smoothing` | off | Disable Gaussian smoothing |
| `--invert` | off | Invert depth (for lithophanes) |
| `-v, --verbose` | off | Show detailed progress |
| `-q, --quiet` | off | Suppress all output except errors |

## Output

The generated OpenSCAD file includes adjustable parameters at the top:

```openscad
// Configuration Parameters
base_thickness = 2.00;  // mm
max_relief_height = 15.00;   // mm
model_width = 100.00;      // mm
model_height = 75.00;    // mm
```

Open the `.scad` file in OpenSCAD to:
- Preview the 3D model
- Adjust parameters in the Customizer panel
- Render to STL for printing

## Use Cases

### Lithophanes
Create backlit photo prints that reveal images when illuminated:
```bash
image-to-scad portrait.jpg --invert --base-thickness 0.8 --max-height 3
```

### Relief Art
Transform artwork into decorative wall pieces:
```bash
image-to-scad artwork.png --width 200 --max-height 10
```

### Topographic Models
Convert heightmaps to terrain models:
```bash
image-to-scad terrain.png --detail 1.5 --no-smoothing
```

## How It Works

1. **Image Loading** - Validates and preprocesses the input image
2. **Depth Estimation** - Intel DPT model infers relative depth from the image
3. **Height Mapping** - Converts depth values to physical heights in mm
4. **Code Generation** - Produces parametric OpenSCAD with embedded height data
5. **STL Export** (optional) - Invokes OpenSCAD CLI to render mesh

## Performance

| Image Size | Detail | Processing Time* |
|------------|--------|------------------|
| 1024x768 | 1.0 | ~10 seconds |
| 1024x768 | 2.0 | ~15 seconds |
| 4000x3000 | 1.0 | ~12 seconds |

*On Apple M1, first run includes ~60s model download

## Development

### Setup

```bash
git clone https://github.com/yourusername/image-to-scad.git
cd image-to-scad
pip install -r requirements-dev.txt
pip install -e .
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Project Structure

```
image-to-scad/
├── src/image_to_scad/
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration dataclasses
│   ├── converter.py        # Pipeline orchestrator
│   ├── exceptions.py       # Custom exceptions
│   ├── pipeline/
│   │   ├── image_loader.py    # Image loading/validation
│   │   ├── depth_estimator.py # AI depth estimation
│   │   ├── depth_analyzer.py  # Depth to height conversion
│   │   └── scad_generator.py  # OpenSCAD code generation
│   ├── exporters/
│   │   └── stl_exporter.py    # OpenSCAD CLI wrapper
│   └── utils/
│       ├── file_utils.py      # File I/O helpers
│       └── logging.py         # Logging configuration
├── tests/                  # Test suite (112 tests)
├── pyproject.toml          # Package configuration
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development dependencies
```

## Dependencies

### Production
- **Pillow** - Image loading and processing
- **NumPy** - Array operations
- **PyTorch** - Deep learning runtime
- **Transformers** - Hugging Face model loading
- **OpenCV** - Image resizing and smoothing

### Development
- **pytest** - Testing framework
- **black** - Code formatter
- **ruff** - Linter
- **mypy** - Type checker

## Troubleshooting

### "Model download failed"
The AI model (~500MB) downloads automatically on first run. Ensure you have internet access and sufficient disk space in `~/.cache/huggingface/`.

### "OpenSCAD not found"
Install [OpenSCAD](https://openscad.org/downloads.html) and ensure it's in your PATH. On macOS, the app bundle is detected automatically.

### "CUDA out of memory"
The model runs on CPU by default. If you have a GPU and encounter memory issues, the tool will fall back to CPU automatically.

### Slow processing
- Use `--detail 0.5` for faster processing
- Reduce input image size before conversion
- First run is slower due to model download

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Intel DPT-Hybrid-MiDaS](https://huggingface.co/Intel/dpt-hybrid-midas) for depth estimation
- [OpenSCAD](https://openscad.org/) for parametric 3D modeling
- [Hugging Face](https://huggingface.co/) for model hosting

---

**Created with the BMad Method** | [Report Issues](https://github.com/yourusername/image-to-scad/issues)
