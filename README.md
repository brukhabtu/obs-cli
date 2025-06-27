# Obsidian DQuery

Execute Dataview queries on Obsidian vaults from the command line.

## Features

- Execute any Dataview query from the command line
- Support for TABLE, LIST, TASK, and CALENDAR queries
- Multiple output formats: table, JSON, CSV
- Query caching for improved performance
- Works with mobile Obsidian vaults
- Comprehensive Dataview syntax help built-in

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/obs-cli.git
cd obs-cli

# Install with uv
uv sync

# Install the Obsidian plugin
cp -r obsidian-metadata-api /path/to/vault/.obsidian/plugins/
```

## Usage

```bash
# Execute a simple query
obs-dquery "TABLE file.name FROM #project"

# Use a different output format
obs-dquery "LIST FROM #todo" --format json

# Execute query from file
obs-dquery --file queries/my-query.dql

# Set default vault path
export OBSIDIAN_VAULT="/path/to/vault"
obs-dquery "TABLE file.mtime WHERE file.mtime >= date(today) - dur(7 days)"

# Show Dataview syntax help
obs-dquery --help-syntax
```

## Query Examples

```sql
-- Find all notes with a specific tag
TABLE file.name, file.mtime FROM #project

-- List recent notes
LIST FROM "" WHERE file.mtime >= date(today) - dur(7 days)

-- Find incomplete tasks
TASK FROM "" WHERE !completed

-- Find notes with specific frontmatter
TABLE file.name, rating FROM "" WHERE rating > 4

-- Complex queries with multiple conditions
TABLE file.name, file.size, file.tags 
FROM "Projects" OR "Archive"
WHERE contains(file.name, "2024") AND file.size > 1000
SORT file.mtime DESC
```

## Output Formats

- **table** (default): Rich formatted table output
- **json**: Structured JSON output for processing
- **csv**: CSV format for spreadsheet import

## Requirements

- Python 3.12+
- Obsidian with the Obsidian Metadata API plugin installed
- The Dataview plugin is recommended for query validation

## Development

```bash
# Run tests
uv run pytest

# Build the Obsidian plugin
cd obsidian-metadata-api
npm install
npm run build
```

## License

MIT