"""History command for imgcreator - view generation history."""

import json
import sys
from pathlib import Path

import click
import yaml

from imgcreator.core.history import HistoryError, create_manager


@click.command()
@click.argument("entry_id", required=False)
@click.option("--limit", "-n", type=int, help="Limit number of entries to show")
@click.option("--series", type=str, help="Filter by series name")
@click.option("--status", type=click.Choice(["success", "failed"]), help="Filter by status")
@click.option("--search", "-s", type=str, help="Search in prompts")
@click.option("--stats", is_flag=True, help="Show history statistics")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.pass_context
def history(
    ctx: click.Context,
    entry_id: str | None,
    limit: int | None,
    series: str | None,
    status: str | None,
    search: str | None,
    stats: bool,
    output_format: str,
) -> None:
    """View generation history.

    Lists recent generations or shows details of a specific entry.

    \b
    Examples:
        img history                    # List recent generations
        img history <id>              # Show details of specific entry
        img history --limit 10        # Show last 10 entries
        img history --series app-icons # Filter by series
        img history --search "icon"   # Search in prompts
        img history --stats           # Show statistics
    """
    try:
        manager = create_manager(project_path=Path.cwd())

        # Show statistics
        if stats:
            stats_data = manager.get_stats()
            _output_stats(stats_data, output_format)
            return

        # Show specific entry
        if entry_id:
            entry = manager.get_entry(entry_id)
            if entry is None:
                click.echo(click.style("✗ ", fg="red") + f"Entry '{entry_id}' not found")
                sys.exit(1)

            _output_entry(entry, output_format)
            return

        # List entries with filters
        if search or series or status:
            entries = manager.search(
                prompt=search,
                series=series,
                status=status,
                limit=limit,
            )
        else:
            entries = manager.list_entries(limit=limit)

        if not entries:
            click.echo("No history entries found.")
            return

        _output_entries(entries, output_format)

    except HistoryError as e:
        click.echo(click.style("✗ ", fg="red") + str(e))
        sys.exit(1)


def _output_entry(entry, format: str) -> None:
    """Output a single history entry."""
    if format == "json":
        click.echo(json.dumps(entry.to_dict(), indent=2, default=str))
    elif format == "yaml":
        click.echo(yaml.dump(entry.to_dict(), default_flow_style=False, allow_unicode=True))
    else:  # text
        click.echo()
        click.echo(click.style(f"Entry: {entry.id}", fg="cyan", bold=True))
        click.echo(f"  Timestamp:     {entry.timestamp}")
        status_color = "green" if entry.status == "success" else "red"
        click.echo(f"  Status:        {click.style(entry.status, fg=status_color)}")
        click.echo(f"  Prompt:        {entry.prompt}")
        click.echo(f"  Resolved:      {entry.resolved_prompt}")
        click.echo(f"  Model:         {entry.model}")
        width = entry.params.get("width", "N/A")
        height = entry.params.get("height", "N/A")
        click.echo(f"  Dimensions:   {width}x{height}")
        if entry.output_path:
            click.echo(f"  Output:        {entry.output_path}")
        if entry.series:
            click.echo(f"  Series:        {entry.series}")
        if entry.item_id:
            click.echo(f"  Item ID:       {entry.item_id}")
        if entry.seed is not None:
            click.echo(f"  Seed:          {entry.seed}")
        if entry.request_id:
            click.echo(f"  Request ID:    {entry.request_id}")
        click.echo(f"  Duration:      {entry.duration_ms}ms")
        if entry.error_message:
            click.echo(f"  Error:         {click.style(entry.error_message, fg='red')}")
        if entry.image_hash:
            click.echo(f"  Image Hash:    {entry.image_hash[:16]}...")


def _output_entries(entries: list, format: str) -> None:
    """Output a list of history entries."""
    if format == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2, default=str))
    elif format == "yaml":
        click.echo(yaml.dump([e.to_dict() for e in entries], default_flow_style=False))
    else:  # text
        click.echo()
        click.echo(click.style("Recent Generations:", fg="cyan", bold=True))
        click.echo()

        for entry in entries:
            status_color = "green" if entry.status == "success" else "red"
            status_icon = "✓" if entry.status == "success" else "✗"

            click.echo(
                f"  {click.style(status_icon, fg=status_color)} "
                f"{click.style(entry.id, fg='cyan')} "
                f"({entry.timestamp[:19]})"
            )
            click.echo(f"    {entry.resolved_prompt[:60]}...")
            if entry.series:
                click.echo(f"    Series: {entry.series}")
            if entry.output_path:
                click.echo(f"    Output: {entry.output_path}")
            click.echo()


def _output_stats(stats: dict, format: str) -> None:
    """Output history statistics."""
    if format == "json":
        click.echo(json.dumps(stats, indent=2))
    elif format == "yaml":
        click.echo(yaml.dump(stats, default_flow_style=False))
    else:  # text
        click.echo()
        click.echo(click.style("History Statistics:", fg="cyan", bold=True))
        click.echo()
        click.echo(f"  Total Generations:  {stats['total']}")
        click.echo(f"  Successful:         {click.style(str(stats['successful']), fg='green')}")
        click.echo(f"  Failed:            {click.style(str(stats['failed']), fg='red')}")
        click.echo(f"  Total Duration:    {stats['total_duration_ms']}ms")
        click.echo(f"  Avg Duration:      {stats['avg_duration_ms']}ms")
        click.echo(f"  Series Count:      {stats['series_count']}")
        click.echo()

