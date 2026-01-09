"""
Unit tests for image_to_scad.pipeline.scad_generator module.

Tests written following TDD practices based on PRD specifications:
- FR13: System can generate valid OpenSCAD code from processed depth data
- FR14: Generated code includes parametric variables for customization
- FR15: User can specify base thickness for generated models
- FR16: User can specify maximum height for relief features
- FR17: User can specify overall model width/scale
- FR18: Generated code includes comments explaining parameters
- FR19: System can generate relief/lithophane style output
"""

import numpy as np
import pytest
import re

from image_to_scad.pipeline.scad_generator import OpenSCADGenerator
from image_to_scad.config import ConversionConfig, HeightData
from image_to_scad.exceptions import OpenSCADGenerationError


@pytest.fixture
def generator():
    """Create OpenSCADGenerator instance for testing."""
    return OpenSCADGenerator()


@pytest.fixture
def sample_height_data():
    """Create sample HeightData for testing."""
    heights = np.array([
        [2.0, 3.0, 4.0],
        [5.0, 10.0, 6.0],
        [3.0, 4.0, 2.0],
    ], dtype=np.float32)
    return HeightData(
        heights=heights,
        width_mm=100.0,
        height_mm=100.0,
    )


@pytest.fixture
def default_config():
    """Create default conversion config."""
    return ConversionConfig()


class TestOpenSCADGeneratorBasics:
    """Basic functionality tests for OpenSCADGenerator."""

    def test_generate_returns_string(self, generator, sample_height_data, default_config):
        """FR13: Should return OpenSCAD code as string."""
        result = generator.generate(sample_height_data, default_config)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_produces_valid_openscad_syntax(self, generator, sample_height_data, default_config):
        """FR13: Generated code should have valid OpenSCAD structure."""
        result = generator.generate(sample_height_data, default_config)

        # Should contain module definition
        assert "module" in result or "polyhedron" in result or "cube" in result

        # Should not have obvious syntax errors
        # Check for balanced braces
        assert result.count("{") == result.count("}")
        assert result.count("[") == result.count("]")
        assert result.count("(") == result.count(")")

    def test_generate_includes_semicolons(self, generator, sample_height_data, default_config):
        """FR13: OpenSCAD statements should end with semicolons."""
        result = generator.generate(sample_height_data, default_config)

        # Variable assignments should have semicolons
        assert re.search(r"=\s*[\d.]+\s*;", result)


class TestParametricVariables:
    """Tests for parametric variable generation (FR14)."""

    def test_includes_base_thickness_variable(self, generator, sample_height_data, default_config):
        """FR15: Should include base_thickness parameter."""
        result = generator.generate(sample_height_data, default_config)

        # Should have a base thickness variable
        assert "base_thickness" in result.lower() or "base" in result.lower()

    def test_includes_max_height_variable(self, generator, sample_height_data, default_config):
        """FR16: Should include max_height parameter."""
        result = generator.generate(sample_height_data, default_config)

        # Should have a max height variable
        assert "max" in result.lower() and "height" in result.lower()

    def test_includes_width_variable(self, generator, sample_height_data, default_config):
        """FR17: Should include model width parameter."""
        result = generator.generate(sample_height_data, default_config)

        # Should have width variable
        assert "width" in result.lower() or "model_width" in result.lower()

    def test_variables_at_top_of_file(self, generator, sample_height_data, default_config):
        """FR14: Parametric variables should be at the top for customizer."""
        result = generator.generate(sample_height_data, default_config)
        lines = result.split('\n')

        # Find first non-comment, non-empty line with a variable
        found_variable = False
        for line in lines[:30]:  # Check first 30 lines
            stripped = line.strip()
            if stripped and not stripped.startswith('//'):
                if '=' in stripped and ';' in stripped:
                    found_variable = True
                    break

        assert found_variable, "Variables should appear near top of file"

    def test_config_values_reflected_in_output(self, generator, sample_height_data):
        """FR14: Config values should be used in generated code."""
        config = ConversionConfig(
            base_thickness=5.0,
            max_height=25.0,
            model_width=150.0,
        )
        result = generator.generate(sample_height_data, config)

        # Config values should appear in output
        assert "5" in result or "5.0" in result or "5.00" in result
        assert "25" in result or "25.0" in result or "25.00" in result


class TestCodeComments:
    """Tests for code documentation (FR18)."""

    def test_includes_header_comment(self, generator, sample_height_data, default_config):
        """FR18: Should include header comment."""
        result = generator.generate(sample_height_data, default_config)

        # Should start with comment
        assert result.strip().startswith("//")

    def test_includes_generation_info(self, generator, sample_height_data, default_config):
        """FR18: Should include generation timestamp or tool info."""
        result = generator.generate(sample_height_data, default_config)

        # Should mention the tool or have date
        assert "image-to-scad" in result.lower() or "generated" in result.lower()

    def test_includes_dimension_info(self, generator, sample_height_data, default_config):
        """FR18: Should document dimensions."""
        result = generator.generate(sample_height_data, default_config)

        # Should have dimension info in comments
        assert "mm" in result.lower() or "dimension" in result.lower() or "width" in result.lower()

    def test_variables_have_comments(self, generator, sample_height_data, default_config):
        """FR18: Parameter variables should have explanatory comments."""
        result = generator.generate(sample_height_data, default_config)

        # Should have comments near variable definitions
        lines = result.split('\n')
        var_lines_with_comments = 0

        for line in lines:
            if '=' in line and '//' in line:
                var_lines_with_comments += 1

        assert var_lines_with_comments >= 2, "Variables should have inline comments"


class TestReliefGeneration:
    """Tests for relief-style output (FR19)."""

    def test_generates_3d_geometry(self, generator, sample_height_data, default_config):
        """FR19: Should generate 3D geometry commands."""
        result = generator.generate(sample_height_data, default_config)

        # Should have 3D primitives or surface generation
        has_3d = any(kw in result.lower() for kw in [
            'polyhedron', 'cube', 'cylinder', 'sphere',
            'linear_extrude', 'surface', 'translate'
        ])
        assert has_3d, "Should contain 3D geometry commands"

    def test_includes_height_data(self, generator, sample_height_data, default_config):
        """FR19: Should embed or reference height data."""
        result = generator.generate(sample_height_data, default_config)

        # Should have height data embedded or in a data structure
        # Check for array syntax or height references
        has_data = '[' in result and ']' in result
        assert has_data, "Should include height data array"

    def test_uses_grid_structure(self, generator, sample_height_data, default_config):
        """FR19: Relief should use grid-based structure."""
        result = generator.generate(sample_height_data, default_config)

        # Should have loop or iteration for grid
        has_loop = 'for' in result.lower() or len(re.findall(r'\[.*\]', result)) > 5
        assert has_loop, "Should use loops or grid data"


class TestHeightDataHandling:
    """Tests for height data processing in generator."""

    def test_handles_various_resolutions(self, generator, default_config):
        """Should handle different height data resolutions."""
        resolutions = [(10, 10), (50, 30), (100, 100)]

        for rows, cols in resolutions:
            heights = np.random.rand(rows, cols).astype(np.float32) * 15 + 2
            height_data = HeightData(heights=heights, width_mm=100.0, height_mm=100.0 * rows / cols)

            result = generator.generate(height_data, default_config)
            assert isinstance(result, str)
            assert len(result) > 100

    def test_height_values_appear_in_output(self, generator):
        """Height values from data should appear in output."""
        heights = np.array([[5.5, 7.5], [9.5, 11.5]], dtype=np.float32)
        height_data = HeightData(heights=heights, width_mm=100.0, height_mm=100.0)
        config = ConversionConfig()

        result = generator.generate(height_data, config)

        # Some height values should appear (may be formatted differently)
        # At least check the data is somehow represented
        assert '5' in result or '7' in result or '9' in result or '11' in result


class TestFormatCode:
    """Tests for code formatting utility."""

    def test_format_removes_trailing_whitespace(self, generator):
        """Format should remove trailing whitespace."""
        code = "line1   \nline2\t\nline3"
        result = generator.format_code(code)

        for line in result.split('\n'):
            assert line == line.rstrip()

    def test_format_preserves_content(self, generator):
        """Format should preserve actual content."""
        code = "module test() {\n  cube([1,2,3]);\n}"
        result = generator.format_code(code)

        assert "module test()" in result
        assert "cube([1,2,3])" in result


class TestErrorHandling:
    """Tests for error handling in generator."""

    def test_openscad_generation_error_is_catchable(self):
        """OpenSCADGenerationError should be part of exception hierarchy."""
        from image_to_scad.exceptions import ImageToScadError

        assert issubclass(OpenSCADGenerationError, ImageToScadError)

    def test_invalid_height_data_raises_error(self, generator, default_config):
        """Should handle invalid height data gracefully."""
        # Create invalid HeightData (this should be caught by HeightData validation)
        with pytest.raises((ValueError, OpenSCADGenerationError)):
            invalid_heights = np.array([1, 2, 3])  # 1D array
            height_data = HeightData(heights=invalid_heights, width_mm=100.0, height_mm=100.0)
