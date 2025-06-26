"""
Database client for reading Obsidian metadata from JSON database file.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import os


class DatabaseClient:
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
        
        self.db_path = self.vault_path / ".obsidian/plugins/obsidian-metadata-api/metadata.json"
        
    def _read_database(self) -> Dict[str, Any]:
        """Read the database file."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found at {self.db_path}")
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_notes(self) -> List[Dict[str, Any]]:
        """Get all notes."""
        db = self._read_database()
        return list(db.get('notes', {}).values())
    
    def get_note(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a specific note by path."""
        db = self._read_database()
        return db.get('notes', {}).get(path)
    
    def search_notes(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search notes by content in path or basename."""
        db = self._read_database()
        notes = []
        
        query_lower = query.lower()
        for note in db.get('notes', {}).values():
            if (query_lower in note['path'].lower() or 
                query_lower in note['basename'].lower()):
                notes.append(note)
                
        if limit:
            notes = notes[:limit]
            
        return notes
    
    def get_tags(self) -> Dict[str, int]:
        """Get all tags with their counts."""
        db = self._read_database()
        return db.get('tags', {})
    
    def get_notes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get notes that have a specific tag."""
        db = self._read_database()
        notes = []
        
        for note in db.get('notes', {}).values():
            if tag in note.get('tags', []):
                notes.append(note)
                
        return notes
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        db = self._read_database()
        stats = db.get('stats', {})
        
        # Add some computed stats
        if 'lastUpdated' in stats:
            last_updated = datetime.fromisoformat(stats['lastUpdated'].replace('Z', '+00:00'))
            stats['lastUpdatedHuman'] = last_updated.strftime('%Y-%m-%d %H:%M:%S')
            
        return stats
    
    def get_links(self, note_path: str) -> Dict[str, List[str]]:
        """Get links for a specific note."""
        db = self._read_database()
        links = db.get('links', {})
        
        if note_path in links:
            return links[note_path]
        else:
            return {'outlinks': [], 'backlinks': []}
    
    def get_all_links(self) -> Dict[str, Dict[str, List[str]]]:
        """Get all links in the vault."""
        db = self._read_database()
        return db.get('links', {})
    
    def get_tasks(self, completed: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get all tasks, optionally filtered by completion status."""
        db = self._read_database()
        tasks = []
        
        for note_path, note in db.get('notes', {}).items():
            for task in note.get('tasks', []):
                task_info = {
                    'note_path': note_path,
                    'note_basename': note['basename'],
                    'text': task['text'],
                    'completed': task['completed'],
                    'line': task['line']
                }
                
                if completed is None or task['completed'] == completed:
                    tasks.append(task_info)
                    
        return tasks
    
    def get_folders(self) -> Dict[str, int]:
        """Get all folders with their note counts."""
        db = self._read_database()
        return db.get('folders', {})
    
    def get_notes_by_folder(self, folder: str) -> List[Dict[str, Any]]:
        """Get notes in a specific folder."""
        db = self._read_database()
        notes = []
        
        # Handle root folder
        if folder == 'root':
            folder = ''
            
        for note in db.get('notes', {}).values():
            if note.get('folder', '') == folder:
                notes.append(note)
                
        return notes
    
    def get_embeds(self) -> List[Dict[str, Any]]:
        """Get all embeds in the vault."""
        db = self._read_database()
        embeds = []
        
        for note_path, note in db.get('notes', {}).items():
            for embed in note.get('embeds', []):
                embeds.append({
                    'from_note': note_path,
                    'from_basename': note['basename'],
                    'to_note': embed
                })
                
        return embeds
    
    def get_code_blocks(self) -> List[Dict[str, Any]]:
        """Get all code blocks in the vault."""
        db = self._read_database()
        code_blocks = []
        
        for note_path, note in db.get('notes', {}).items():
            for block in note.get('codeBlocks', []):
                code_blocks.append({
                    'note_path': note_path,
                    'note_basename': note['basename'],
                    'language': block['language'],
                    'count': block['count']
                })
                
        return code_blocks
    
    def get_code_stats(self) -> Dict[str, int]:
        """Get code statistics by language."""
        db = self._read_database()
        language_counts = {}
        
        for note in db.get('notes', {}).values():
            for block in note.get('codeBlocks', []):
                language = block['language']
                language_counts[language] = language_counts.get(language, 0) + block['count']
                
        return language_counts