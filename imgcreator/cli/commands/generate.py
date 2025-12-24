"""Generate command for imgcreator - creates images from prompts."""

import json
import sys
import time
from pathlib import Path

import click
import yaml

from imgcreator.core.config import ConfigError, ConfigLoader, ConfigNotFoundError
from imgcreator.core.pipeline import create_pipeline
from imgcreator.core.series import (
    SeriesError,
    SeriesNotFoundError,
    load_series,
)


@click.command()
@click.option("--prompt", "-p", type=str, help="Generation prompt (overrides config)")
@click.option("--width", "-w", type=int, help="Image width in pixels")
@click.option("--height", "-h", type=int, help="Image height in pixels")
@click.option("--model", "-m", type=str, help="Model to use for generation")
@click.option("--style", "-s", type=str, help="Style prefix for prompt")
@click.option("--seed", type=int, help="Random seed for reproducibility")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--sample", is_flag=True, help="Generate a single sample image")
@click.option(
    "--series",
    type=str,
    default=None,
    help="Generate from series (name or empty for default)",
)
@click.option("--limit", type=int, help="Limit number of items to generate (for testing)")
@click.option("--dry-run", is_flag=True, help="Preview without making API call")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.pass_context
def generate(
    ctx: click.Context,
    prompt: str | None,
    width: int | None,
    height: int | None,
    model: str | None,
    style: str | None,
    seed: int | None,
    output: str | None,
    sample: bool,
    series: str | None,
    limit: int | None,
    dry_run: bool,
    output_format: str,
) -> None:
    """Generate an image from a prompt or series.

    Uses configuration from imgcreator.yaml with optional overrides.

    \b
    Examples:
        img generate                        # Use config defaults
        img generate --prompt "cat icon"    # Override prompt
        img generate --series app-icons     # Generate from series
        img generate --series              # Use default series
        img generate --sample               # Single sample mode
        img generate --dry-run              # Preview without API call
        img generate -v                     # Verbose output
    """
    verbose = ctx.obj.get("verbose", False)

    # Handle series generation
    if series is not None or (series == "" and prompt is None and not sample):
        try:
            _generate_series(
                series_name=series if series else None,
                limit=limit,
                dry_run=dry_run,
                output_format=output_format,
                verbose=verbose,
            )
            return
        except SeriesNotFoundError as e:
            # If series explicitly requested, fail
            if series is not None:
                click.echo(click.style("✗ ", fg="red") + str(e))
                sys.exit(1)
            # Otherwise fall through to single generation
        except SeriesError as e:
            click.echo(click.style("✗ ", fg="red") + str(e))
            sys.exit(1)

    try:
        # Load configuration
        loader = ConfigLoader(verbose=verbose)
        try:
            config = loader.load()
        except ConfigNotFoundError as e:
            click.echo(click.style("✗ ", fg="red") + str(e))
            sys.exit(1)

        # Determine prompt
        if prompt is None and not sample:
            # Check for default prompt in config
            default_prompt = config._raw.get("generation", {}).get("prompt")
            if default_prompt:
                prompt = default_prompt
            else:
                click.echo(
                    click.style("✗ ", fg="red")
                    + "No prompt provided. Use --prompt or set generation.prompt in config."
                )
                sys.exit(1)

        # For sample mode without prompt, use a default
        if sample and prompt is None:
            prompt = "sample image"

        # Create pipeline
        project_path = Path.cwd()
        with create_pipeline(config=config, verbose=verbose, project_path=project_path) as pipeline:
            # Create generation context
            output_dir = Path(output) if output else None
            context = pipeline.create_context(
                prompt=prompt,
                width=width,
                height=height,
                model=model,
                style=style,
                output_dir=output_dir,
                seed=seed,
            )

            # Dry run mode
            if dry_run:
                preview = pipeline.dry_run(context)
                _output_result(preview, output_format, is_dry_run=True)
                return

            # Run generation
            click.echo(
                f"Generating image: {click.style(context.resolved_prompt[:60], fg='cyan')}..."
            )

            result = pipeline.run(context)

            if result.success:
                _output_result(result.to_dict(), output_format)
                if output_format == "text":
                    click.echo()
                    click.echo(
                        click.style("✓ ", fg="green")
                        + f"Generated in {result.duration_ms}ms"
                    )
                    click.echo(f"  Output: {result.output_path}")
            else:
                _output_error(result.error_message or "Unknown error", output_format)
                sys.exit(1)

    except ConfigError as e:
        click.echo(click.style("✗ Configuration error: ", fg="red") + str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nAborted.")
        sys.exit(130)


def _output_result(data: dict, format: str, is_dry_run: bool = False) -> None:
    """Output result in specified format."""
    if format == "json":
        click.echo(json.dumps(data, indent=2, default=str))
    elif format == "yaml":
        click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    else:  # text
        if is_dry_run:
            click.echo()
            click.echo(click.style("Dry Run Preview:", fg="yellow", bold=True))
            click.echo()
            click.echo(f"  Prompt:           {data.get('prompt', '')}")
            click.echo(f"  Resolved Prompt:  {data.get('resolved_prompt', '')}")
            click.echo(f"  Model:            {data.get('model', '')}")
            click.echo(f"  Dimensions:       {data.get('dimensions', '')}")
            click.echo(f"  Style:            {data.get('style', '')}")
            click.echo(f"  Negative Prompt:  {data.get('negative_prompt', '')}")
            click.echo(f"  Seed:             {data.get('seed', 'random')}")
            click.echo(f"  Output Path:      {data.get('output_path', '')}")
            click.echo()
            click.echo(click.style("  [No API call made]", fg="yellow"))


def _output_error(message: str, format: str) -> None:
    """Output error in specified format."""
    if format == "json":
        click.echo(json.dumps({"success": False, "error": message}, indent=2))
    elif format == "yaml":
        click.echo(yaml.dump({"success": False, "error": message}))
    else:
        click.echo(click.style("✗ ", fg="red") + message)


def _generate_series(
    series_name: str | None,
    limit: int | None,
    dry_run: bool,
    output_format: str,
    verbose: bool,
) -> None:
    """Generate images from a series definition."""
    from imgcreator.core.config import ConfigLoader
    from imgcreator.core.pipeline import create_pipeline

    # Load series
    try:
        series = load_series(name=series_name)
    except SeriesNotFoundError as e:
        click.echo(click.style("✗ ", fg="red") + str(e))
        sys.exit(1)

    # Load config
    loader = ConfigLoader(verbose=verbose)
    try:
        config = loader.load()
    except ConfigNotFoundError as e:
        click.echo(click.style("✗ ", fg="red") + str(e))
        sys.exit(1)

    # Apply limit if specified
    items = series.items[:limit] if limit else series.items
    total = len(items)

    if total == 0:
        click.echo(click.style("✗ ", fg="red") + "Series has no items")
        sys.exit(1)

    click.echo(f"Series: {click.style(series.name, fg='cyan', bold=True)}")
    click.echo(f"Items: {total}")
    click.echo()

    # Dry run mode
    if dry_run:
        previews = []
        for item in items:
            context = _create_item_context(series, item, config, None)
            with create_pipeline(config=config, verbose=verbose) as pipeline:
                preview = pipeline.dry_run(context)
                preview["item_id"] = item.id
                previews.append(preview)

        if output_format == "json":
            click.echo(json.dumps({"series": series.name, "items": previews}, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump({"series": series.name, "items": previews}))
        else:
            for preview in previews:
                click.echo(f"Item: {click.style(preview['item_id'], fg='cyan')}")
                click.echo(f"  Resolved Prompt: {preview['resolved_prompt']}")
                click.echo(f"  Model: {preview['model']}")
                click.echo(f"  Dimensions: {preview['dimensions']}")
                click.echo()
        return

    # Actual generation
    results = []
    errors = []
    start_time = time.time()
    project_path = Path.cwd()

    with create_pipeline(config=config, verbose=verbose, project_path=project_path) as pipeline:
        with click.progressbar(
            items, label="Generating", show_pos=True, show_percent=True
        ) as bar:
            for item in bar:
                try:
                    # Create context for this item
                    context = _create_item_context(series, item, config, None)
                    # Set series info for history tracking
                    context.series = series.name
                    context.item_id = item.id

                    # Generate
                    result = pipeline.run(context)

                    if result.success:
                        results.append({
                            "item_id": item.id,
                            "success": True,
                            "output_path": str(result.output_path),
                            "duration_ms": result.duration_ms,
                        })
                    else:
                        errors.append({
                            "item_id": item.id,
                            "error": result.error_message,
                        })
                        results.append({
                            "item_id": item.id,
                            "success": False,
                            "error": result.error_message,
                        })

                    # Rate limiting delay (small delay between requests)
                    if item != items[-1]:  # Don't delay after last item
                        time.sleep(0.5)

                except KeyboardInterrupt:
                    click.echo("\n\nAborted.")
                    sys.exit(130)
                except Exception as e:
                    error_msg = str(e)
                    errors.append({"item_id": item.id, "error": error_msg})
                    results.append({
                        "item_id": item.id,
                        "success": False,
                        "error": error_msg,
                    })

    # Summary
    total_time = int((time.time() - start_time) * 1000)
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = len(errors)

    if output_format == "json":
        click.echo()
        click.echo(
            json.dumps(
                {
                    "series": series.name,
                    "total": total,
                    "success": success_count,
                    "failed": fail_count,
                    "duration_ms": total_time,
                    "results": results,
                },
                indent=2,
                default=str,
            )
        )
    elif output_format == "yaml":
        click.echo()
        click.echo(
            yaml.dump(
                {
                    "series": series.name,
                    "total": total,
                    "success": success_count,
                    "failed": fail_count,
                    "duration_ms": total_time,
                    "results": results,
                },
                default_flow_style=False,
            )
        )
    else:
        click.echo()
        click.echo(click.style("Summary:", fg="cyan", bold=True))
        click.echo(f"  Total:    {total}")
        click.echo(f"  Success:  {click.style(str(success_count), fg='green')}")
        if fail_count > 0:
            click.echo(f"  Failed:   {click.style(str(fail_count), fg='red')}")
        click.echo(f"  Duration: {total_time}ms")
        click.echo()

        if errors:
            click.echo(click.style("Errors:", fg="red", bold=True))
            for error in errors:
                click.echo(f"  {error['item_id']}: {error['error']}")

    if fail_count > 0:
        sys.exit(1)


def _create_item_context(series, item, config, output_dir):
    """Create a generation context for a series item."""
    from pathlib import Path

    from imgcreator.core.pipeline import GenerationContext

    # Merge series config with project config
    width = series.config.width or config.defaults.width
    height = series.config.height or config.defaults.height
    model = series.config.model or config.api.model
    style = series.config.style or config.defaults.style
    negative_prompt = (
        series.config.negative_prompt or config.defaults.negative_prompt
    )
    seed = series.config.seed

    # Use item data as template context
    template_context = item.data.copy()
    template_defaults = series.defaults.copy()

    # Create context with template support
    context = GenerationContext(
        prompt=series.template,
        width=width,
        height=height,
        model=model,
        style=style,
        negative_prompt=negative_prompt,
        output_dir=Path(output_dir) if output_dir else Path(config.output.base_dir),
        seed=seed,
        template_context=template_context,
        template_defaults=template_defaults,
    )

    # Resolve prompt with template
    context.resolve_prompt(use_template=True)

    return context

