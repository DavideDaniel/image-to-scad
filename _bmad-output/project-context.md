---
project_name: 'image-to-ai-to-stil'
user_name: 'David'
date: '2026-01-09'
sections_completed: ['technology_stack', 'python_rules', 'pipeline_rules', 'testing_rules', 'code_quality', 'critical_rules']
status: 'complete'
rule_count: 45
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns for implementing code in this project. Focus on unobvious details._

---

## Technology Stack & Versions

| Technology | Version | Critical Notes |
|------------|---------|----------------|
| Python | 3.9+ | Target 3.9 minimum for broad compatibility |
| PyTorch | >=2.0 | ALWAYS check CUDA availability, never assume GPU |
| Transformers | >=4.35 | Model cached in ~/.cache/huggingface/ |
| Pillow | >=10.0 | Use Image.Resampling.LANCZOS (not ANTIALIAS) |
| OpenCV | >=4.8 | opencv-python package (has GUI deps) |
| NumPy | >=1.24 | Watch for NumPy 2.0 dtype changes |
| huggingface-hub | >=0.20 | First run downloads ~500MB model |
| OpenSCAD | External | Optional - must handle when not installed |

### Version Gotchas

- **Pillow 10.0+**: `Image.ANTIALIAS` removed, use `Image.Resampling.LANCZOS`
- **PyTorch device**: Always use `torch.device('cuda' if torch.cuda.is_available() else 'cpu')`
- **Model caching**: Never reload DPT model repeatedly - cache in memory
- **CI environments**: Cache huggingface models, OpenSCAD may not be available

## Critical Implementation Rules

### Python-Specific Rules

**Type Hints (Required):**
- ALL functions must have complete type hints (mypy strict mode)
- Use `Optional[X]` not `X | None` (Python 3.9 compat)
- Use `Tuple[int, int]` not `tuple[int, int]` (Python 3.9 compat)

**Imports:**
- Use absolute imports: `from image_to_scad.config import ConversionConfig`
- Never use relative imports like `from .config import ...`
- Group: stdlib, third-party, local (ruff handles this)

**Dataclasses:**
- All configuration objects must be `@dataclass`
- Validate in `__post_init__`, raise `ValueError` for invalid params
- Include `to_dict()` for serialization when needed

**Exceptions:**
- Always raise from custom hierarchy (`ImageToScadError` subclasses)
- Use `raise NewError("message") from original_error`
- Never catch bare `Exception` unless re-raising

### Pipeline Architecture Rules

**Module Structure:**
- Each pipeline stage lives in `src/image_to_scad/pipeline/`
- One class per file, file named after class (snake_case)
- Exporters live in `src/image_to_scad/exporters/`

**Component Design:**
- Each component is a class with clear input/output types
- Use `__init__` for configuration, methods for operations
- Always use `get_logger(__name__)` for logging
- Private methods prefixed with `_` (e.g., `_validate_input`)

**Data Flow:**
- `ImageLoader.load()` → `np.ndarray` (RGB image)
- `DepthEstimator.estimate()` → `np.ndarray` (depth map 0.0-1.0)
- `DepthAnalyzer.analyze()` → `HeightData` dataclass
- `ScadGenerator.generate()` → `str` (OpenSCAD code)
- `STLExporter.export()` → `Path` (optional, may fail)

**Error Boundaries:**
- Each stage catches its errors and wraps in stage-specific exception
- Never let raw PyTorch/PIL/CV2 exceptions bubble up
- Always include context in error messages (file path, dimensions, etc.)

### Testing Rules

**Test Organization:**
- Unit tests: `tests/unit/test_<module>.py`
- Integration tests: `tests/integration/`
- One test file per source module
- Use fixtures from `conftest.py`, don't duplicate

**Fixtures:**
- Use provided fixtures: `sample_image_array`, `sample_depth_map`, `default_config`
- For file I/O tests, use `temp_output_dir` (auto-cleaned)
- Test images should be small (64x64, 128x128) for speed

**Markers:**
- `@pytest.mark.slow` - Tests that download models or take >10s
- Skip GPU tests: `@pytest.mark.skipif(not torch.cuda.is_available(), reason="No GPU")`

**Mocking:**
- Mock `DepthEstimator` in unit tests (avoid model loading)
- Mock file I/O with `tmp_path` fixture
- Never mock dataclasses - use real instances

**Coverage:**
- Target 90% for pipeline stages
- Exclude `if TYPE_CHECKING:` blocks
- Exclude `raise NotImplementedError`

### Code Quality & Style

**Formatting:**
- Run `black src/ tests/` before committing
- Line length: 100 characters max
- black handles all formatting - don't fight it

**Linting:**
- Run `ruff check src/ tests/` - must pass with no errors
- Imports auto-sorted by ruff (stdlib → third-party → local)
- Fix: `ruff check --fix src/ tests/`

**Type Checking:**
- Run `mypy src/` - must pass
- Every function needs type hints (no exceptions)
- Use `# type: ignore[specific-error]` sparingly with comment why

**Docstrings:**
- Required on: classes, public methods, modules
- Format: Google-style with Args/Returns/Raises sections

**Naming:**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Critical Don't-Miss Rules

**NEVER Do:**
- Load the DPT model more than once per session (cache it!)
- Assume CUDA/GPU is available
- Use `print()` for output - use the logger
- Hardcode paths - use `Path` objects
- Let PIL/PyTorch/CV2 exceptions escape unwrapped
- Add features not in the PRD/epics

**ALWAYS Do:**
- Check `torch.cuda.is_available()` before using GPU
- Wrap external library exceptions in custom exceptions
- Include file path/dimensions in error messages
- Use `Path` from pathlib, never string concatenation for paths
- Validate image dimensions before processing
- Handle OpenSCAD not being installed gracefully

**Edge Cases to Handle:**
- RGBA images → convert to RGB with white background
- Grayscale images → convert to RGB
- Images <64px → raise `ImageLoadError`
- Images >4096px → resize with warning
- OpenSCAD missing → skip STL, return .scad only

**Performance Critical:**
- Model loading: ~5s cold, instant warm (cache the model instance)
- Image resize: do BEFORE depth estimation, not after
- Depth estimation: O(pixels), keep images <1024px for speed
- OpenSCAD render: can take minutes for complex models

**Security:**
- Model source: `Intel/dpt-hybrid-midas` from Hugging Face only
- No telemetry, no external API calls
- Validate input paths exist and are files

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

---

_Last Updated: 2026-01-09_
