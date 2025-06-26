"""Commands for working with folders."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json
from datetime import datetime


@click.group(name="folders")
@click.pass_context
def folders_group(ctx):
    """Manage and query folder structure."""
    pass


@folders_group.command(name="list")
@click.option("--sort", "-s", type=click.Choice(["name", "count"]), default="name")
@click.pass_context
def list_folders(ctx, sort):
    """List all folders with note counts."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        folders_dict = client.get_folders()
        
        # Convert to list format
        folders = []
        for folder, count in folders_dict.items():
            display_name = folder if folder != 'root' else '/ (root)'
            folders.append({
                'folder': display_name,
                'path': folder,
                'count': count
            })
        
        # Sort
        if sort == "name":
            folders.sort(key=lambda f: f['folder'])
        else:
            folders.sort(key=lambda f: f['count'], reverse=True)
        
        output = format_output(
            folders,
            format=ctx.obj["format"],
            headers=["Folder", "Notes"],
            keys=["folder", "count"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@folders_group.command(name="notes")
@click.argument("folder")
@click.option("--limit", "-l", type=int, help="Limit number of results")
@click.pass_context
def folder_notes(ctx, folder, limit):
    """List notes in a specific folder."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        # Handle root folder notation
        if folder == '/' or folder == '(root)':
            folder = 'root'
            
        notes = client.get_notes_by_folder(folder)
        
        if not notes:
            console.print(f"No notes found in folder: {folder}")
            return
        
        # Sort by name
        notes.sort(key=lambda n: n.get('basename', ''))
        
        # Apply limit
        if limit:
            notes = notes[:limit]
        
        # Format for display
        for note in notes:
            note['tags_str'] = ', '.join(note.get('tags', []))
            if 'mtime' in note:
                note['modified'] = datetime.fromtimestamp(note['mtime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        output = format_output(
            notes,
            format=ctx.obj["format"],
            headers=["Basename", "Tags", "Modified"],
            keys=["basename", "tags_str", "modified"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@folders_group.command(name="tree")
@click.option("--max-depth", "-d", type=int, help="Maximum depth to display")
@click.pass_context
def folder_tree(ctx, max_depth):
    """Show folder structure as a tree."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        folders_dict = client.get_folders()
        
        # Build tree structure
        tree = {}
        for folder_path in folders_dict.keys():
            if folder_path == 'root':
                continue
                
            parts = folder_path.split('/')
            current = tree
            
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        def print_tree(node, prefix="", path_parts=None, depth=0):
            if path_parts is None:
                path_parts = []
            
            if max_depth and depth >= max_depth:
                return
                
            items = sorted(node.items())
            for i, (name, children) in enumerate(items):
                is_last = i == len(items) - 1
                
                # Build the full path
                current_path_parts = path_parts + [name]
                full_path = '/'.join(current_path_parts)
                    
                count = folders_dict.get(full_path, 0)
                
                connector = "└── " if is_last else "├── "
                console.print(f"{prefix}{connector}{name} ({count} notes)")
                
                extension = "    " if is_last else "│   "
                print_tree(children, prefix + extension, current_path_parts, depth + 1)
        
        console.print("[bold]Folder Structure[/bold]")
        if 'root' in folders_dict:
            console.print(f"/ (root) ({folders_dict['root']} notes)")
            
        print_tree(tree)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)