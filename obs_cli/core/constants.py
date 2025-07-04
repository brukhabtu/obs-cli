"""Central constants for the obs-cli project."""

# Dataview query execution
DEFAULT_TIMEOUT_MS = 5000
MAX_QUERY_RETRIES = 3
CACHE_SIZE_LIMIT = 100
DEFAULT_OUTPUT_FORMAT = "table"

# Plugin information
PLUGIN_REPO_URL = "https://github.com/BrukT/obsidian-metadata-api"
DATABASE_FILE_PATH = ".obsidian/plugins/obsidian-metadata-api/metadata.json"

# Validation system
DEFAULT_QUERY_TIMEOUT = 30000  # milliseconds (30 seconds)
MAX_RESULT_DISPLAY_LENGTH = 500  # characters
MAX_ASSERTION_EVAL_TIME = 5000  # milliseconds

# Config file names
CONFIG_FILE_NAMES = [".obs-validate.yaml", ".obs-validate.toml"]

# Severity levels
SEVERITY_LEVELS = ["error", "warning", "info"]

# Output formatting
TABLE_MAX_COLUMN_WIDTH = 50
JSON_INDENT = 2
CSV_DELIMITER = ","