"""
Integration tests for the command-line interface.

These tests verify that the CLI correctly parses arguments and
invokes the conversion pipeline.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from PIL import Image

from image_to_scad.cli import main, parse_args, validate_args, build_config, create_parser
from image_to_scad.config import ConversionConfig


class TestCLIParsing:
    """Test CLI argument parsing."""

    @pytest.fixture
    def sample_image_file(self, tmp_path: Path) -> Path:
        """Create a sample image file for testing."""
        image_path = tmp_path / "test.png"
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        Image.fromarray(image).save(image_path)
        return image_path

    def test_parse_minimal_args(self, sample_image_file: Path):
        """Test parsing with only required arguments."""
        args = parse_args([str(sample_image_file)])

        assert args.input == sample_image_file
        assert args.output is None
        assert args.stl is False
        assert args.base_thickness == 2.0
        assert args.max_height == 15.0
        assert args.width == 100.0
        assert args.detail == 1.0
        assert args.no_smoothing is False
        assert args.invert is False

    def test_parse_output_flag(self, sample_image_file: Path, tmp_path: Path):
        """Test parsing output path."""
        output_path = tmp_path / "output.scad"
        args = parse_args([str(sample_image_file), "-o", str(output_path)])

        assert args.output == output_path

    def test_parse_dimension_flags(self, sample_image_file: Path):
        """Test parsing dimension parameters."""
        args = parse_args([
            str(sample_image_file),
            "--base-thickness", "3.0",
            "--max-height", "20.0",
            "--width", "150.0",
        ])

        assert args.base_thickness == 3.0
        assert args.max_height == 20.0
        assert args.width == 150.0

    def test_parse_detail_flag(self, sample_image_file: Path):
        """Test parsing detail level."""
        args = parse_args([str(sample_image_file), "--detail", "1.5"])

        assert args.detail == 1.5

    def test_parse_processing_flags(self, sample_image_file: Path):
        """Test parsing processing option flags."""
        args = parse_args([
            str(sample_image_file),
            "--no-smoothing",
            "--invert",
        ])

        assert args.no_smoothing is True
        assert args.invert is True

    def test_parse_stl_flag(self, sample_image_file: Path):
        """Test parsing STL generation flag."""
        args = parse_args([str(sample_image_file), "--stl"])

        assert args.stl is True

    def test_parse_verbosity_flags(self, sample_image_file: Path):
        """Test parsing verbosity flags."""
        args_verbose = parse_args([str(sample_image_file), "-v"])
        assert args_verbose.verbose is True

        args_quiet = parse_args([str(sample_image_file), "-q"])
        assert args_quiet.quiet is True


class TestCLIValidation:
    """Test CLI argument validation."""

    @pytest.fixture
    def sample_image_file(self, tmp_path: Path) -> Path:
        """Create a sample image file for testing."""
        image_path = tmp_path / "test.png"
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        Image.fromarray(image).save(image_path)
        return image_path

    def test_validate_existing_file(self, sample_image_file: Path):
        """Test validation passes for existing file."""
        args = parse_args([str(sample_image_file)])
        # Should not raise
        validate_args(args)

    def test_validate_missing_file(self, tmp_path: Path):
        """Test validation fails for missing file."""
        args = parse_args([str(tmp_path / "nonexistent.png")])

        with pytest.raises(FileNotFoundError):
            validate_args(args)

    def test_validate_directory_instead_of_file(self, tmp_path: Path):
        """Test validation fails when path is a directory."""
        args = parse_args([str(tmp_path)])

        with pytest.raises(ValueError, match="not a file"):
            validate_args(args)

    def test_validate_invalid_detail_low(self, sample_image_file: Path):
        """Test validation fails for detail < 0.5."""
        args = parse_args([str(sample_image_file), "--detail", "0.3"])

        with pytest.raises(ValueError, match="Detail level"):
            validate_args(args)

    def test_validate_invalid_detail_high(self, sample_image_file: Path):
        """Test validation fails for detail > 2.0."""
        args = parse_args([str(sample_image_file), "--detail", "2.5"])

        with pytest.raises(ValueError, match="Detail level"):
            validate_args(args)

    def test_validate_negative_dimensions(self, sample_image_file: Path):
        """Test validation fails for negative dimensions."""
        args = parse_args([str(sample_image_file), "--base-thickness", "-1"])

        with pytest.raises(ValueError, match="positive"):
            validate_args(args)


class TestCLIConfigBuilding:
    """Test building ConversionConfig from CLI args."""

    @pytest.fixture
    def sample_image_file(self, tmp_path: Path) -> Path:
        """Create a sample image file for testing."""
        image_path = tmp_path / "test.png"
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        Image.fromarray(image).save(image_path)
        return image_path

    def test_build_default_config(self, sample_image_file: Path):
        """Test building config with default values."""
        args = parse_args([str(sample_image_file)])
        config = build_config(args)

        assert isinstance(config, ConversionConfig)
        assert config.base_thickness == 2.0
        assert config.max_height == 15.0
        assert config.model_width == 100.0
        assert config.detail_level == 1.0
        assert config.smoothing is True
        assert config.invert_depth is False

    def test_build_custom_config(self, sample_image_file: Path):
        """Test building config with custom values."""
        args = parse_args([
            str(sample_image_file),
            "--base-thickness", "5.0",
            "--max-height", "25.0",
            "--width", "200.0",
            "--detail", "1.5",
            "--no-smoothing",
            "--invert",
        ])
        config = build_config(args)

        assert config.base_thickness == 5.0
        assert config.max_height == 25.0
        assert config.model_width == 200.0
        assert config.detail_level == 1.5
        assert config.smoothing is False
        assert config.invert_depth is True


class TestCLIMainFunction:
    """Test the main CLI entry point."""

    @pytest.fixture
    def sample_image_file(self, tmp_path: Path) -> Path:
        """Create a sample image file for testing."""
        image_path = tmp_path / "test.png"
        image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        Image.fromarray(image).save(image_path)
        return image_path

    def test_main_returns_zero_on_success(self, sample_image_file: Path, tmp_path: Path):
        """Test main returns 0 on successful conversion."""
        pytest.importorskip("transformers")

        output_path = tmp_path / "output.scad"

        exit_code = main([str(sample_image_file), "-o", str(output_path), "-q"])

        assert exit_code == 0
        assert output_path.exists()

    def test_main_returns_one_on_missing_file(self, tmp_path: Path):
        """Test main returns 1 for missing input file."""
        exit_code = main([str(tmp_path / "nonexistent.png")])

        assert exit_code == 1

    def test_main_returns_one_on_invalid_args(self, sample_image_file: Path):
        """Test main returns 1 for invalid arguments."""
        exit_code = main([str(sample_image_file), "--detail", "5.0"])

        assert exit_code == 1

    def test_main_handles_keyboard_interrupt(self, sample_image_file: Path, tmp_path: Path):
        """Test main handles KeyboardInterrupt gracefully."""
        with patch("image_to_scad.cli.Converter") as mock_converter:
            mock_converter.return_value.convert.side_effect = KeyboardInterrupt()

            exit_code = main([str(sample_image_file), "-o", str(tmp_path / "out.scad")])

            assert exit_code == 130

    def test_main_generates_default_output_path(self, sample_image_file: Path):
        """Test main generates output path from input when not specified."""
        pytest.importorskip("transformers")

        # Run in the same directory as the image
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(sample_image_file.parent)

            exit_code = main([sample_image_file.name, "-q"])

            expected_output = sample_image_file.with_suffix(".scad")
            assert expected_output.exists()
            assert exit_code == 0

        finally:
            import os
            os.chdir(original_cwd)


class TestCLIHelpAndVersion:
    """Test CLI help and version output."""

    def test_help_text_includes_all_options(self):
        """Test that help text documents all options."""
        parser = create_parser()
        help_text = parser.format_help()

        # Check required options
        assert "input" in help_text
        assert "-o" in help_text or "--output" in help_text

        # Check dimension options
        assert "--base-thickness" in help_text
        assert "--max-height" in help_text
        assert "--width" in help_text
        assert "--detail" in help_text

        # Check processing options
        assert "--no-smoothing" in help_text
        assert "--invert" in help_text
        assert "--stl" in help_text

        # Check verbosity options
        assert "-v" in help_text or "--verbose" in help_text
        assert "-q" in help_text or "--quiet" in help_text

    def test_version_flag_shows_version(self):
        """Test that --version shows version number."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])

        assert exc_info.value.code == 0


class TestCLIEndToEnd:
    """End-to-end CLI tests."""

    @pytest.fixture
    def sample_image_file(self, tmp_path: Path) -> Path:
        """Create a sample image file for testing."""
        image_path = tmp_path / "test_image.jpg"
        image = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        Image.fromarray(image).save(image_path)
        return image_path

    def test_full_conversion_with_all_options(self, sample_image_file: Path, tmp_path: Path):
        """Test full conversion with all CLI options specified."""
        pytest.importorskip("transformers")

        output_path = tmp_path / "custom_output.scad"

        exit_code = main([
            str(sample_image_file),
            "-o", str(output_path),
            "--base-thickness", "3.0",
            "--max-height", "20.0",
            "--width", "150.0",
            "--detail", "0.5",
            "--no-smoothing",
            "--invert",
            "-q",
        ])

        assert exit_code == 0
        assert output_path.exists()

        # Verify generated content has custom parameters
        content = output_path.read_text()
        assert "base_thickness = 3.00" in content
        assert "max_relief_height = 20.00" in content

    def test_scad_output_is_valid(self, sample_image_file: Path, tmp_path: Path):
        """Test that generated .scad file has valid structure."""
        pytest.importorskip("transformers")

        output_path = tmp_path / "output.scad"

        exit_code = main([str(sample_image_file), "-o", str(output_path), "-q"])

        assert exit_code == 0

        content = output_path.read_text()

        # Check for required OpenSCAD elements
        assert "// Generated by image-to-scad" in content
        assert "module relief_surface()" in content
        assert "polyhedron(" in content
        assert "relief_surface();" in content

        # Check for proper polyhedron structure
        assert "points = [" in content
        assert "faces = [" in content
