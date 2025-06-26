"""Commands for working with notes."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json


@click.group(name="notes")
@click.pass_context
def notes_group(ctx):
    """Manage and query Obsidian notes."""
    pass


@notes_group.command(name="list")
@click.option("--limit", "-l", type=int, help="Limit number of results")
@click.option("--sort", "-s", type=click.Choice(["name", "modified", "created"]), default="name")
@click.pass_context
def list_notes(ctx, limit, sort):
    """List all notes in the vault."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        notes = client.get_notes()
        
        # Sort notes
        if sort == "name":
            notes.sort(key=lambda n: n.get('basename', ''))
        elif sort == "modified":
            notes.sort(key=lambda n: n.get('mtime', 0), reverse=True)
        elif sort == "created":
            notes.sort(key=lambda n: n.get('ctime', 0), reverse=True)
        
        # Apply limit
        if limit:
            notes = notes[:limit]
        
        # Format tags for display
        for note in notes:
            note['tags_str'] = ', '.join(note.get('tags', []))
            # Convert mtime to readable format
            from datetime import datetime
            if 'mtime' in note:
                note['modified'] = datetime.fromtimestamp(note['mtime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        output = format_output(
            notes,
            format=ctx.obj["format"],
            headers=["Path", "Basename", "Tags", "Modified"],
            keys=["path", "basename", "tags_str", "modified"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@notes_group.command(name="info")
@click.argument("path")
@click.pass_context
def note_info(ctx, path):
    """Show detailed metadata for a specific note."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        metadata = client.get_note(path)
        if not metadata:
            console.print(f"[red]Error:[/red] Note not found: {path}")
            ctx.exit(1)
        
        # Get links info
        links = client.get_links(path)
        
        if ctx.obj["format"] == "json":
            metadata['backlinks'] = links.get('backlinks', [])
            metadata['outlinks'] = links.get('outlinks', [])
            console.print(json.dumps(metadata, indent=2))
        else:
            from datetime import datetime
            console.print(f"[bold]Note:[/bold] {metadata.get('path', 'Unknown')}")
            console.print(f"[bold]Basename:[/bold] {metadata.get('basename', 'Untitled')}")
            console.print(f"[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}")
            if 'ctime' in metadata:
                created = datetime.fromtimestamp(metadata['ctime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                console.print(f"[bold]Created:[/bold] {created}")
            if 'mtime' in metadata:
                modified = datetime.fromtimestamp(metadata['mtime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                console.print(f"[bold]Modified:[/bold] {modified}")
            console.print(f"[bold]Size:[/bold] {metadata.get('size', 0)} bytes")
            console.print(f"[bold]Backlinks:[/bold] {len(links.get('backlinks', []))}")
            console.print(f"[bold]Outlinks:[/bold] {len(links.get('outlinks', []))}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@notes_group.command(name="links")
@click.argument("path")
@click.option("--direction", "-d", type=click.Choice(["in", "out", "both"]), default="both")
@click.pass_context
def note_links(ctx, path, direction):
    """Show links for a specific note."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        links = client.get_links(path)
        
        if ctx.obj["format"] == "json":
            if direction == "in":
                console.print(json.dumps({"backlinks": links.get("backlinks", [])}, indent=2))
            elif direction == "out":
                console.print(json.dumps({"outlinks": links.get("outlinks", [])}, indent=2))
            else:
                console.print(json.dumps(links, indent=2))
        else:
            if direction in ["in", "both"] and links.get("backlinks"):
                console.print("[bold]Backlinks:[/bold]")
                for link in links["backlinks"]:
                    console.print(f"  ← {link}")
                    
            if direction in ["out", "both"] and links.get("outlinks"):
                console.print("[bold]Outlinks:[/bold]")
                for link in links["outlinks"]:
                    console.print(f"  → {link}")
                    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)