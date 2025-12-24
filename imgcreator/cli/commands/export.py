"""Export command for imgcreator - export images to multiple sizes."""

import json
import sys
from pathlib import Path

import click
import yaml

from imgcreator.export.profiles import (
    ANDROID_PROFILE,
    IOS_PROFILE,
    ExportProfile,
    SizeProfile,
    get_profile,
    parse_custom_size,
)
from imgcreator.export.resize import (
    ExportError,
    ImageNotFoundError,
    export_image,
    load_image,
)


@click.command()
@click.argument("images", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--profile",
    type=click.Choice(["ios", "android"]),
    help="Export profile to use",
)
@click.option(
    "--size",
    type=str,
    help="Custom size (e.g., 100x100)",
)
@click.option("--all", "export_all", is_flag=True, help="Apply all configured profiles")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="export",
    help="Output directory (default: export/)",
)
@click.option(
    "--maintain-aspect/--no-maintain-aspect",
    default=True,
    help="Maintain aspect ratio for custom sizes",
)
@click.option("--dry-run", is_flag=True, help="Preview without exporting")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.pass_context
def export(
    ctx: click.Context,
    images: tuple[str, ...],
    profile: str | None,
    size: str | None,
    export_all: bool,
    output: str,
    maintain_aspect: bool,
    dry_run: bool,
    output_format: str,
) -> None:
    """Export images to multiple sizes.

    Exports images using iOS, Android, or custom size profiles.

    \b
    Examples:
        img export image.png --profile ios        # iOS @1x/@2x/@3x
        img export image.png --profile android   # Android densities
        img export image.png --size 100x100      # Custom size
        img export *.png --all                   # All profiles
        img export --dry-run                     # Preview only
    """
    # Determine source images
    if images:
        image_paths = [Path(img) for img in images]
    else:
        # Default to output directory
        output_dir = Path("output")
        if not output_dir.exists():
            click.echo(
                click.style("✗ ", fg="red")
                + f"Output directory not found: {output_dir}\n"
                "Generate some images first or specify image paths."
            )
            sys.exit(1)
        image_paths = list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))

    if not image_paths:
        click.echo(click.style("✗ ", fg="red") + "No images found to export.")
        sys.exit(1)

    # Determine export profiles
    profiles: list[ExportProfile] = []

    if export_all:
        profiles = [IOS_PROFILE, ANDROID_PROFILE]
        if size:
            size_tuple = parse_custom_size(size)
            if size_tuple:
                profiles.append(SizeProfile("custom", "Custom size", *size_tuple))
    elif profile:
        profile_obj = get_profile(profile)
        if profile_obj:
            profiles = [profile_obj]
    elif size:
        size_tuple = parse_custom_size(size)
        if not size_tuple:
            click.echo(
                click.style("✗ ", fg="red")
                + f"Invalid size format: {size}. Use WIDTHxHEIGHT (e.g., 100x100)"
            )
            sys.exit(1)
        profiles = [SizeProfile("custom", "Custom size", *size_tuple)]
    else:
        click.echo(
            click.style("✗ ", fg="red")
            + "Specify --profile, --size, or --all"
        )
        sys.exit(1)

    output_dir = Path(output)

    # Dry run mode
    if dry_run:
        previews = []
        for image_path in image_paths:
            try:
                image = load_image(image_path)
                width, height = image.size
                base_name = image_path.stem

                for profile_obj in profiles:
                    if isinstance(profile_obj, SizeProfile):
                        previews.append({
                            "image": str(image_path),
                            "profile": "custom",
                            "size": f"{profile_obj.width}x{profile_obj.height}",
                            "output": (
                                f"{output_dir}/custom/"
                                f"{base_name}_{profile_obj.width}x{profile_obj.height}.png"
                            ),
                        })
                    elif profile_obj.name == "ios":
                        for scale_name in IOS_PROFILE.scales.keys():
                            previews.append({
                                "image": str(image_path),
                                "profile": "ios",
                                "scale": scale_name,
                                "output": f"{output_dir}/ios/{base_name}{scale_name}.png",
                            })
                    elif profile_obj.name == "android":
                        for density in ANDROID_PROFILE.scales.keys():
                            previews.append({
                                "image": str(image_path),
                                "profile": "android",
                                "density": density,
                                "output": f"{output_dir}/android/{density}/{base_name}.png",
                            })
            except ImageNotFoundError as e:
                previews.append({"image": str(image_path), "error": str(e)})

        _output_preview(previews, output_format)
        return

    # Actual export
    results = []
    errors = []

    with click.progressbar(
        image_paths, label="Exporting", show_pos=True, show_percent=True
    ) as bar:
        for image_path in bar:
            try:
                for profile_obj in profiles:
                    exported = export_image(
                        image_path,
                        profile_obj,
                        output_dir,
                        maintain_aspect=maintain_aspect,
                    )
                    results.extend(exported)
            except (ImageNotFoundError, ExportError) as e:
                errors.append({"image": str(image_path), "error": str(e)})
            except Exception as e:
                errors.append({"image": str(image_path), "error": f"Unexpected error: {e}"})

    # Summary
    if output_format == "json":
        click.echo()
        click.echo(
            json.dumps(
                {
                    "total_images": len(image_paths),
                    "exported_files": len(results),
                    "error_count": len(errors),
                    "files": [str(p) for p in results],
                    "errors": errors,
                },
                indent=2,
            )
        )
    elif output_format == "yaml":
        click.echo()
        click.echo(
            yaml.dump(
                {
                    "total_images": len(image_paths),
                    "exported_files": len(results),
                    "error_count": len(errors),
                    "files": [str(p) for p in results],
                    "errors": errors,
                },
                default_flow_style=False,
            )
        )
    else:  # text
        click.echo()
        click.echo(click.style("Export Summary:", fg="cyan", bold=True))
        click.echo(f"  Images processed: {len(image_paths)}")
        click.echo(f"  Files exported:   {click.style(str(len(results)), fg='green')}")
        if errors:
            click.echo(f"  Errors:           {click.style(str(len(errors)), fg='red')}")
            click.echo()
            click.echo(click.style("Errors:", fg="red", bold=True))
            for error in errors:
                click.echo(f"  {error['image']}: {error['error']}")
        click.echo()
        click.echo(f"  Output directory: {output_dir}")

    if errors:
        sys.exit(1)


def _output_preview(previews: list[dict], format: str) -> None:
    """Output dry-run preview."""
    if format == "json":
        click.echo(json.dumps({"preview": previews}, indent=2))
    elif format == "yaml":
        click.echo(yaml.dump({"preview": previews}, default_flow_style=False))
    else:  # text
        click.echo()
        click.echo(click.style("Export Preview:", fg="yellow", bold=True))
        click.echo()

        for preview in previews:
            if "error" in preview:
                click.echo(f"  {click.style('✗', fg='red')} {preview['image']}: {preview['error']}")
            else:
                click.echo(f"  {click.style('→', fg='cyan')} {preview['image']}")
                if "profile" in preview:
                    click.echo(f"    Profile: {preview['profile']}")
                if "scale" in preview:
                    click.echo(f"    Scale: {preview['scale']}")
                if "density" in preview:
                    click.echo(f"    Density: {preview['density']}")
                if "size" in preview:
                    click.echo(f"    Size: {preview['size']}")
                click.echo(f"    Output: {preview['output']}")
                click.echo()

        click.echo(click.style("  [No files exported]", fg="yellow"))

