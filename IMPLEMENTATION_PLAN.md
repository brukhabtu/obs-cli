# Obsidian CLI Tool Implementation Plan

## Overview
Create a CLI tool that interacts with Obsidian metadata through a custom plugin that exposes an HTTP API.

## Architecture

### 1. Obsidian Plugin (Server)
**Purpose**: Expose Obsidian's internal metadata via HTTP API

**Key Components**:
- HTTP server running on localhost (port 27123)
- API key authentication for security
- RESTful endpoints for metadata access
- WebSocket support for real-time updates (optional)

**Technology Stack**:
- TypeScript
- Express.js for HTTP server
- Rollup for bundling
- Obsidian API for vault access

### 2. CLI Tool (Client)
**Purpose**: Command-line interface for querying Obsidian metadata

**Key Components**:
- HTTP client for API communication
- Command parser (using Commander.js or similar)
- Output formatters (JSON, table, graph)
- Configuration management

**Technology Stack**:
- Python with UV package manager
- Click for CLI framework
- httpx for HTTP requests
- Rich for terminal output

## API Design

### Core Endpoints

#### Metadata Endpoints
- `GET /api/vault/info` - Vault statistics and configuration
- `GET /api/notes` - List all notes with basic metadata
- `GET /api/notes/{path}/metadata` - Get full metadata for a note
- `GET /api/tags` - List all tags with usage counts
- `GET /api/tags/{tag}/notes` - Get notes with specific tag
- `GET /api/links/{path}` - Get backlinks and outlinks for a note
- `GET /api/graph` - Get full vault graph structure

#### Search Endpoints
- `POST /api/search/notes` - Search notes by content/title
- `POST /api/search/tags` - Search by tag combinations
- `GET /api/search/orphans` - Find orphaned notes
- `GET /api/search/untagged` - Find untagged notes

#### Analysis Endpoints
- `GET /api/stats/daily` - Daily note creation statistics
- `GET /api/stats/tags/timeline` - Tag usage over time
- `GET /api/analyze/clusters` - Find note clusters by links

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. **Plugin Setup**
   - Create basic Obsidian plugin structure
   - Implement HTTP server with health check endpoint
   - Add API key authentication
   - Setup build pipeline

2. **CLI Setup**
   - Create Python project with UV
   - Implement basic CLI structure with Click
   - Add configuration management
   - Create HTTP client wrapper

### Phase 2: Core Features (Week 2)
1. **Metadata Access**
   - Implement notes listing endpoint
   - Add tag extraction and listing
   - Create link relationship endpoints
   - Add metadata caching for performance

2. **CLI Commands**
   - `obs-cli notes list` - List all notes
   - `obs-cli tags list` - List all tags
   - `obs-cli note info <path>` - Show note metadata
   - `obs-cli links <path>` - Show note connections

### Phase 3: Search & Query (Week 3)
1. **Search Implementation**
   - Full-text search endpoint
   - Tag-based filtering
   - Complex query support (AND/OR/NOT)
   - Regular expression support

2. **CLI Search Commands**
   - `obs-cli search <query>` - Search notes
   - `obs-cli find --tag <tag>` - Find by tags
   - `obs-cli find --orphaned` - Find orphaned notes
   - `obs-cli find --unlinked` - Find unlinked notes

### Phase 4: Analysis & Visualization (Week 4)
1. **Analysis Features**
   - Graph traversal algorithms
   - Clustering detection
   - Statistics calculation
   - Timeline generation

2. **CLI Analysis Commands**
   - `obs-cli stats` - Show vault statistics
   - `obs-cli graph export` - Export graph data
   - `obs-cli analyze clusters` - Find note clusters
   - `obs-cli timeline --tag <tag>` - Tag usage timeline

## Security Considerations
- API key stored in Obsidian plugin settings
- CLI reads API key from config file or environment
- Server only accepts connections from localhost
- Rate limiting to prevent abuse
- Input validation on all endpoints

## Configuration

### Plugin Configuration
```json
{
  "port": 27123,
  "apiKey": "generated-on-first-run",
  "enableCORS": false,
  "maxRequestsPerMinute": 100
}
```

### CLI Configuration (~/.config/obs-cli/config.yaml)
```yaml
obsidian:
  host: localhost
  port: 27123
  api_key: !env OBS_CLI_API_KEY
  
output:
  format: table  # json, table, csv
  color: true
  
cache:
  enabled: true
  ttl: 300  # seconds
```

## Testing Strategy
1. Unit tests for API endpoints
2. Integration tests for CLI commands
3. Performance tests for large vaults
4. Security tests for authentication

## Documentation Plan
1. Plugin README with installation instructions
2. CLI help text and man page
3. API documentation (OpenAPI spec)
4. Example scripts and use cases

## Future Enhancements
- WebSocket support for real-time updates
- Bulk operations (update multiple notes)
- Export to various formats (GraphML, Gephi)
- Plugin system for custom analyzers
- Web UI dashboard (optional)