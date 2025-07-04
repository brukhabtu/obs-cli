"""
Test fixtures for obs-cli.
"""
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pytest


@pytest.fixture
def mock_vault(tmp_path):
    """Creates a temporary vault structure for testing."""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()
    
    # Create .obsidian directory structure
    obsidian_path = vault_path / ".obsidian"
    obsidian_path.mkdir()
    
    plugins_path = obsidian_path / "plugins"
    plugins_path.mkdir()
    
    metadata_plugin_path = plugins_path / "obsidian-dataview-bridge"
    metadata_plugin_path.mkdir()
    
    return vault_path


@pytest.fixture
def mock_database() -> Dict[str, Any]:
    """Returns a mock metadata database with sample data."""
    now = datetime.now().isoformat()
    
    return {
        "version": "1.0.0",
        "lastUpdated": now,
        "dataviewAvailable": True,
        "settings": {
            "enableAutoUpdate": True,
            "updateInterval": 5000
        },
        "notes": {
            "Daily Notes/2024-01-15.md": {
                "path": "Daily Notes/2024-01-15.md",
                "basename": "2024-01-15",
                "extension": "md",
                "created": "2024-01-15T09:00:00.000Z",
                "modified": "2024-01-15T17:30:00.000Z",
                "size": 1234,
                "tags": ["daily", "work", "meeting"],
                "frontmatter": {
                    "date": "2024-01-15",
                    "type": "daily-note",
                    "mood": "productive"
                },
                "links": ["Projects/Project Alpha.md", "People/John Doe.md"],
                "backlinks": ["Weekly Review 2024-W03.md"],
                "embeds": ["attachments/meeting-notes.png"],
                "tasks": [
                    {
                        "text": "Review PR #123",
                        "completed": True,
                        "line": 10
                    },
                    {
                        "text": "Call client about requirements",
                        "completed": False,
                        "line": 12
                    }
                ]
            },
            "Projects/Project Alpha.md": {
                "path": "Projects/Project Alpha.md",
                "basename": "Project Alpha",
                "extension": "md",
                "created": "2024-01-01T10:00:00.000Z",
                "modified": "2024-01-20T14:15:00.000Z",
                "size": 5678,
                "tags": ["project", "active", "python"],
                "frontmatter": {
                    "status": "in-progress",
                    "priority": "high",
                    "due": "2024-02-15",
                    "team": ["John Doe", "Jane Smith"]
                },
                "links": ["Resources/Python Guide.md", "People/John Doe.md", "People/Jane Smith.md"],
                "backlinks": ["Daily Notes/2024-01-15.md", "Projects/Project Overview.md"],
                "embeds": [],
                "tasks": [
                    {
                        "text": "Complete API design",
                        "completed": True,
                        "line": 25
                    },
                    {
                        "text": "Write unit tests",
                        "completed": False,
                        "line": 27
                    },
                    {
                        "text": "Deploy to staging",
                        "completed": False,
                        "line": 29
                    }
                ]
            },
            "People/John Doe.md": {
                "path": "People/John Doe.md",
                "basename": "John Doe",
                "extension": "md",
                "created": "2023-12-01T11:00:00.000Z",
                "modified": "2024-01-10T16:20:00.000Z",
                "size": 890,
                "tags": ["person", "team", "developer"],
                "frontmatter": {
                    "role": "Senior Developer",
                    "email": "john.doe@example.com",
                    "skills": ["Python", "TypeScript", "Docker"]
                },
                "links": ["Projects/Project Alpha.md", "Projects/Project Beta.md"],
                "backlinks": ["Daily Notes/2024-01-15.md", "Projects/Project Alpha.md"],
                "embeds": ["attachments/profile-pic.jpg"],
                "tasks": []
            },
            "Resources/Python Guide.md": {
                "path": "Resources/Python Guide.md",
                "basename": "Python Guide",
                "extension": "md",
                "created": "2023-11-15T09:30:00.000Z",
                "modified": "2024-01-05T11:45:00.000Z",
                "size": 12345,
                "tags": ["resource", "python", "guide", "reference"],
                "frontmatter": {
                    "type": "guide",
                    "language": "python",
                    "version": "3.11",
                    "topics": ["async", "testing", "packaging"]
                },
                "links": ["Resources/Testing Best Practices.md", "Resources/Async Programming.md"],
                "backlinks": ["Projects/Project Alpha.md", "Learning/Python Notes.md"],
                "embeds": [],
                "codeBlocks": [
                    {
                        "language": "python",
                        "line": 45,
                        "content": "def example():\\n    return 'Hello, World!'"
                    },
                    {
                        "language": "python",
                        "line": 120,
                        "content": "async def fetch_data():\\n    async with aiohttp.ClientSession() as session:\\n        return await session.get(url)"
                    }
                ]
            },
            "Archive/Old Project.md": {
                "path": "Archive/Old Project.md",
                "basename": "Old Project",
                "extension": "md",
                "created": "2023-06-01T10:00:00.000Z",
                "modified": "2023-10-15T15:30:00.000Z",
                "size": 3456,
                "tags": ["project", "archived", "completed"],
                "frontmatter": {
                    "status": "completed",
                    "completed_date": "2023-10-15",
                    "outcome": "successful"
                },
                "links": ["Archive/Lessons Learned.md"],
                "backlinks": ["Year Review 2023.md"],
                "embeds": [],
                "tasks": []
            }
        },
        "tags": {
            "daily": 1,
            "work": 1,
            "meeting": 1,
            "project": 2,
            "active": 1,
            "python": 2,
            "person": 1,
            "team": 1,
            "developer": 1,
            "resource": 1,
            "guide": 1,
            "reference": 1,
            "archived": 1,
            "completed": 1
        },
        "links": {
            "Daily Notes/2024-01-15.md": ["Projects/Project Alpha.md", "People/John Doe.md"],
            "Projects/Project Alpha.md": ["Resources/Python Guide.md", "People/John Doe.md", "People/Jane Smith.md"],
            "People/John Doe.md": ["Projects/Project Alpha.md", "Projects/Project Beta.md"],
            "Resources/Python Guide.md": ["Resources/Testing Best Practices.md", "Resources/Async Programming.md"],
            "Archive/Old Project.md": ["Archive/Lessons Learned.md"]
        },
        "tasks": [
            {
                "path": "Daily Notes/2024-01-15.md",
                "text": "Review PR #123",
                "completed": True,
                "line": 10
            },
            {
                "path": "Daily Notes/2024-01-15.md",
                "text": "Call client about requirements",
                "completed": False,
                "line": 12
            },
            {
                "path": "Projects/Project Alpha.md",
                "text": "Complete API design",
                "completed": True,
                "line": 25
            },
            {
                "path": "Projects/Project Alpha.md",
                "text": "Write unit tests",
                "completed": False,
                "line": 27
            },
            {
                "path": "Projects/Project Alpha.md",
                "text": "Deploy to staging",
                "completed": False,
                "line": 29
            }
        ],
        "codeBlocks": {
            "python": 2,
            "javascript": 0,
            "typescript": 0,
            "bash": 0
        }
    }


@pytest.fixture
def sample_metadata_file(mock_vault, mock_database):
    """Creates a sample metadata.json file in the vault."""
    metadata_path = mock_vault / ".obsidian" / "plugins" / "obsidian-dataview-bridge" / "metadata.json"
    
    with open(metadata_path, 'w') as f:
        json.dump(mock_database, f, indent=2)
    
    return metadata_path


@pytest.fixture
def vault_with_plugin(mock_vault, sample_metadata_file):
    """Sets up a vault with the metadata plugin installed and sample data."""
    # Create some actual note files to match the database
    notes = [
        ("Daily Notes/2024-01-15.md", """---
date: 2024-01-15
type: daily-note
mood: productive
---

# Daily Note - 2024-01-15

#daily #work #meeting

## Tasks
- [x] Review PR #123
- [ ] Call client about requirements

## Notes
Met with [[John Doe]] about [[Project Alpha]].

![[attachments/meeting-notes.png]]
"""),
        ("Projects/Project Alpha.md", """---
status: in-progress
priority: high
due: 2024-02-15
team: ["John Doe", "Jane Smith"]
---

# Project Alpha

#project #active #python

## Overview
This project uses [[Python Guide]] as reference.

## Team
- [[John Doe]]
- [[Jane Smith]]

## Tasks
- [x] Complete API design
- [ ] Write unit tests
- [ ] Deploy to staging
"""),
        ("People/John Doe.md", """---
role: Senior Developer
email: john.doe@example.com
skills: ["Python", "TypeScript", "Docker"]
---

# John Doe

#person #team #developer

![[attachments/profile-pic.jpg]]

## Projects
- [[Project Alpha]]
- [[Project Beta]]
"""),
        ("Resources/Python Guide.md", """---
type: guide
language: python
version: "3.11"
topics: ["async", "testing", "packaging"]
---

# Python Guide

#resource #python #guide #reference

## Introduction
See also [[Testing Best Practices]] and [[Async Programming]].

## Example Code

```python
def example():
    return 'Hello, World!'
```

## Async Example

```python
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        return await session.get(url)
```
"""),
        ("Archive/Old Project.md", """---
status: completed
completed_date: 2023-10-15
outcome: successful
---

# Old Project

#project #archived #completed

See [[Lessons Learned]] for retrospective.
""")
    ]
    
    for path, content in notes:
        note_path = mock_vault / path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content)
    
    return mock_vault


# Fixture factories

@pytest.fixture
def vault_with_notes():
    """Factory fixture to create a vault with a specified number of notes."""
    def _vault_with_notes(tmp_path, num_notes: int = 5):
        vault_path = tmp_path / "test_vault_factory"
        vault_path.mkdir()
        
        # Create .obsidian structure
        plugin_path = vault_path / ".obsidian" / "plugins" / "obsidian-dataview-bridge"
        plugin_path.mkdir(parents=True)
        
        # Create notes
        database = {
            "version": "1.0.0",
            "lastUpdated": datetime.now().isoformat(),
            "settings": {},
            "notes": {},
            "tags": {},
            "links": {},
            "tasks": [],
            "codeBlocks": {}
        }
        
        for i in range(num_notes):
            note_path = f"Note{i}.md"
            full_path = vault_path / note_path
            
            content = f"""---
title: Note {i}
created: 2024-01-{i+1:02d}
tags: ["test", "note{i}"]
---

# Note {i}

This is test note number {i}.

#test #note{i}

- [ ] Task for note {i}
"""
            full_path.write_text(content)
            
            # Add to database
            database["notes"][note_path] = {
                "path": note_path,
                "basename": f"Note{i}",
                "extension": "md",
                "created": f"2024-01-{i+1:02d}T10:00:00.000Z",
                "modified": f"2024-01-{i+1:02d}T15:00:00.000Z",
                "size": len(content),
                "tags": ["test", f"note{i}"],
                "frontmatter": {
                    "title": f"Note {i}",
                    "created": f"2024-01-{i+1:02d}",
                    "tags": ["test", f"note{i}"]
                },
                "links": [],
                "backlinks": [],
                "embeds": [],
                "tasks": [{
                    "text": f"Task for note {i}",
                    "completed": False,
                    "line": 11
                }]
            }
            
            # Update tag counts
            database["tags"]["test"] = database["tags"].get("test", 0) + 1
            database["tags"][f"note{i}"] = 1
        
        # Write database
        metadata_path = plugin_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(database, f, indent=2)
        
        return vault_path
    
    return _vault_with_notes


@pytest.fixture
def database_with_query_results():
    """Factory fixture to create a database with specific query results."""
    def _database_with_query_results(results: List[Dict[str, Any]]):
        database = {
            "version": "1.0.0",
            "lastUpdated": datetime.now().isoformat(),
            "settings": {},
            "notes": {},
            "tags": {},
            "links": {},
            "tasks": [],
            "codeBlocks": {}
        }
        
        for i, result in enumerate(results):
            note_path = result.get("path", f"test{i}.md")
            database["notes"][note_path] = {
                "path": note_path,
                "basename": Path(note_path).stem,
                "extension": "md",
                "created": result.get("created", datetime.now().isoformat()),
                "modified": result.get("modified", datetime.now().isoformat()),
                "size": result.get("size", 1000),
                "tags": result.get("tags", []),
                "frontmatter": result.get("frontmatter", {}),
                "links": result.get("links", []),
                "backlinks": result.get("backlinks", []),
                "embeds": result.get("embeds", []),
                "tasks": result.get("tasks", [])
            }
        
        return database
    
    return _database_with_query_results


@pytest.fixture
def error_database():
    """Factory fixture to create databases with various error conditions."""
    def _error_database(error_type: str = "invalid_json"):
        if error_type == "invalid_json":
            return '{"invalid": json content'
        elif error_type == "missing_version":
            return {
                "lastUpdated": datetime.now().isoformat(),
                "notes": {}
            }
        elif error_type == "wrong_version":
            return {
                "version": "2.0.0",  # Unsupported version
                "lastUpdated": datetime.now().isoformat(),
                "notes": {}
            }
        elif error_type == "corrupted_notes":
            return {
                "version": "1.0.0",
                "lastUpdated": datetime.now().isoformat(),
                "notes": {
                    "bad_note.md": {
                        "path": "bad_note.md"
                        # Missing required fields
                    }
                }
            }
        elif error_type == "empty":
            return {}
        else:
            raise ValueError(f"Unknown error type: {error_type}")
    
    return _error_database


@pytest.fixture
def cli_runner():
    """Provides a CLI runner for testing commands."""
    from click.testing import CliRunner
    return CliRunner()