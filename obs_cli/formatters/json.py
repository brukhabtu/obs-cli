"""JSON formatter for obs-cli output."""

import json
from typing import List, Dict, Any, Optional
from obs_cli.formatters.base import BaseFormatter


class JSONFormatter(BaseFormatter):
    """Format output as JSON."""
    
    def format(
        self, 
        data: List[Dict[str, Any]], 
        headers: Optional[List[str]] = None,
        keys: Optional[List[str]] = None
    ) -> str:
        """Format data as JSON."""
        # If keys are specified, filter the data
        if keys:
            filtered_data = []
            for item in data:
                filtered_item = {k: item.get(k) for k in keys}
                filtered_data.append(filtered_item)
            data = filtered_data
        
        return json.dumps(data, indent=2, ensure_ascii=False)