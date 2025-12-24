"""Init command for imgcreator - creates project structure."""

from pathlib import Path

import click

# Default config template with comments and examples
DEFAULT_CONFIG = """\
# imgcreator configuration
# Documentation: https://github.com/malden/imgcreator

# API Configuration
api:
  provider: volcengine
  # Model options: "图片生成4.0", "文生图3.1"
  model: "图片生成4.0"

# Default generation settings
defaults:
  width: 1024
  height: 1024
  # Default style applied to all prompts
  style: "flat, minimal, modern"

# Output configuration
output:
  base_dir: ./output
  # Naming pattern: {timestamp}_{id}.png
  naming: "{timestamp}_{id}"

# Export profiles
export:
  ios:
    enabled: true
    scales: ["@1x", "@2x", "@3x"]
  android:
    enabled: true
    densities: ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"]
  custom:
    # Add custom sizes here
    # - width: 100
    #   height: 100
    #   suffix: "_thumb"
"""

ENV_EXAMPLE = """\
# imgcreator environment variables
# Copy this file to .env and fill in your API key

# Volcengine Jimeng AI API Key (required)
VOLCENGINE_API_KEY=your_api_key_here

# Optional: Access Key ID and Secret for Volcengine authentication
# VOLCENGINE_ACCESS_KEY_ID=your_access_key_id
# VOLCENGINE_SECRET_ACCESS_KEY=your_secret_access_key
"""

SERIES_EXAMPLE = """\
# Example series definition
# Place your series YAML files in this directory

# Example: app-icons.yaml
# name: app-icons
# template: "{{style}} icon of {{subject}}, {{constraints}}"
# defaults:
#   style: "flat, minimal, modern"
#   constraints: "single color, centered, no text"
# config:
#   width: 512
#   height: 512
# items:
#   - id: home
#     subject: "home house"
#   - id: settings
#     subject: "gear cog"
"""


def create_directory(path: Path, verbose: bool = False) -> bool:
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True)
        if verbose:
            click.echo(f"  Created: {path}/")
        return True
    return False


def create_file(path: Path, content: str, verbose: bool = False) -> bool:
    """Create file if it doesn't exist."""
    if not path.exists():
        path.write_text(content)
        if verbose:
            click.echo(f"  Created: {path}")
        return True
    return False


def is_existing_project(path: Path) -> bool:
    """Check if path contains an existing imgcreator project."""
    config_file = path / "imgcreator.yaml"
    return config_file.exists()


@click.command()
@click.argument("name", required=False, default=".")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing project")
@click.pass_context
def init(ctx: click.Context, name: str, force: bool) -> None:
    """Initialize a new imgcreator project.

    Creates project structure with configuration files.

    \b
    Examples:
        img init              # Initialize in current directory
        img init my-project   # Create new project folder
        img init . --force    # Reinitialize existing project
    """
    verbose = ctx.obj.get("verbose", False)

    # Resolve project path
    if name == ".":
        project_path = Path.cwd()
        project_name = project_path.name
    else:
        project_path = Path.cwd() / name
        project_name = name

    # Check for existing project
    if is_existing_project(project_path) and not force:
        click.echo(
            click.style("⚠️  ", fg="yellow")
            + f"Project already exists at {project_path}"
        )
        if not click.confirm("Do you want to reinitialize? (existing files will be preserved)"):
            click.echo("Aborted.")
            raise SystemExit(0)

    styled_name = click.style(project_name, fg="cyan", bold=True)
    click.echo(f"Initializing imgcreator project: {styled_name}")
    click.echo()

    # Create project root if needed
    if name != ".":
        create_directory(project_path, verbose)

    # Create directory structure
    directories = [
        project_path / "series",
        project_path / "output",
        project_path / "history",
    ]

    for dir_path in directories:
        create_directory(dir_path, verbose)

    # Create configuration files
    files_created = []

    config_path = project_path / "imgcreator.yaml"
    if create_file(config_path, DEFAULT_CONFIG, verbose):
        files_created.append("imgcreator.yaml")

    env_example_path = project_path / ".env.example"
    if create_file(env_example_path, ENV_EXAMPLE, verbose):
        files_created.append(".env.example")

    series_readme = project_path / "series" / "README.md"
    if create_file(series_readme, SERIES_EXAMPLE, verbose):
        files_created.append("series/README.md")

    # Create .gitignore if it doesn't exist
    gitignore_path = project_path / ".gitignore"
    gitignore_content = """\
# imgcreator generated files
output/
history/

# Environment
.env

# Python
__pycache__/
*.py[cod]
.venv/
"""
    if create_file(gitignore_path, gitignore_content, verbose):
        files_created.append(".gitignore")

    # Success message
    click.echo()
    click.echo(click.style("✅ Project initialized successfully!", fg="green", bold=True))
    click.echo()
    click.echo("Project structure:")
    click.echo(f"  {project_path}/")
    click.echo("  ├── imgcreator.yaml    # Project configuration")
    click.echo("  ├── .env.example       # API key template")
    click.echo("  ├── .gitignore         # Git ignore rules")
    click.echo("  ├── series/            # Series definitions")
    click.echo("  ├── output/            # Generated images")
    click.echo("  └── history/           # Generation history")
    click.echo()
    click.echo(click.style("Next steps:", fg="cyan", bold=True))
    click.echo("  1. Copy .env.example to .env and add your VOLCENGINE_API_KEY")
    click.echo("  2. Edit imgcreator.yaml to customize defaults")
    click.echo("  3. Create a series definition in series/")
    click.echo("  4. Run: img generate --sample")

