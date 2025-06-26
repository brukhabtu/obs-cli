"""Table formatter for obs-cli output."""

from typing import List, Dict, Any, Optional
from rich.table import Table
from rich.console import Console
from obs_cli.formatters.base import BaseFormatter


class TableFormatter(BaseFormatter):
    """Format output as a rich table."""
    
    def format(
        self, 
        data: List[Dict[str, Any]], 
        headers: Optional[List[str]] = None,
        keys: Optional[List[str]] = None
    ) -> str:
        """Format data as a table."""
        if not data:
            return "No data to display"
        
        # Auto-detect headers and keys if not provided
        if not keys:
            keys = list(data[0].keys()) if data else []
        if not headers:
            headers = [k.replace('_', ' ').title() for k in keys]
        
        table = Table(show_header=True, header_style="bold magenta")
        
        # Add columns
        for header in headers:
            table.add_column(header)
        
        # Add rows
        for item in data:
            row = []
            for key in keys:
                value = item.get(key, "")
                
                # Format special values
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                elif isinstance(value, bool):
                    value = "✓" if value else "✗"
                elif value is None:
                    value = "-"
                
                row.append(str(value))
            
            table.add_row(*row)
        
        # Render table to string
        console = Console()
        with console.capture() as capture:
            console.print(table)
        
        return capture.get().strip()