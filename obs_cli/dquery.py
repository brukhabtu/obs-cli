"""Simplified Obsidian CLI focused on Dataview queries."""

import click
import json
import sys
import csv
import io
from pathlib import Path
from typing import Optional, List, Dict, Any
from obs_cli.dataview_client import DataviewClient
from rich.console import Console
from rich.table import Table
from obs_cli import __version__

console = Console()


def format_csv(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
    """Format data as CSV."""
    if not data:
        return ""
    
    output = io.StringIO()
    
    # Get headers from first row if not provided
    if headers is None:
        headers = list(data[0].keys()) if data else []
    
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def format_table(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
    """Format data as a rich table."""
    if not data:
        return "No results found"
    
    # Get headers from first row if not provided
    if headers is None:
        headers = list(data[0].keys()) if data else []
    
    table = Table()
    
    # Add columns
    for header in headers:
        table.add_column(header.title())
    
    # Add rows
    for row in data:
        table.add_row(*[str(row.get(h, '')) for h in headers])
    
    # Convert table to string
    with console.capture() as capture:
        console.print(table)
    
    return capture.get()


DATAVIEW_SYNTAX_HELP = """
Dataview Query Language Syntax:

QUERY TYPES:
  TABLE [col1, col2, ...] FROM <source> WHERE <conditions> SORT <field> [ASC/DESC]
  LIST FROM <source> WHERE <conditions> SORT <field> [ASC/DESC]
  TASK FROM <source> WHERE <conditions>
  CALENDAR date FROM <source>

SOURCES:
  #tag              - All pages with this tag
  "folder"          - All pages in this folder
  [[page]]          - Specific page
  outgoing([[page]]) - Pages linked from page
  incoming([[page]]) - Pages linking to page

FIELDS:
  file.name        - Note name
  file.folder      - Folder path
  file.path        - Full path
  file.link        - Link to the file
  file.size        - File size
  file.ctime       - Creation time
  file.mtime       - Modified time
  file.tags        - List of tags
  file.etags       - List of tags with subtags
  file.inlinks     - Incoming links
  file.outlinks    - Outgoing links
  file.aliases     - File aliases
  file.tasks       - Tasks in the file

OPERATORS:
  =, !=, >, >=, <, <=   - Comparison
  contains()            - Check if field contains value
  !contains()           - Check if field doesn't contain value
  AND, OR               - Logical operators
  length()              - Length of list/string
  date()                - Parse date
  dur()                 - Parse duration

EXAMPLES:
  TABLE file.name, file.size FROM #project
  LIST FROM "folder" WHERE file.size > 1000
  TASK WHERE !completed AND contains(tags, "#urgent")
  TABLE file.mtime as "Modified" WHERE file.mtime >= date(today) - dur(7 days)
  LIST FROM #book OR #article SORT file.name ASC

For more information, see: https://blacksmithgu.github.io/obsidian-dataview/
"""


def format_dataview_results(results, format_type, no_color):
    """Format Dataview results for output."""
    if results.get('status') != 'success':
        if format_type == "json":
            return json.dumps(results, indent=2, default=str)
        else:
            return f"Query failed: {results.get('error', 'Unknown error')}"
    
    query_type = results.get('type', 'unknown').upper()
    data = results.get('data', [])
    
    if format_type == "json":
        return json.dumps(results, indent=2, default=str)
    
    if not data:
        return "No results found"
    
    if format_type == "csv":
        # For CSV, we need to determine headers
        if query_type == 'TABLE':
            headers = results.get('headers', [])
            if not headers and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
            
            # Convert to list format for CSV
            csv_data = []
            for row in data:
                if isinstance(row, dict):
                    csv_data.append(row)
                elif isinstance(row, list):
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header] = row[i] if i < len(row) else ''
                    csv_data.append(row_dict)
            
            return format_csv(csv_data, headers=headers)
        else:
            # For LIST and TASK, create simple structure
            csv_data = []
            for item in data:
                if isinstance(item, dict):
                    csv_data.append(item)
                else:
                    csv_data.append({"value": str(item)})
            
            return format_csv(csv_data)
    
    # Table format
    output_lines = []
    
    if query_type == 'TABLE':
        headers = results.get('headers', [])
        if not headers and data:
            headers = list(data[0].keys()) if isinstance(data[0], dict) else []
        
        if headers:
            table_data = []
            for row in data:
                if isinstance(row, dict):
                    table_data.append(row)
                elif isinstance(row, list):
                    row_dict = {}
                    for i, header in enumerate(headers):
                        row_dict[header] = row[i] if i < len(row) else ''
                    table_data.append(row_dict)
            
            return format_table(table_data, headers=headers)
        else:
            # Fall back to simple list
            for item in data:
                output_lines.append(f"• {item}")
    
    elif query_type == 'LIST':
        for item in data:
            if isinstance(item, dict):
                value = item.get('file', item.get('page', str(item)))
                output_lines.append(f"• {value}")
            else:
                output_lines.append(f"• {item}")
    
    elif query_type == 'TASK':
        for task in data:
            if isinstance(task, dict):
                status = "✓" if task.get('completed', False) else "○"
                text = task.get('text', '')
                file = task.get('file', '')
                line = task.get('line', '')
                
                output_lines.append(f"{status} {text}")
                if file and not no_color:
                    output_lines.append(f"  ({file}:{line})")
            else:
                output_lines.append(f"○ {task}")
    
    else:
        # Unknown type, format as JSON
        return json.dumps(data, indent=2, default=str)
    
    return '\n'.join(output_lines)


@click.command()
@click.version_option(version=__version__, prog_name="obs-dquery")
@click.argument("query", required=False)
@click.option("--vault", "-v", type=click.Path(), envvar="OBSIDIAN_VAULT", 
              help="Path to Obsidian vault")
@click.option("--format", "-f", type=click.Choice(["json", "table", "csv"]), 
              default="table", help="Output format")
@click.option("--file", type=click.Path(exists=True), 
              help="Execute query from file")
@click.option("--help-syntax", is_flag=True, 
              help="Show Dataview syntax help")
@click.option("--no-cache", is_flag=True, 
              help="Don't use cached results")
@click.option("--no-color", is_flag=True, 
              help="Disable colored output")
def dquery(query, vault, format, file, help_syntax, no_cache, no_color):
    """Execute Dataview queries on your Obsidian vault.
    
    Examples:
    
        obs-dquery "TABLE file.name FROM #project"
        
        obs-dquery "LIST WHERE contains(tags, 'work')"
        
        obs-dquery --file queries/my-query.dql
        
        obs-dquery --help-syntax
    """
    # Show syntax help if requested
    if help_syntax:
        console.print(DATAVIEW_SYNTAX_HELP)
        return
    
    # Get query from file or argument
    if file:
        with open(file, 'r', encoding='utf-8') as f:
            query = f.read().strip()
    elif not query:
        console.print("[red]Error:[/red] Please provide a query or use --file option")
        console.print("\nUse --help-syntax to see Dataview query syntax")
        sys.exit(1)
    
    try:
        # Initialize dataview client
        client = DataviewClient(vault_path=vault)
        
        # Execute the query
        results = client.execute_dataview_query(query, use_cache=not no_cache)
        
        if results is None:
            console.print("[yellow]Warning:[/yellow] Dataview plugin not installed or query execution failed")
            console.print("Please ensure the Dataview plugin is installed in your vault.")
            sys.exit(1)
        
        # Format and output results
        output = format_dataview_results(results, format, no_color)
        
        if no_color or format in ["json", "csv"]:
            # For JSON/CSV or no-color mode, use plain print
            print(output)
        else:
            # For table format with color, use console
            console.print(output)
            
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] Database file not found. Please ensure the Obsidian Metadata API plugin is installed.")
        console.print(f"Expected location: {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    dquery()