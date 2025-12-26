"""Integration tests for image-to-image generation with YAML config."""

from pathlib import Path

import pytest
import yaml

from imgcreator.core.config import ConfigLoader
from imgcreator.core.pipeline import GenerationContext, GenerationPipeline
from imgcreator.core.series import SeriesLoader


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory."""
    config_file = tmp_path / "imgcreator.yaml"
    config_file.write_text(
        yaml.dump(
            {
                "api": {"provider": "volcengine", "model": "图片生成4.0"},
                "defaults": {
                    "width": 1024,
                    "height": 1024,
                    "reference_image": "./assets/base-style.png",
                },
                "output": {"base_dir": "./output"},
            }
        )
    )
    return tmp_path


@pytest.fixture
def test_image(project_dir):
    """Create a test reference image."""
    from PIL import Image

    assets_dir = project_dir / "assets"
    assets_dir.mkdir()
    image_path = assets_dir / "base-style.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path, "PNG")
    return image_path


class TestConfigWithReferenceImage:
    """Tests for config loading with reference_image."""

    def test_load_config_with_reference_image(self, project_dir, test_image):
        """Test loading config with reference_image in defaults."""
        loader = ConfigLoader(project_path=project_dir)
        config = loader.load()

        assert config.defaults.reference_image == "./assets/base-style.png"

    def test_config_without_reference_image(self, tmp_path):
        """Test backward compatibility: config without reference_image."""
        config_file = tmp_path / "imgcreator.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "api": {"provider": "volcengine"},
                    "defaults": {"width": 1024},
                }
            )
        )

        loader = ConfigLoader(project_path=tmp_path)
        config = loader.load()

        assert config.defaults.reference_image is None

    def test_pipeline_creates_context_with_reference(self, project_dir, test_image):
        """Test pipeline creates context with reference_image from config."""
        pipeline = GenerationPipeline(project_path=project_dir, verbose=False)
        context = pipeline.create_context(prompt="test prompt")

        assert context.reference_image_path == "./assets/base-style.png"

    def test_pipeline_overrides_reference_image(self, project_dir, test_image):
        """Test pipeline can override reference_image from CLI."""
        pipeline = GenerationPipeline(project_path=project_dir, verbose=False)
        context = pipeline.create_context(
            prompt="test", reference_image_path="./assets/override.png"
        )

        assert context.reference_image_path == "./assets/override.png"


class TestSeriesWithReferenceImage:
    """Tests for series config with reference_image."""

    def test_series_config_with_reference_image(self, project_dir, test_image):
        """Test series config can specify reference_image."""
        series_file = project_dir / "series" / "test-series.yaml"
        series_file.parent.mkdir()
        series_file.write_text(
            yaml.dump(
                {
                    "name": "test-series",
                    "template": "{{subject}} icon",
                    "config": {"reference_image": "./assets/series-style.png"},
                    "items": [{"id": "home", "subject": "home"}],
                }
            )
        )

        # Create series reference image
        series_img = project_dir / "assets" / "series-style.png"
        from PIL import Image

        img = Image.new("RGB", (50, 50), color="blue")
        img.save(series_img, "PNG")

        loader = SeriesLoader(project_path=project_dir)
        series = loader.load("test-series")

        assert series.config.reference_image == "./assets/series-style.png"

    def test_series_reference_overrides_default(self, project_dir, test_image):
        """Test series reference_image overrides project default."""
        series_file = project_dir / "series" / "test-series.yaml"
        series_file.parent.mkdir()
        series_file.write_text(
            yaml.dump(
                {
                    "name": "test-series",
                    "template": "{{subject}}",
                    "config": {"reference_image": "./assets/series-style.png"},
                    "items": [{"id": "home", "subject": "home"}],
                }
            )
        )

        # Create series reference image
        series_img = project_dir / "assets" / "series-style.png"
        from PIL import Image

        img = Image.new("RGB", (50, 50), color="blue")
        img.save(series_img, "PNG")

        loader = SeriesLoader(project_path=project_dir)
        series = loader.load("test-series")

        # Series config should override project default
        assert series.config.reference_image == "./assets/series-style.png"
        assert series.config.reference_image != "./assets/base-style.png"

    def test_series_level_reference_image(self, project_dir, test_image):
        """Test reference_image at series level (not in config)."""
        series_file = project_dir / "series" / "test-series.yaml"
        series_file.parent.mkdir()
        series_file.write_text(
            yaml.dump(
                {
                    "name": "test-series",
                    "template": "{{subject}}",
                    "reference_image": "./assets/series-level.png",  # At series level
                    "items": [{"id": "home", "subject": "home"}],
                }
            )
        )

        # Create series reference image
        series_img = project_dir / "assets" / "series-level.png"
        from PIL import Image

        img = Image.new("RGB", (50, 50), color="green")
        img.save(series_img, "PNG")

        loader = SeriesLoader(project_path=project_dir)
        series = loader.load("test-series")

        # Should be loaded into config
        assert series.config.reference_image == "./assets/series-level.png"


class TestDryRunWithReferenceImage:
    """Tests for dry-run mode with reference images."""

    def test_dry_run_shows_api_mode(self, project_dir, test_image):
        """Test dry-run shows correct API mode for image-to-image."""
        pipeline = GenerationPipeline(project_path=project_dir, verbose=False)
        context = pipeline.create_context(prompt="test prompt")

        preview = pipeline.dry_run(context)

        assert preview["api_mode"] == "Image-to-image (图生图3.0)"
        assert preview["reference_image"] == "./assets/base-style.png"

    def test_dry_run_shows_text_to_image_mode(self, tmp_path):
        """Test dry-run shows text-to-image mode when no reference."""
        config_file = tmp_path / "imgcreator.yaml"
        config_file.write_text(
            yaml.dump(
                {
                    "api": {"provider": "volcengine"},
                    "defaults": {"width": 1024},
                }
            )
        )

        pipeline = GenerationPipeline(project_path=tmp_path, verbose=False)
        context = pipeline.create_context(prompt="test prompt")

        preview = pipeline.dry_run(context)

        assert preview["api_mode"] == "Text-to-image"
        assert "reference_image" not in preview


class TestReferenceImagePathResolution:
    """Tests for reference image path resolution."""

    def test_relative_path_resolution(self, project_dir, test_image):
        """Test relative paths are resolved from project root."""
        pipeline = GenerationPipeline(project_path=project_dir, verbose=False)
        context = pipeline.create_context(prompt="test")

        # Path should be relative to project root
        assert context.reference_image_path == "./assets/base-style.png"

    def test_absolute_path_preserved(self, project_dir, test_image):
        """Test absolute paths are preserved."""
        abs_path = test_image.absolute()
        pipeline = GenerationPipeline(project_path=project_dir, verbose=False)
        context = pipeline.create_context(
            prompt="test", reference_image_path=str(abs_path)
        )

        assert Path(context.reference_image_path).is_absolute()

