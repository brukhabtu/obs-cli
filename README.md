# Obsidian DQuery

Execute Dataview queries on Obsidian vaults from the command line.

## Features

- Execute any Dataview query from the command line
- Support for TABLE, LIST, TASK, and CALENDAR queries
- Multiple output formats: table, JSON, CSV
- Query caching for improved performance
- Works with mobile Obsidian vaults
- Comprehensive Dataview syntax help built-in
- **Vault validation and linting** with configurable rules

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

## Vault Validation & Linting

The CLI includes a powerful validation system that lets you define rules to maintain vault quality and consistency.

### Quick Start

```bash
# Create a validation config file
cat > .obs-validate.toml << 'EOF'
version = "1.0"

[[rules]]
name = "No Empty Files"
severity = "error"
query = "LIST WHERE file.size == 0"
assertion = "len(results) == 0"
message = "Found {count} empty files: {results}"
EOF

# Run validation
obs validate --vault /path/to/vault
```

### Configuration Format

Validation rules are defined in TOML files with the following structure:

```toml
version = "1.0"

[[rules]]
name = "Rule Name"                    # Required: Rule identifier
severity = "error"                    # Required: "error", "warning", or "info"
query = "LIST FROM \"folder\""        # Required: Dataview query
assertion = "len(results) == 0"       # Required: Python assertion
message = "Found {count} files"       # Required: Error message template
description = "Optional description"   # Optional: Human-readable description

# Optional: Variables for template substitution
[rules.variables]
max_size = 50000
required_tag = "#project"
```

### Rule Examples

**Check for missing tags:**
```toml
[[rules]]
name = "Required Project Tags"
severity = "warning"
query = "LIST FROM \"Projects\" WHERE !contains(file.tags, {required_tag})"
assertion = "len(results) == 0"
message = "Project files missing required tag: {results}"
[rules.variables]
required_tag = "#project"
```

**Validate file sizes:**
```toml
[[rules]]
name = "Large Files Check"
severity = "info"
query = "LIST WHERE file.size > {max_size}"
assertion = "len(results) < {max_files}"
message = "Found {count} large files (limit: {max_files})"
[rules.variables]
max_size = 50000
max_files = 5
```

**Check daily note naming:**
```toml
[[rules]]
name = "Daily Notes Format"
severity = "error"
query = "LIST FROM \"Daily\" WHERE !contains(file.name, {date_pattern})"
assertion = "len(results) == 0"
message = "Daily notes not following naming convention: {results}"
[rules.variables]
date_pattern = "2024-"
```

### Configuration Discovery

The system automatically searches for configuration files in this order:
1. Explicit path via `--config` flag
2. Current directory: `.obs-validate.yaml` or `.obs-validate.toml`
3. Vault root directory: `.obs-validate.yaml` or `.obs-validate.toml`

### Validation Commands

```bash
# Run validation with automatic config discovery
obs validate --vault /path/to/vault

# Use explicit config file
obs validate --vault /path/to/vault --config /path/to/config.toml

# Run with debug output
obs validate --vault /path/to/vault --debug --verbose
```

### Assertion Context

Rule assertions have access to these variables:
- `results`: Query result rows
- `count`: Number of results
- `len`, `any`, `all`, `sum`, `min`, `max`: Python built-ins
- `result_count`: Alias for count
- `is_empty`: Boolean indicating empty results
- Custom variables from the `variables` section

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