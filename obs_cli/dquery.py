"""Simplified Obsidian CLI focused on Dataview queries."""

import click
import json
import sys
import csv
import io
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from obs_cli.core.dataview import DataviewClient
from obs_cli.install import install_plugin
from obs_cli.logging import setup_logging
from rich.console import Console
from rich.table import Table
from obs_cli import __version__

console = Console()
logger = logging.getLogger(__name__)


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
    
    result_data = results.get('result', {})
    query_type = result_data.get('type', 'unknown').upper()
    data = result_data.get('values', [])
    
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
                # Handle Dataview Link objects
                if 'path' in item:
                    value = item['path']
                else:
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


@click.group()
@click.version_option(version=__version__, prog_name="obs")
@click.option("--debug", is_flag=True, help="Enable debug logging", hidden=True)
@click.pass_context
def cli(ctx, debug):
    """Obsidian CLI for executing Dataview queries and managing plugins.
    
    Examples:
    
        obs query "TABLE file.name FROM #project"
        
        obs query "LIST WHERE contains(tags, 'work')"
        
        obs install-plugin /path/to/vault
    """
    # Set up logging for the entire CLI
    log_level = "DEBUG" if debug else "WARNING"
    setup_logging(level=log_level)
    
    # Store debug flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug


@cli.command()
@click.argument("query", required=False)
@click.option("--vault", "-v", type=click.Path(), envvar="OBSIDIAN_VAULT", 
              help="Path to Obsidian vault")
@click.option("--format", "-f", type=click.Choice(["json", "table", "csv"]), 
              default="table", help="Output format")
@click.option("--file", type=click.Path(exists=True), 
              help="Execute query from file")
@click.option("--help-syntax", is_flag=True, 
              help="Show Dataview syntax help")
@click.option("--no-color", is_flag=True, 
              help="Disable colored output")
def query(query, vault, format, file, help_syntax, no_color):
    """Execute a Dataview query on your Obsidian vault."""
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
        results = client.execute_dataview_query(query)
        
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


@cli.command("install-plugin")
@click.argument("vault", type=click.Path())
def install_plugin_cmd(vault):
    """Install the Obsidian Dataview Bridge plugin to a vault."""
    if install_plugin(vault):
        sys.exit(0)
    else:
        sys.exit(1)


@cli.command()
@click.option("--vault", "-v", type=click.Path(), envvar="OBSIDIAN_VAULT", 
              help="Path to Obsidian vault")
@click.option("--config", "-c", type=click.Path(exists=True), 
              help="Path to validation config file")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def validate(vault, config, debug, verbose):
    """Validate vault content against rules defined in config file.
    
    Looks for .obs-validate.yaml or .obs-validate.toml in vault root by default.
    """
    from obs_cli.cli.lint_command import lint_command
    
    # Use the new lint command implementation
    lint_command(vault=vault, config=config, debug=debug, verbose=verbose)


if __name__ == "__main__":
    cli()