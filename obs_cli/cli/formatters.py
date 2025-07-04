"""Formatters for query results output."""

import json
import csv
import io
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table


class QueryResultFormatter:
    """Formatter for Dataview query results."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the formatter.
        
        Args:
            console: Rich console instance for table formatting
        """
        self.console = console or Console()
    
    def format_table(self, data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
        """
        Format data as a rich table.
        
        Args:
            data: List of dictionaries containing row data
            headers: Optional list of column headers
            
        Returns:
            Formatted table string
        """
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
        with self.console.capture() as capture:
            self.console.print(table)
        
        return capture.get()
    
    def format_json(self, data: Any) -> str:
        """
        Format data as JSON.
        
        Args:
            data: Data to format as JSON
            
        Returns:
            JSON formatted string
        """
        return json.dumps(data, indent=2, default=str)
    
    def format_csv(self, data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
        """
        Format data as CSV.
        
        Args:
            data: List of dictionaries containing row data
            headers: Optional list of column headers
            
        Returns:
            CSV formatted string
        """
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
    
    def format_dataview_results(self, results: Dict[str, Any], format_type: str, no_color: bool = False) -> str:
        """
        Format Dataview query results based on the specified format type.
        
        Args:
            results: Raw Dataview query results
            format_type: Output format ('table', 'json', 'csv')
            no_color: Whether to disable colored output
            
        Returns:
            Formatted output string
        """
        if results.get('status') != 'success':
            if format_type == "json":
                return self.format_json(results)
            else:
                return f"Query failed: {results.get('error', 'Unknown error')}"
        
        result_data = results.get('result', {})
        query_type = result_data.get('type', 'unknown').upper()
        data = result_data.get('values', [])
        
        if format_type == "json":
            return self.format_json(results)
        
        if not data:
            return "No results found"
        
        if format_type == "csv":
            return self._format_csv_output(results, query_type, data)
        
        # Table format
        return self._format_table_output(results, query_type, data, no_color)
    
    def _format_csv_output(self, results: Dict[str, Any], query_type: str, data: List[Any]) -> str:
        """Format results as CSV based on query type."""
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
            
            return self.format_csv(csv_data, headers=headers)
        else:
            # For LIST and TASK, create simple structure
            csv_data = []
            for item in data:
                if isinstance(item, dict):
                    csv_data.append(item)
                else:
                    csv_data.append({"value": str(item)})
            
            return self.format_csv(csv_data)
    
    def _format_table_output(self, results: Dict[str, Any], query_type: str, data: List[Any], no_color: bool) -> str:
        """Format results as table based on query type."""
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
                
                return self.format_table(table_data, headers=headers)
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
            return self.format_json(data)
        
        return '\n'.join(output_lines)