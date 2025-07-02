"""
Simplified database client for reading Obsidian metadata from JSON database file.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time
import hashlib


class DataviewClient:
    """Client for reading Obsidian metadata from JSON database."""
    
    def __init__(self, vault_path: Optional[str] = None):
        """Initialize database client.
        
        Args:
            vault_path: Path to Obsidian vault. If not provided, will try to auto-detect.
        """
        if vault_path:
            self.vault_path = Path(vault_path)
        else:
            # Try to auto-detect vault path
            default_vault = Path.home() / "storage/shared/Obsidian/Claude"
            if default_vault.exists():
                self.vault_path = default_vault
            else:
                raise ValueError("Could not auto-detect vault path. Please provide vault_path.")
        
        self.db_path = self.vault_path / ".obsidian/plugins/obsidian-dataview-bridge/metadata.json"
        
    def _read_database(self) -> Dict[str, Any]:
        """Read the database file."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found at {self.db_path}")
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_database(self, data: Dict[str, Any]) -> None:
        """Write data back to the database file."""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic database statistics."""
        db = self._read_database()
        stats = db.get('stats', {})
        
        # Add some computed stats
        if 'lastUpdated' in stats:
            last_updated = datetime.fromisoformat(stats['lastUpdated'].replace('Z', '+00:00'))
            stats['lastUpdatedHuman'] = last_updated.strftime('%Y-%m-%d %H:%M:%S')
            
        return stats
    
    def execute_dataview_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute a Dataview query and return results.
        
        This method writes the query to a special location in the database
        and waits for the plugin to execute it and write back results.
        
        Args:
            query: The Dataview query to execute
            
        Returns:
            Dictionary with query results or None if Dataview is not available
        """
        db = self._read_database()
        
        # Check if Dataview is available
        if not db.get('dataviewAvailable', False):
            # Try to trigger a check by writing a request
            db['dataviewQueries'] = db.get('dataviewQueries', {})
            db['dataviewQueries']['_check'] = {
                'query': 'CHECK_DATAVIEW',
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            self._write_database(db)
            
            # Wait briefly for plugin to respond
            time.sleep(0.5)
            db = self._read_database()
            
            if not db.get('dataviewAvailable', False):
                return None
        
        # Generate unique query ID for this execution
        query_id = hashlib.sha256(f"{query}_{time.time()}".encode()).hexdigest()[:16]
        
        # Submit query for execution
        if 'dataviewQueries' not in db:
            db['dataviewQueries'] = {}
            
        db['dataviewQueries'][query_id] = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self._write_database(db)
        
        # Wait for plugin to execute query (with timeout)
        max_wait = 5.0  # 5 seconds timeout
        poll_interval = 0.1
        elapsed = 0.0
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            db = self._read_database()
            result = db.get('dataviewQueries', {}).get(query_id)
            
            if result and result.get('status') in ['success', 'error']:
                return result
        
        # Timeout - return pending status
        return {
            'query': query,
            'status': 'timeout',
            'error': 'Query execution timed out',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cached_dataview_results(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached Dataview query results."""
        db = self._read_database()
        queries = db.get('dataviewQueries', {})
        
        # Filter out internal queries
        return {
            query_id: result 
            for query_id, result in queries.items() 
            if not query_id.startswith('_')
        }
    
    def clear_dataview_cache(self) -> int:
        """Clear all cached Dataview queries.
        
        Returns:
            Number of queries cleared
        """
        db = self._read_database()
        
        if 'dataviewQueries' not in db:
            return 0
            
        # Count non-internal queries
        count = len([q for q in db['dataviewQueries'].keys() if not q.startswith('_')])
        
        # Clear all queries except internal ones
        db['dataviewQueries'] = {
            k: v for k, v in db['dataviewQueries'].items() 
            if k.startswith('_')
        }
        
        self._write_database(db)
        return count