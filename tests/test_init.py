"""Tests for the init command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from imgcreator.cli.main import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def isolated_runner(runner):
    """Create an isolated filesystem for testing."""
    with runner.isolated_filesystem():
        yield runner


class TestInitCommand:
    """Tests for img init command."""

    def test_init_creates_directory_structure(self, isolated_runner):
        """Test that init creates expected directories."""
        result = isolated_runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert Path("imgcreator.yaml").exists()
        assert Path("series").is_dir()
        assert Path("output").is_dir()
        assert Path("history").is_dir()
        assert Path(".env.example").exists()
        assert Path(".gitignore").exists()

    def test_init_creates_named_project(self, isolated_runner):
        """Test that init <name> creates project in named folder."""
        result = isolated_runner.invoke(cli, ["init", "my-project"])

        assert result.exit_code == 0
        assert Path("my-project").is_dir()
        assert Path("my-project/imgcreator.yaml").exists()
        assert Path("my-project/series").is_dir()
        assert Path("my-project/output").is_dir()
        assert Path("my-project/history").is_dir()

    def test_init_config_file_content(self, isolated_runner):
        """Test that imgcreator.yaml has expected content."""
        isolated_runner.invoke(cli, ["init"])

        config_content = Path("imgcreator.yaml").read_text()
        assert "api:" in config_content
        assert "provider: volcengine" in config_content
        assert "defaults:" in config_content
        assert "width: 1024" in config_content

    def test_init_env_example_content(self, isolated_runner):
        """Test that .env.example has expected content."""
        isolated_runner.invoke(cli, ["init"])

        env_content = Path(".env.example").read_text()
        assert "VOLCENGINE_API_KEY" in env_content

    def test_init_existing_project_warning(self, isolated_runner):
        """Test that init warns on existing project."""
        # First init
        isolated_runner.invoke(cli, ["init"])

        # Second init should warn
        result = isolated_runner.invoke(cli, ["init"], input="n\n")

        assert "already exists" in result.output
        assert result.exit_code == 0

    def test_init_existing_project_force(self, isolated_runner):
        """Test that init --force overwrites without prompt."""
        # First init
        isolated_runner.invoke(cli, ["init"])

        # Config exists from first init
        config_path = Path("imgcreator.yaml")

        # Force reinit
        result = isolated_runner.invoke(cli, ["init", "--force"])

        assert result.exit_code == 0
        # File should still exist (preserved, not recreated)
        assert config_path.exists()

    def test_init_success_message(self, isolated_runner):
        """Test that init shows success message with next steps."""
        result = isolated_runner.invoke(cli, ["init"])

        assert "successfully" in result.output.lower()
        assert "Next steps" in result.output
        assert "VOLCENGINE_API_KEY" in result.output

    def test_init_verbose_mode(self, isolated_runner):
        """Test that verbose mode shows created files."""
        result = isolated_runner.invoke(cli, ["-v", "init"])

        assert result.exit_code == 0
        assert "Created:" in result.output

    def test_init_help(self, runner):
        """Test that init --help shows usage info."""
        result = runner.invoke(cli, ["init", "--help"])

        assert result.exit_code == 0
        assert "Initialize" in result.output
        assert "--force" in result.output


class TestDirectoryCreation:
    """Tests for directory creation logic."""

    def test_creates_nested_directories(self, isolated_runner):
        """Test that nested directories are created properly."""
        result = isolated_runner.invoke(cli, ["init", "deep/nested/project"])

        assert result.exit_code == 0
        assert Path("deep/nested/project/imgcreator.yaml").exists()

    def test_series_readme_created(self, isolated_runner):
        """Test that series directory contains README."""
        isolated_runner.invoke(cli, ["init"])

        readme_path = Path("series/README.md")
        assert readme_path.exists()
        assert "Example series" in readme_path.read_text()


class TestGitignore:
    """Tests for .gitignore creation."""

    def test_gitignore_ignores_output(self, isolated_runner):
        """Test that .gitignore includes output directory."""
        isolated_runner.invoke(cli, ["init"])

        gitignore_content = Path(".gitignore").read_text()
        assert "output/" in gitignore_content

    def test_gitignore_ignores_history(self, isolated_runner):
        """Test that .gitignore includes history directory."""
        isolated_runner.invoke(cli, ["init"])

        gitignore_content = Path(".gitignore").read_text()
        assert "history/" in gitignore_content

    def test_gitignore_ignores_env(self, isolated_runner):
        """Test that .gitignore includes .env file."""
        isolated_runner.invoke(cli, ["init"])

        gitignore_content = Path(".gitignore").read_text()
        assert ".env" in gitignore_content

