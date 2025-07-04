"""Simplified Obsidian CLI focused on Dataview queries."""

import click
import sys
import logging
from pathlib import Path
from obs_cli.core.dataview import DataviewClient
from obs_cli.install import install_plugin
from obs_cli.logging import setup_logging
from obs_cli.cli.formatters import QueryResultFormatter
from rich.console import Console
from obs_cli import __version__

console = Console()
logger = logging.getLogger(__name__)




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
        formatter = QueryResultFormatter(console=console)
        output = formatter.format_dataview_results(results, format, no_color)
        
        # Check if the query failed
        if results.get('status') == 'error':
            if format == "json":
                print(output)
            else:
                console.print(f"[red]{output}[/red]")
            sys.exit(1)
        
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