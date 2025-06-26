"""Configuration settings for obs-cli."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for obs-cli."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".config" / "obs-cli" / "config.yaml"
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._load_env()
        self._load_config()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        load_dotenv()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                content = f.read()
                # Replace !env tags with environment variables
                self._config = self._process_env_tags(yaml.safe_load(content))
    
    def _process_env_tags(self, data: Any) -> Any:
        """Process !env tags in configuration."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("!env "):
                    env_var = value[5:].strip()
                    result[key] = os.getenv(env_var, "")
                else:
                    result[key] = self._process_env_tags(value)
            return result
        elif isinstance(data, list):
            return [self._process_env_tags(item) for item in data]
        return data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def get_obsidian_config(self) -> Dict[str, Any]:
        """Get Obsidian connection configuration."""
        return {
            "host": self.get("obsidian.host", "localhost"),
            "port": self.get("obsidian.port", 27123),
            "api_key": self.get("obsidian.api_key", os.getenv("OBS_CLI_API_KEY", ""))
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output formatting configuration."""
        return {
            "format": self.get("output.format", "table"),
            "color": self.get("output.color", True)
        }
    
    def save_default_config(self):
        """Save default configuration file."""
        default_config = {
            "obsidian": {
                "host": "localhost",
                "port": 27123,
                "api_key": "!env OBS_CLI_API_KEY"
            },
            "output": {
                "format": "table",
                "color": True
            },
            "cache": {
                "enabled": True,
                "ttl": 300
            }
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)


# Global config instance
config = Config()