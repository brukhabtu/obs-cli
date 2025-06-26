"""CSV formatter for obs-cli output."""

import csv
import io
from typing import List, Dict, Any, Optional
from obs_cli.formatters.base import BaseFormatter


class CSVFormatter(BaseFormatter):
    """Format output as CSV."""
    
    def format(
        self, 
        data: List[Dict[str, Any]], 
        headers: Optional[List[str]] = None,
        keys: Optional[List[str]] = None
    ) -> str:
        """Format data as CSV."""
        if not data:
            return ""
        
        # Auto-detect keys if not provided
        if not keys:
            keys = list(data[0].keys()) if data else []
        if not headers:
            headers = keys
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(headers)
        
        # Write data
        for item in data:
            row = []
            for key in keys:
                value = item.get(key, "")
                
                # Format special values
                if isinstance(value, list):
                    value = "; ".join(str(v) for v in value)
                elif value is None:
                    value = ""
                
                row.append(str(value))
            
            writer.writerow(row)
        
        return output.getvalue().strip()