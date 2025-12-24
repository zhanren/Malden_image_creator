"""CLI entry point for imgcreator."""

from pathlib import Path

import click
from dotenv import load_dotenv

from imgcreator import __version__
from imgcreator.cli.commands.config import config
from imgcreator.cli.commands.export import export
from imgcreator.cli.commands.generate import generate
from imgcreator.cli.commands.history import history
from imgcreator.cli.commands.init import init


@click.group()
@click.version_option(version=__version__, prog_name="imgcreator")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AI Image Series Creator - Generate themed image assets with AI."""
    # Load .env file if it exists
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


# Register commands
cli.add_command(init)
cli.add_command(config)
cli.add_command(generate)
cli.add_command(history)
cli.add_command(export)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()

