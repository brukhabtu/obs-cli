"""Output formatters for obs-cli."""

from typing import List, Dict, Any, Optional
from obs_cli.formatters.table import TableFormatter
from obs_cli.formatters.json import JSONFormatter
from obs_cli.formatters.csv import CSVFormatter


def format_output(
    data: List[Dict[str, Any]], 
    format: str = "table",
    headers: Optional[List[str]] = None,
    keys: Optional[List[str]] = None
) -> str:
    """Format output data based on specified format."""
    formatters = {
        "table": TableFormatter(),
        "json": JSONFormatter(),
        "csv": CSVFormatter()
    }
    
    formatter = formatters.get(format, TableFormatter())
    return formatter.format(data, headers=headers, keys=keys)