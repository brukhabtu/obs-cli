"""Main CLI interface for obs-cli."""

import click
from obs_cli import __version__
from obs_cli.commands import notes, tags, search, stats, analyze, tasks, folders, code


@click.group()
@click.version_option(version=__version__, prog_name="obs-cli")
@click.option("--vault", "-v", type=click.Path(), envvar="OBSIDIAN_VAULT", help="Path to Obsidian vault")
@click.option("--format", "-f", type=click.Choice(["json", "table", "csv"]), default="table", help="Output format")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx, vault, format, no_color):
    """Obsidian CLI - Command-line interface for Obsidian metadata."""
    ctx.ensure_object(dict)
    ctx.obj["vault"] = vault
    ctx.obj["format"] = format
    ctx.obj["no_color"] = no_color


cli.add_command(notes.notes_group)
cli.add_command(tags.tags_group)
cli.add_command(search.search_group)
cli.add_command(stats.stats_group)
cli.add_command(analyze.analyze_group)
cli.add_command(tasks.tasks_group)
cli.add_command(folders.folders_group)
cli.add_command(code.code_group)