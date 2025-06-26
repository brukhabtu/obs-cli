"""Commands for searching notes."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json
from datetime import datetime


@click.group(name="search")
@click.pass_context
def search_group(ctx):
    """Search Obsidian vault."""
    pass


@search_group.command(name="notes")
@click.argument("query")
@click.option("--limit", "-l", type=int, help="Limit number of results")
@click.pass_context
def search_notes(ctx, query, limit):
    """Search notes by path or basename."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        results = client.search_notes(query, limit=limit)
        
        # Format for display
        for note in results:
            # Add modified date
            if 'mtime' in note:
                note['modified'] = datetime.fromtimestamp(note['mtime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            # Format tags
            note['tags_str'] = ', '.join(note.get('tags', []))
        
        output = format_output(
            results,
            format=ctx.obj["format"],
            headers=["Path", "Basename", "Tags", "Modified"],
            keys=["path", "basename", "tags_str", "modified"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@search_group.command(name="orphans")
@click.pass_context
def find_orphans(ctx):
    """Find orphaned notes (no backlinks or outlinks)."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        notes = client.get_notes()
        all_links = client.get_all_links()
        
        orphans = []
        for note in notes:
            note_path = note['path']
            if note_path not in all_links or (not all_links[note_path]['backlinks'] and not all_links[note_path]['outlinks']):
                # Add created date
                if 'ctime' in note:
                    note['created'] = datetime.fromtimestamp(note['ctime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                orphans.append(note)
        
        output = format_output(
            orphans,
            format=ctx.obj["format"],
            headers=["Path", "Basename", "Created"],
            keys=["path", "basename", "created"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@search_group.command(name="untagged")
@click.pass_context
def find_untagged(ctx):
    """Find untagged notes."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        notes = client.get_notes()
        
        untagged = []
        for note in notes:
            if not note.get('tags', []):
                # Add modified date
                if 'mtime' in note:
                    note['modified'] = datetime.fromtimestamp(note['mtime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                untagged.append(note)
        
        output = format_output(
            untagged,
            format=ctx.obj["format"],
            headers=["Path", "Basename", "Modified"],
            keys=["path", "basename", "modified"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)