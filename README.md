# obs-cli

A command-line interface for querying Obsidian vault metadata. Works with the Obsidian Metadata API plugin to provide powerful search and analysis capabilities from the terminal.

## Features

- 📝 **Notes**: List, search, and analyze notes
- 🏷️ **Tags**: View tag usage and statistics  
- 📁 **Folders**: Explore vault structure
- ✅ **Tasks**: Track todos across your vault
- 💻 **Code**: Analyze code blocks by language
- 📊 **Stats**: Comprehensive vault statistics
- 🔍 **Search**: Find orphaned notes, untagged content
- 🔗 **Analysis**: Discover note clusters and relationships

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Obsidian with the Metadata API plugin installed

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/obs-cli.git
cd obs-cli
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Install the Obsidian plugin:
   - Copy the `obsidian-metadata-api` folder to your vault's `.obsidian/plugins/` directory
   - Enable the plugin in Obsidian settings
   - Run "Rebuild Metadata Database" command in Obsidian

## Usage

### Basic Commands

```bash
# List all notes
uv run obs-cli --vault /path/to/vault notes list

# Show vault statistics  
uv run obs-cli --vault /path/to/vault stats vault

# List all tags
uv run obs-cli --vault /path/to/vault tags list

# Search for notes
uv run obs-cli --vault /path/to/vault search notes "project"

# Show folder structure
uv run obs-cli --vault /path/to/vault folders tree
```

### Environment Variable

Set the `OBSIDIAN_VAULT` environment variable to avoid specifying `--vault` each time:

```bash
export OBSIDIAN_VAULT="/path/to/your/vault"
uv run obs-cli notes list
```

### Command Categories

#### Notes Commands
- `notes list` - List all notes with metadata
- `notes recent` - Show recently modified notes
- `notes largest` - Find largest notes

#### Tags Commands  
- `tags list` - List all tags with counts
- `tags notes <tag>` - Find notes with specific tag

#### Search Commands
- `search notes <query>` - Search note titles/paths
- `search orphans` - Find notes without links
- `search untagged` - Find notes without tags

#### Tasks Commands
- `tasks list` - Show all tasks
- `tasks pending` - Show incomplete tasks only
- `tasks by-note` - Group tasks by note

#### Folders Commands
- `folders tree` - Display folder hierarchy
- `folders stats` - Show folder statistics

#### Code Commands
- `code stats` - Language statistics
- `code notes` - Notes containing code
- `code search <language>` - Find specific language blocks

#### Stats Commands
- `stats vault` - Overall vault statistics
- `stats daily` - Daily note creation stats

#### Analyze Commands
- `analyze clusters` - Find linked note groups
- `analyze embeds` - Analyze embedded content
- `analyze graph` - Export graph data

## Mobile Usage (Termux)

The tool works great on Android with Termux:

1. Install Termux from F-Droid
2. Install Python and git: `pkg install python git`
3. Follow installation steps above
4. Point to your Obsidian vault in shared storage

**Note**: On mobile, the Obsidian plugin requires manual database rebuilds. Use the Command Palette in Obsidian to run "Rebuild Metadata Database" after making changes.

## Development

### Project Structure

```
obs-cli/
├── obs_cli/
│   ├── cli.py              # Main CLI entry point
│   ├── database_client.py  # Database reader
│   └── commands/           # Command modules
├── obsidian-metadata-api/  # Obsidian plugin
│   ├── main.ts            # Plugin entry point
│   └── src/
│       ├── database.ts    # Database writer
│       └── settings.ts    # Plugin settings
└── pyproject.toml         # Project configuration
```

### Running Tests

```bash
uv run pytest
```

## Architecture

The system consists of two parts:

1. **Obsidian Plugin**: Monitors vault changes and writes metadata to a JSON database
2. **CLI Tool**: Reads the database and provides query capabilities

This approach works on all platforms including mobile Obsidian where HTTP servers aren't supported.

## License

MIT