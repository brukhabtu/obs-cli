# Obsidian Dataview Bridge Plugin

This plugin acts as a bridge between the Dataview plugin and external tools, allowing you to execute Dataview queries through a JSON interface.

## Purpose

The Dataview Bridge plugin provides a simple way for external tools to execute Dataview queries in your Obsidian vault without needing direct access to the Obsidian API. It monitors a JSON file for query requests and writes the results back to the same file.

## Requirements

- Obsidian v0.15.0 or higher
- Dataview plugin must be installed and enabled

## Features

- Execute any Dataview query (TABLE, LIST, TASK)
- Query results are cached and stored in JSON format
- Automatic cleanup of old query results (24 hours)
- Works on all platforms including mobile
- Lightweight polling mechanism

## Installation

1. Copy this folder to your vault's `.obsidian/plugins/` directory
2. Reload Obsidian
3. Enable "Obsidian Dataview Bridge" in Settings → Community plugins
4. Make sure the Dataview plugin is also installed and enabled

## Usage

### JSON Interface

The bridge monitors the following file for query requests:
```
.obsidian/plugins/obsidian-metadata-api/metadata.json
```

### Query Format

To submit a query, add an entry to the `dataviewQueries` object:

```json
{
  "dataviewQueries": {
    "query-id-123": {
      "query": "TABLE file.name, file.size FROM \"\"",
      "status": "pending"
    }
  }
}
```

### Query Results

The plugin will execute the query and update the entry with results:

```json
{
  "dataviewQueries": {
    "query-id-123": {
      "query": "TABLE file.name, file.size FROM \"\"",
      "status": "success",
      "result": {
        "type": "table",
        "headers": ["File", "file.name", "file.size"],
        "values": [
          ["[[Note 1]]", "Note 1", 1234],
          ["[[Note 2]]", "Note 2", 5678]
        ]
      },
      "timestamp": "2024-01-20T10:30:00Z"
    }
  }
}
```

### Error Handling

If a query fails, the status will be "error" with an error message:

```json
{
  "dataviewQueries": {
    "query-id-123": {
      "query": "INVALID QUERY",
      "status": "error",
      "error": "Query execution failed",
      "timestamp": "2024-01-20T10:30:00Z"
    }
  }
}
```

### Checking Dataview Availability

To check if Dataview is available, create a special query:

```json
{
  "dataviewQueries": {
    "_check": {
      "status": "pending"
    }
  }
}
```

The plugin will update the `dataviewAvailable` field in the root of the JSON file.

## Commands

- **Check Dataview Status**: Manually check if Dataview is available
- **Show Bridge Database Path**: Display the path to the bridge JSON file

## Development

### Building from Source

```bash
npm install
npm run build
```

### Project Structure

```
src/
├── database.ts    # Dataview query bridge logic
├── settings.ts    # Plugin settings
main.ts           # Plugin entry point
manifest.json     # Plugin manifest
```

## Integration

This plugin is designed to work with external tools that need to execute Dataview queries, such as:
- Command-line tools
- Mobile apps
- Automation scripts

## License

MIT