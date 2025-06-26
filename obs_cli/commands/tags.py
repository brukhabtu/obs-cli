"""Commands for working with tags."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json


@click.group(name="tags")
@click.pass_context
def tags_group(ctx):
    """Manage and query Obsidian tags."""
    pass


@tags_group.command(name="list")
@click.option("--sort", "-s", type=click.Choice(["name", "count"]), default="count")
@click.option("--limit", "-l", type=int, help="Limit number of results")
@click.pass_context
def list_tags(ctx, sort, limit):
    """List all tags in the vault."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        tags_dict = client.get_tags()
        
        # Convert to list format
        tags = [{"tag": tag, "count": count} for tag, count in tags_dict.items()]
        
        # Sort tags
        if sort == "name":
            tags.sort(key=lambda t: t["tag"])
        else:  # count
            tags.sort(key=lambda t: t["count"], reverse=True)
        
        # Apply limit
        if limit:
            tags = tags[:limit]
        
        output = format_output(
            tags,
            format=ctx.obj["format"],
            headers=["Tag", "Count"],
            keys=["tag", "count"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@tags_group.command(name="notes")
@click.argument("tag")
@click.option("--limit", "-l", type=int, help="Limit number of results")
@click.pass_context
def tag_notes(ctx, tag, limit):
    """List notes with a specific tag."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        notes = client.get_notes_by_tag(tag)
        
        # Apply limit
        if limit:
            notes = notes[:limit]
        
        # Format for display
        from datetime import datetime
        for note in notes:
            if 'mtime' in note:
                note['modified'] = datetime.fromtimestamp(note['mtime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        output = format_output(
            notes,
            format=ctx.obj["format"],
            headers=["Path", "Basename", "Modified"],
            keys=["path", "basename", "modified"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)