"""Commands for working with code blocks."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json


@click.group(name="code")
@click.pass_context
def code_group(ctx):
    """Analyze code blocks in notes."""
    pass


@code_group.command(name="stats")
@click.pass_context
def code_stats(ctx):
    """Show code block statistics by language."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        language_stats = client.get_code_stats()
        
        if not language_stats:
            console.print("No code blocks found in vault")
            return
        
        # Convert to list format
        stats = [{'language': lang, 'count': count} 
                 for lang, count in language_stats.items()]
        
        # Sort by count
        stats.sort(key=lambda s: s['count'], reverse=True)
        
        if ctx.obj["format"] == "json":
            console.print(json.dumps(stats, indent=2))
        else:
            console.print("[bold]Code Block Statistics[/bold]")
            
            output = format_output(
                stats,
                format="table",
                headers=["Language", "Blocks"],
                keys=["language", "count"]
            )
            
            console.print(output)
            
            total = sum(s['count'] for s in stats)
            console.print(f"\n[bold]Total:[/bold] {total} code blocks")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@code_group.command(name="notes")
@click.option("--language", "-l", help="Filter by language")
@click.pass_context
def code_notes(ctx, language):
    """List notes containing code blocks."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        code_blocks = client.get_code_blocks()
        
        # Filter by language if specified
        if language:
            code_blocks = [cb for cb in code_blocks if cb['language'] == language]
        
        if not code_blocks:
            msg = f"No code blocks found"
            if language:
                msg += f" for language: {language}"
            console.print(msg)
            return
        
        # Group by note
        notes_dict = {}
        for block in code_blocks:
            path = block['note_path']
            if path not in notes_dict:
                notes_dict[path] = {
                    'note_path': path,
                    'note_basename': block['note_basename'],
                    'languages': [],
                    'total_blocks': 0
                }
            
            # Add language if not already present
            lang_entry = f"{block['language']} ({block['count']})"
            if lang_entry not in notes_dict[path]['languages']:
                notes_dict[path]['languages'].append(lang_entry)
            notes_dict[path]['total_blocks'] += block['count']
        
        # Convert to list
        notes = list(notes_dict.values())
        
        # Format languages for display
        for note in notes:
            note['languages_str'] = ', '.join(note['languages'])
        
        # Sort by total blocks
        notes.sort(key=lambda n: n['total_blocks'], reverse=True)
        
        output = format_output(
            notes,
            format=ctx.obj["format"],
            headers=["Note", "Languages", "Total Blocks"],
            keys=["note_basename", "languages_str", "total_blocks"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@code_group.command(name="search")
@click.argument("language")
@click.pass_context
def search_by_language(ctx, language):
    """Find all notes with code blocks of a specific language."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        code_blocks = client.get_code_blocks()
        
        # Filter by language
        matching = [cb for cb in code_blocks if cb['language'].lower() == language.lower()]
        
        if not matching:
            console.print(f"No {language} code blocks found")
            return
        
        # Format for display
        for block in matching:
            block['blocks'] = f"{block['count']} block{'s' if block['count'] > 1 else ''}"
        
        output = format_output(
            matching,
            format=ctx.obj["format"],
            headers=["Note Path", "Note", "Blocks"],
            keys=["note_path", "note_basename", "blocks"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
        total = sum(b['count'] for b in matching)
        if ctx.obj["format"] != "json":
            console.print(f"\n[bold]Total:[/bold] {total} {language} code blocks in {len(matching)} notes")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)