# Obsidian Metadata API Plugin

This plugin exports your Obsidian vault metadata to a JSON database that can be queried by external tools like `obs-cli`.

## Features

- Monitors all vault changes in real-time
- Exports comprehensive metadata including:
  - Note properties (path, size, dates)
  - Tags and frontmatter
  - Links and backlinks
  - Headings structure
  - Tasks with completion status
  - Code blocks with language detection
  - Folder hierarchy
  - Embedded content
- Works on all platforms including mobile
- Lightweight JSON database format

## Installation

1. Copy this folder to your vault's `.obsidian/plugins/` directory
2. Reload Obsidian
3. Enable "Metadata API" in Settings → Community plugins
4. The plugin will automatically build the initial database

## Usage

### Automatic Updates

The plugin automatically updates the metadata database when:
- Notes are created, modified, or deleted
- Tags are added or removed
- Links are created or broken
- Tasks are checked/unchecked

### Manual Rebuild

To manually rebuild the entire database:
1. Open Command Palette (Ctrl/Cmd + P)
2. Search for "Rebuild Metadata Database"
3. Press Enter

### Database Location

The metadata is stored at:
```
.obsidian/plugins/obsidian-metadata-api/metadata.json
```

## Mobile Considerations

On mobile devices, the plugin may not update in the background. You may need to:
- Keep Obsidian in the foreground for real-time updates
- Manually rebuild the database after making changes
- Reopen Obsidian if updates seem stuck

## Development

### Building from Source

```bash
npm install
npm run build
```

### Project Structure

```
src/
├── database.ts    # Database operations
├── settings.ts    # Plugin settings
main.ts           # Plugin entry point
manifest.json     # Plugin manifest
```

## Integration

This plugin is designed to work with [obs-cli](https://github.com/yourusername/obs-cli), a command-line tool for querying Obsidian metadata.

## License

MIT