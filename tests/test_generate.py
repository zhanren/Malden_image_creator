"""Tests for the generate command and pipeline."""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from imgcreator.api.base import GenerationResult, GenerationStatus
from imgcreator.cli.main import cli
from imgcreator.core.pipeline import (
    GenerationContext,
    GenerationPipeline,
    PipelineResult,
    generate_filename,
)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {
        "VOLCENGINE_ACCESS_KEY_ID": "test_key",
        "VOLCENGINE_SECRET_ACCESS_KEY": "test_secret",
    }):
        yield


@pytest.fixture
def project_config():
    """Return default project config content."""
    return """
api:
  provider: volcengine
  model: "图片生成4.0"
defaults:
  width: 512
  height: 512
  style: "flat minimal"
output:
  base_dir: ./output
"""


class TestGenerateFilename:
    """Tests for filename generation."""

    def test_generate_filename_format(self):
        """Test filename format."""
        ts = datetime(2024, 12, 24, 14, 30, 0)
        filename = generate_filename("test prompt", ts)

        assert filename.startswith("20241224_143000_")
        assert filename.endswith(".png")

    def test_generate_filename_hash_consistency(self):
        """Test that same prompt produces same hash."""
        ts = datetime(2024, 12, 24, 14, 30, 0)
        filename1 = generate_filename("test prompt", ts)
        filename2 = generate_filename("test prompt", ts)

        assert filename1 == filename2

    def test_generate_filename_different_prompts(self):
        """Test that different prompts produce different hashes."""
        ts = datetime(2024, 12, 24, 14, 30, 0)
        filename1 = generate_filename("prompt one", ts)
        filename2 = generate_filename("prompt two", ts)

        assert filename1 != filename2


class TestGenerationContext:
    """Tests for GenerationContext."""

    def test_context_defaults(self):
        """Test context with default values."""
        ctx = GenerationContext(
            prompt="test",
            width=512,
            height=512,
            model="图片生成4.0",
        )
        assert ctx.style == ""
        assert ctx.negative_prompt == ""
        assert ctx.seed is None

    def test_resolve_prompt_with_style(self):
        """Test prompt resolution with style."""
        ctx = GenerationContext(
            prompt="cat icon",
            width=512,
            height=512,
            model="图片生成4.0",
            style="flat minimal",
        )
        resolved = ctx.resolve_prompt()

        assert resolved == "flat minimal, cat icon"
        assert ctx.resolved_prompt == resolved

    def test_resolve_prompt_without_style(self):
        """Test prompt resolution without style."""
        ctx = GenerationContext(
            prompt="cat icon",
            width=512,
            height=512,
            model="图片生成4.0",
        )
        resolved = ctx.resolve_prompt()

        assert resolved == "cat icon"

    def test_to_dict(self):
        """Test context serialization."""
        ctx = GenerationContext(
            prompt="test",
            width=512,
            height=512,
            model="图片生成4.0",
            style="minimal",
        )
        ctx.resolve_prompt()
        data = ctx.to_dict()

        assert data["prompt"] == "test"
        assert data["resolved_prompt"] == "minimal, test"
        assert data["width"] == 512
        assert data["model"] == "图片生成4.0"


class TestGenerationPipeline:
    """Tests for GenerationPipeline."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = MagicMock()
        config.api.model = "图片生成4.0"
        config.api.timeout = 60
        config.api.max_retries = 3
        config.api.retry_delay = 1.0
        config.defaults.width = 1024
        config.defaults.height = 1024
        config.defaults.style = "flat minimal"
        config.defaults.negative_prompt = ""
        config.output.base_dir = "./output"
        return config

    def test_create_context_with_defaults(self, mock_config):
        """Test context creation uses config defaults."""
        pipeline = GenerationPipeline(config=mock_config)
        ctx = pipeline.create_context(prompt="test prompt")

        assert ctx.prompt == "test prompt"
        assert ctx.width == 1024
        assert ctx.height == 1024
        assert ctx.style == "flat minimal"
        assert ctx.model == "图片生成4.0"

    def test_create_context_with_overrides(self, mock_config):
        """Test context creation with overrides."""
        pipeline = GenerationPipeline(config=mock_config)
        ctx = pipeline.create_context(
            prompt="test",
            width=512,
            height=512,
            style="custom style",
        )

        assert ctx.width == 512
        assert ctx.height == 512
        assert ctx.style == "custom style"

    def test_dry_run(self, mock_config):
        """Test dry run preview."""
        pipeline = GenerationPipeline(config=mock_config)
        ctx = pipeline.create_context(prompt="test prompt")
        preview = pipeline.dry_run(ctx)

        assert "prompt" in preview
        assert "resolved_prompt" in preview
        assert "model" in preview
        assert "dimensions" in preview
        assert "api_call" in preview
        assert "Would call" in preview["api_call"]


class TestGenerateCommand:
    """Tests for img generate command."""

    def test_generate_help(self, runner):
        """Test generate --help shows usage."""
        result = runner.invoke(cli, ["generate", "--help"])

        assert result.exit_code == 0
        assert "Generate an image" in result.output
        assert "--prompt" in result.output
        assert "--dry-run" in result.output

    def test_generate_no_config(self, runner):
        """Test generate fails without project config."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["generate", "--prompt", "test"])

        # Should fail - either config not found or API keys not set
        assert result.exit_code == 1

    def test_generate_no_prompt(self, runner, project_config):
        """Test generate fails without prompt."""
        with runner.isolated_filesystem():
            Path("imgcreator.yaml").write_text(project_config)
            result = runner.invoke(cli, ["generate"])

        assert result.exit_code == 1
        assert "prompt" in result.output.lower()

    def test_generate_dry_run(self, runner, project_config, mock_env):
        """Test generate --dry-run shows preview."""
        with runner.isolated_filesystem():
            Path("imgcreator.yaml").write_text(project_config)
            result = runner.invoke(
                cli, ["generate", "--prompt", "test icon", "--dry-run"]
            )

        assert result.exit_code == 0
        assert "Dry Run" in result.output
        assert "test icon" in result.output
        assert "No API call" in result.output

    def test_generate_dry_run_json(self, runner, project_config, mock_env):
        """Test generate --dry-run with JSON output."""
        with runner.isolated_filesystem():
            Path("imgcreator.yaml").write_text(project_config)
            result = runner.invoke(
                cli,
                ["generate", "--prompt", "test", "--dry-run", "--output-format", "json"],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "prompt" in data
        assert "resolved_prompt" in data
        assert "model" in data

    def test_generate_dry_run_yaml(self, runner, project_config, mock_env):
        """Test generate --dry-run with YAML output."""
        with runner.isolated_filesystem():
            Path("imgcreator.yaml").write_text(project_config)
            result = runner.invoke(
                cli,
                ["generate", "--prompt", "test", "--dry-run", "--output-format", "yaml"],
            )

        assert result.exit_code == 0
        data = yaml.safe_load(result.output)
        assert "prompt" in data

    def test_generate_with_overrides(self, runner, project_config, mock_env):
        """Test generate with option overrides in dry-run."""
        with runner.isolated_filesystem():
            Path("imgcreator.yaml").write_text(project_config)
            result = runner.invoke(
                cli,
                [
                    "generate",
                    "--prompt", "custom prompt",
                    "--width", "256",
                    "--height", "256",
                    "--style", "custom style",
                    "--dry-run",
                    "--output-format", "json",
                ],
            )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "256x256" in data["dimensions"]
        assert "custom style" in data["resolved_prompt"]

    def test_generate_sample_mode(self, runner, project_config, mock_env):
        """Test generate --sample uses default prompt."""
        with runner.isolated_filesystem():
            Path("imgcreator.yaml").write_text(project_config)
            result = runner.invoke(
                cli, ["generate", "--sample", "--dry-run"]
            )

        assert result.exit_code == 0
        assert "sample" in result.output.lower()


class TestPipelineResult:
    """Tests for PipelineResult."""

    def test_result_success(self):
        """Test successful result."""
        result = PipelineResult(
            success=True,
            output_path=Path("output/test.png"),
            duration_ms=1234,
        )
        assert result.success is True
        assert result.output_path == Path("output/test.png")

    def test_result_failure(self):
        """Test failed result."""
        result = PipelineResult(
            success=False,
            error_message="API error",
            duration_ms=500,
        )
        assert result.success is False
        assert result.error_message == "API error"

    def test_result_to_dict(self):
        """Test result serialization."""
        ctx = GenerationContext(
            prompt="test",
            width=512,
            height=512,
            model="图片生成4.0",
        )
        result = PipelineResult(
            success=True,
            output_path=Path("output/test.png"),
            duration_ms=1000,
            context=ctx,
        )
        data = result.to_dict()

        assert data["success"] is True
        assert data["output_path"] == "output/test.png"
        assert data["duration_ms"] == 1000
        assert "context" in data


class TestPipelineIntegration:
    """Integration tests for pipeline with mocked API."""

    @pytest.fixture
    def mock_generation_result(self):
        """Create a mock successful generation result."""
        return GenerationResult(
            status=GenerationStatus.SUCCESS,
            images=[b"fake image data"],
            request_id="test-123",
            seed=42,
            duration_ms=1500,
        )

    def test_pipeline_run_success(self, mock_env, mock_generation_result, tmp_path):
        """Test successful pipeline run with mocked API."""
        # Create mock config
        config = MagicMock()
        config.api.model = "图片生成4.0"
        config.api.timeout = 60
        config.api.max_retries = 3
        config.api.retry_delay = 1.0
        config.defaults.width = 512
        config.defaults.height = 512
        config.defaults.style = ""
        config.defaults.negative_prompt = ""
        config.defaults.reference_image = None  # No reference image for this test
        config.output.base_dir = str(tmp_path)

        # Create mock client
        mock_client = MagicMock()
        mock_client.generate.return_value = mock_generation_result

        # Run pipeline
        pipeline = GenerationPipeline(config=config, client=mock_client)
        ctx = pipeline.create_context(prompt="test prompt", output_dir=tmp_path)
        result = pipeline.run(ctx)

        assert result.success is True
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.duration_ms >= 0  # May be 0 if very fast
        mock_client.generate.assert_called_once()

    def test_pipeline_run_failure(self, mock_env, tmp_path):
        """Test pipeline run with API failure."""
        config = MagicMock()
        config.api.model = "图片生成4.0"
        config.api.timeout = 60
        config.api.max_retries = 3
        config.api.retry_delay = 1.0
        config.defaults.width = 512
        config.defaults.height = 512
        config.defaults.style = ""
        config.defaults.negative_prompt = ""
        config.defaults.reference_image = None  # No reference image for this test
        config.output.base_dir = str(tmp_path)

        # Create mock client that returns failure
        mock_client = MagicMock()
        mock_client.generate.return_value = GenerationResult(
            status=GenerationStatus.FAILED,
            images=[],
            error_message="API rate limit exceeded",
        )

        pipeline = GenerationPipeline(config=config, client=mock_client)
        ctx = pipeline.create_context(prompt="test", output_dir=tmp_path)
        result = pipeline.run(ctx)

        assert result.success is False
        assert "rate limit" in result.error_message.lower()

