"""Commands for working with tasks."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json


@click.group(name="tasks")
@click.pass_context
def tasks_group(ctx):
    """Manage and query tasks in notes."""
    pass


@tasks_group.command(name="list")
@click.option("--status", "-s", type=click.Choice(["all", "incomplete", "complete"]), default="all")
@click.option("--limit", "-l", type=int, help="Limit number of results")
@click.pass_context
def list_tasks(ctx, status, limit):
    """List tasks from all notes."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        if status == "incomplete":
            tasks = client.get_tasks(completed=False)
        elif status == "complete":
            tasks = client.get_tasks(completed=True)
        else:
            tasks = client.get_tasks()
        
        # Apply limit
        if limit:
            tasks = tasks[:limit]
        
        # Format for display
        for task in tasks:
            task['status'] = '✓' if task['completed'] else '☐'
        
        output = format_output(
            tasks,
            format=ctx.obj["format"],
            headers=["Status", "Task", "Note", "Line"],
            keys=["status", "text", "note_basename", "line"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@tasks_group.command(name="stats")
@click.pass_context
def task_stats(ctx):
    """Show task statistics."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        all_tasks = client.get_tasks()
        incomplete = [t for t in all_tasks if not t['completed']]
        complete = [t for t in all_tasks if t['completed']]
        
        stats = {
            'total': len(all_tasks),
            'incomplete': len(incomplete),
            'complete': len(complete),
            'completion_rate': f"{(len(complete) / len(all_tasks) * 100):.1f}%" if all_tasks else "0%"
        }
        
        if ctx.obj["format"] == "json":
            console.print(json.dumps(stats, indent=2))
        else:
            console.print("[bold]Task Statistics[/bold]")
            console.print(f"Total Tasks: {stats['total']}")
            console.print(f"Incomplete: {stats['incomplete']}")
            console.print(f"Complete: {stats['complete']}")
            console.print(f"Completion Rate: {stats['completion_rate']}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@tasks_group.command(name="by-note")
@click.argument("note_path")
@click.pass_context
def tasks_by_note(ctx, note_path):
    """List tasks in a specific note."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        all_tasks = client.get_tasks()
        note_tasks = [t for t in all_tasks if t['note_path'] == note_path]
        
        if not note_tasks:
            console.print(f"No tasks found in {note_path}")
            return
        
        # Format for display
        for task in note_tasks:
            task['status'] = '✓' if task['completed'] else '☐'
        
        output = format_output(
            note_tasks,
            format=ctx.obj["format"],
            headers=["Status", "Task", "Line"],
            keys=["status", "text", "line"]
        )
        
        console.print(output, style="none" if ctx.obj["no_color"] else None)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)