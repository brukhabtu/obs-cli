"""Commands for analyzing vault structure."""

import click
from obs_cli.database_client import DatabaseClient
from obs_cli.formatters import format_output
from obs_cli.utils.console import console
import json
from collections import defaultdict, deque


@click.group(name="analyze")
@click.pass_context
def analyze_group(ctx):
    """Analyze vault structure and relationships."""
    pass


@analyze_group.command(name="clusters")
@click.option("--min-size", "-m", type=int, default=3, help="Minimum cluster size")
@click.pass_context
def find_clusters(ctx, min_size):
    """Find note clusters by link relationships."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        all_links = client.get_all_links()
        
        # Build adjacency list
        graph = defaultdict(set)
        for note_path, links in all_links.items():
            for outlink in links.get('outlinks', []):
                graph[note_path].add(outlink)
                graph[outlink].add(note_path)  # Make undirected
        
        # Find connected components using BFS
        visited = set()
        clusters = []
        
        for node in graph:
            if node not in visited:
                # BFS to find all connected nodes
                component = []
                queue = deque([node])
                visited.add(node)
                
                while queue:
                    current = queue.popleft()
                    component.append(current)
                    
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                if len(component) >= min_size:
                    clusters.append({
                        'notes': component,
                        'size': len(component)
                    })
        
        # Sort clusters by size
        clusters.sort(key=lambda c: c['size'], reverse=True)
        
        if ctx.obj["format"] == "json":
            console.print(json.dumps(clusters, indent=2))
        else:
            console.print(f"[bold]Note Clusters (min size: {min_size})[/bold]")
            for i, cluster in enumerate(clusters, 1):
                console.print(f"\n[bold]Cluster {i}:[/bold] ({cluster['size']} notes)")
                for note in cluster['notes'][:5]:  # Show first 5
                    console.print(f"  - {note}")
                if len(cluster['notes']) > 5:
                    console.print(f"  ... and {len(cluster['notes']) - 5} more")
                    
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@analyze_group.command(name="embeds")
@click.pass_context
def analyze_embeds(ctx):
    """Analyze embedded content in the vault."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        embeds = client.get_embeds()
        
        if not embeds:
            console.print("No embeds found in vault")
            return
        
        # Count embeds by target
        embed_counts = defaultdict(int)
        for embed in embeds:
            embed_counts[embed['to_note']] += 1
        
        # Sort by most embedded
        most_embedded = sorted(embed_counts.items(), key=lambda x: x[1], reverse=True)
        
        if ctx.obj["format"] == "json":
            result = {
                'total_embeds': len(embeds),
                'unique_embedded_files': len(embed_counts),
                'most_embedded': [
                    {'file': file, 'count': count} 
                    for file, count in most_embedded[:10]
                ],
                'all_embeds': embeds
            }
            console.print(json.dumps(result, indent=2))
        else:
            console.print("[bold]Embed Analysis[/bold]")
            console.print(f"Total Embeds: {len(embeds)}")
            console.print(f"Unique Embedded Files: {len(embed_counts)}")
            
            if most_embedded:
                console.print("\n[bold]Most Embedded Files:[/bold]")
                for file, count in most_embedded[:10]:
                    console.print(f"  {file}: {count} times")
                
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)


@analyze_group.command(name="graph")
@click.option("--output", "-o", type=click.Path(), help="Output file for graph data")
@click.pass_context
def export_graph(ctx, output):
    """Export vault graph structure."""
    try:
        client = DatabaseClient(vault_path=ctx.obj["vault"])
        
        notes = client.get_notes()
        all_links = client.get_all_links()
        
        # Build graph data
        nodes = []
        edges = []
        
        for note in notes:
            nodes.append({
                'id': note['path'],
                'label': note['basename'],
                'tags': note.get('tags', [])
            })
        
        # Create edges from links
        edge_id = 0
        for note_path, links in all_links.items():
            for outlink in links.get('outlinks', []):
                edges.append({
                    'id': edge_id,
                    'source': note_path,
                    'target': outlink
                })
                edge_id += 1
        
        graph = {
            'nodes': nodes,
            'edges': edges
        }
        
        if output:
            with open(output, 'w') as f:
                json.dump(graph, f, indent=2)
            console.print(f"Graph exported to {output}")
        else:
            if ctx.obj["format"] == "json":
                console.print(json.dumps(graph, indent=2))
            else:
                console.print(f"[bold]Vault Graph[/bold]")
                console.print(f"Nodes: {len(nodes)}")
                console.print(f"Edges: {len(edges)}")
                
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        ctx.exit(1)