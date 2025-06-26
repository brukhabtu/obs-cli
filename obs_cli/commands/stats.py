"""Commands for vault statistics."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.utils.console import console
import json
from datetime import datetime, timedelta
from collections import defaultdict


@click.group(name="stats")
@click.pass_context
def stats_group(ctx):
    """View vault statistics."""
    pass


@stats_group.command(name="vault")
@click.pass_context
def vault_stats(ctx):
    """Show overall vault statistics."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        stats = client.get_stats()
        notes = client.get_notes()
        
        # Calculate additional stats
        orphaned_notes = 0
        untagged_notes = 0
        total_size = 0
        
        all_links = client.get_all_links()
        
        for note in notes:
            if not note.get('tags', []):
                untagged_notes += 1
            
            note_path = note['path']
            if note_path not in all_links or (not all_links[note_path]['backlinks'] and not all_links[note_path]['outlinks']):
                orphaned_notes += 1
                
            total_size += note.get('size', 0)
        
        stats['orphanedNotes'] = orphaned_notes
        stats['untaggedNotes'] = untagged_notes
        stats['totalSize'] = total_size
        
        if ctx.obj["format"] == "json":
            console.print(json.dumps(stats, indent=2))
        else:
            console.print("[bold]Vault Statistics[/bold]")
            console.print(f"Total Notes: {stats.get('totalNotes', 0)}")
            console.print(f"Total Tags: {stats.get('totalTags', 0)}")
            console.print(f"Total Links: {stats.get('totalLinks', 0)}")
            console.print(f"Total Size: {total_size:,} bytes")
            console.print(f"Orphaned Notes: {orphaned_notes}")
            console.print(f"Untagged Notes: {untagged_notes}")
            if 'lastUpdatedHuman' in stats:
                console.print(f"Last Updated: {stats['lastUpdatedHuman']}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@stats_group.command(name="daily")
@click.option("--days", "-d", type=int, default=30, help="Number of days to show")
@click.pass_context
def daily_stats(ctx, days):
    """Show daily note creation statistics."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        notes = client.get_notes()
        
        # Calculate daily stats
        daily_counts = defaultdict(int)
        now = datetime.now()
        
        for note in notes:
            if 'ctime' in note:
                created = datetime.fromtimestamp(note['ctime'] / 1000)
                days_ago = (now - created).days
                
                if days_ago < days:
                    date_str = created.strftime('%Y-%m-%d')
                    daily_counts[date_str] += 1
        
        # Create list of daily stats
        daily = []
        for i in range(days):
            date = now - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            daily.append({
                'date': date_str,
                'count': daily_counts.get(date_str, 0)
            })
        
        # Sort by date
        daily.sort(key=lambda x: x['date'], reverse=True)
        
        if ctx.obj["format"] == "json":
            console.print(json.dumps(daily, indent=2))
        else:
            console.print(f"[bold]Daily Statistics (Last {days} days)[/bold]")
            for day_stat in daily:
                if day_stat['count'] > 0:
                    console.print(f"{day_stat['date']}: {day_stat['count']} notes")
                
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)