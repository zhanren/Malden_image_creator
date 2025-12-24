"""Config command for imgcreator - display and validate configuration."""

import os
from pathlib import Path

import click
import yaml

from imgcreator.api.volcengine import VolcengineClient
from imgcreator.core.config import (
    ConfigError,
    ConfigLoader,
    ConfigNotFoundError,
    ConfigValidationError,
)


@click.command()
@click.option("--validate", "-c", is_flag=True, help="Validate configuration only")
@click.option("--global", "show_global", is_flag=True, help="Show global config location")
@click.option("--test-auth", is_flag=True, help="Test API authentication")
@click.pass_context
def config(ctx: click.Context, validate: bool, show_global: bool, test_auth: bool) -> None:
    """Display or validate project configuration.

    Shows the resolved configuration with all layers merged.

    \b
    Examples:
        img config              # Show resolved config
        img -v config           # Show config with verbose loading info
        img config --validate   # Validate config without showing
        img config --global     # Show global config path
        img config --test-auth  # Test API authentication
    """
    verbose = ctx.obj.get("verbose", False)

    if test_auth:
        _test_authentication(verbose)
        return

    if show_global:
        global_path = ConfigLoader.GLOBAL_CONFIG_PATH
        click.echo(f"Global config path: {global_path}")
        if global_path.exists():
            click.echo(click.style("  ✓ File exists", fg="green"))
        else:
            click.echo(click.style("  ✗ File does not exist", fg="yellow"))
        return

    try:
        loader = ConfigLoader(project_path=Path.cwd(), verbose=verbose)
        config_obj = loader.load()

        if validate:
            click.echo(click.style("✓ Configuration is valid", fg="green"))
            return

        # Display resolved configuration
        click.echo(click.style("Resolved Configuration:", fg="cyan", bold=True))
        click.echo()

        # Convert config to dict for display
        config_dict = {
            "api": {
                "provider": config_obj.api.provider,
                "model": config_obj.api.model,
                "timeout": config_obj.api.timeout,
                "max_retries": config_obj.api.max_retries,
            },
            "defaults": {
                "width": config_obj.defaults.width,
                "height": config_obj.defaults.height,
                "style": config_obj.defaults.style or "(not set)",
            },
            "output": {
                "base_dir": config_obj.output.base_dir,
                "naming": config_obj.output.naming,
                "format": config_obj.output.format,
            },
        }

        yaml_output = yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)
        click.echo(yaml_output)

    except ConfigNotFoundError as e:
        click.echo(click.style("✗ ", fg="red") + str(e))
        raise SystemExit(1)

    except ConfigValidationError as e:
        click.echo(click.style("✗ Configuration invalid:", fg="red"))
        click.echo(str(e))
        raise SystemExit(1)

    except ConfigError as e:
        click.echo(click.style("✗ Configuration error: ", fg="red") + str(e))
        raise SystemExit(1)


def _test_authentication(verbose: bool) -> None:
    """Test API authentication."""
    click.echo(click.style("Testing API Authentication...", fg="cyan", bold=True))
    click.echo()

    # Check environment variables
    access_key_id = os.environ.get("VOLCENGINE_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("VOLCENGINE_SECRET_ACCESS_KEY", "")

    if not access_key_id:
        click.echo(
            click.style("✗ ", fg="red")
            + "VOLCENGINE_ACCESS_KEY_ID not set"
        )
        click.echo("  Set it with: export VOLCENGINE_ACCESS_KEY_ID=your_key_id")
        click.echo("  Or add it to .env file")
        raise SystemExit(1)

    if not secret_key:
        click.echo(
            click.style("✗ ", fg="red")
            + "VOLCENGINE_SECRET_ACCESS_KEY not set"
        )
        click.echo("  Set it with: export VOLCENGINE_SECRET_ACCESS_KEY=your_secret")
        click.echo("  Or add it to .env file")
        raise SystemExit(1)

    click.echo(
        click.style("✓ ", fg="green")
        + f"Access Key ID: {access_key_id[:8]}...{access_key_id[-4:]}"
    )
    click.echo(
        click.style("✓ ", fg="green")
        + f"Secret Key: {'*' * 8}...{secret_key[-4:] if len(secret_key) > 4 else '****'}"
    )
    click.echo()

    # Test with a minimal API call
    click.echo("Testing API connection...")
    try:
        client = VolcengineClient(verbose=verbose)
        errors = client.validate_config()
        if errors:
            click.echo(click.style("✗ ", fg="red") + "Configuration validation failed:")
            for error in errors:
                click.echo(f"  - {error}")
            raise SystemExit(1)

        # Try a dry-run generation to test auth
        from imgcreator.api.base import GenerationRequest

        request = GenerationRequest(
            prompt="test",
            width=512,
            height=512,
        )

        click.echo("Making test API call...")
        result = client.generate(request)

        if result.status.value == "failed":
            error_msg = result.error_message or "Unknown error"
            click.echo(click.style("✗ ", fg="red") + "Authentication failed")
            click.echo()
            # Show the actual error message from API
            click.echo(f"Error: {error_msg}")
            click.echo()
            click.echo("Troubleshooting:")
            click.echo("  1. Verify your Access Key ID and Secret are correct in .env file")
            click.echo("  2. Check that your API key has permissions for Visual AI service")
            click.echo("  3. Ensure Visual AI service is enabled in your Volcengine account")
            click.echo("  4. Verify the service is available in region: cn-north-1")
            click.echo("  5. Check your Volcengine console: https://console.volcengine.com/")
            if not verbose:
                click.echo("  6. Use --verbose for more details: img --verbose config --test-auth")
            raise SystemExit(1)

        click.echo(click.style("✓ ", fg="green") + "Authentication successful!")
        click.echo("  API responded successfully")

    except Exception as e:
        click.echo(click.style("✗ ", fg="red") + f"Error: {e}")
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
        raise SystemExit(1)

