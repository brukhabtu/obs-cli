"""Configuration parsing and validation for validation rules."""

import tomllib
from pathlib import Path
from typing import Dict, Any, List, Optional

from obs_cli.core.constants import CONFIG_FILE_NAMES, SEVERITY_LEVELS
from obs_cli.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when validation config is invalid."""
    pass


class ValidationConfig:
    """Container for validation configuration data."""
    
    def __init__(self, data: Dict[str, Any]):
        self.version = data.get("version", "1.0")
        self.rules = data.get("rules", [])
        self.variables = data.get("variables", {})
        self._raw_data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        return self._raw_data


class ConfigLoader:
    """Handles loading and validation of configuration files."""
    
    @staticmethod
    def load(config_path: str) -> ValidationConfig:
        """Load and validate TOML configuration file.
        
        Args:
            config_path: Path to TOML config file
            
        Returns:
            Validated configuration object
            
        Raises:
            ValidationError: If config is invalid
            FileNotFoundError: If config file doesn't exist
        """
        path = Path(config_path)
        logger.info(f"Loading configuration from: {path}")
        
        if not path.exists():
            logger.error(f"Configuration file not found: {path}")
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'rb') as f:
                data = tomllib.load(f)
            logger.debug(f"Successfully parsed TOML from {path}")
        except tomllib.TOMLDecodeError as e:
            logger.error(f"Invalid TOML syntax in {path}: {e}")
            raise ValidationError(f"Invalid TOML syntax: {e}")
        
        # Validate the configuration
        validated_data = ConfigLoader._validate_config(data)
        logger.info(f"Configuration validated successfully. Found {len(validated_data.get('rules', []))} rules.")
        
        return ValidationConfig(validated_data)
    
    @staticmethod
    def find_config_file(config_path: Optional[str], vault_path: Optional[Path]) -> Optional[Path]:
        """Find configuration file using discovery rules.
        
        Args:
            config_path: Explicit config path from --config flag
            vault_path: Vault path for searching vault root
            
        Returns:
            Path to config file if found, None otherwise
        """
        logger.debug(f"Searching for config file. Explicit path: {config_path}, Vault path: {vault_path}")
        
        # 1. Use explicit --config path
        if config_path:
            path = Path(config_path)
            logger.debug(f"Using explicit config path: {path}")
            return path
        
        # 2. Check current directory
        for filename in CONFIG_FILE_NAMES:
            path = Path.cwd() / filename
            logger.debug(f"Checking current directory for {filename}: {path}")
            if path.exists():
                logger.info(f"Found config file in current directory: {path}")
                return path
        
        # 3. Check vault root if available
        if vault_path:
            for filename in CONFIG_FILE_NAMES:
                path = vault_path / filename
                logger.debug(f"Checking vault root for {filename}: {path}")
                if path.exists():
                    logger.info(f"Found config file in vault root: {path}")
                    return path
        
        logger.warning("No configuration file found in any default location")
        return None
    
    @staticmethod
    def _validate_config(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate TOML config using structural pattern matching.
        
        Args:
            data: Parsed TOML data
            
        Returns:
            Validated config data
            
        Raises:
            ValidationError: If config is invalid
        """
        logger.debug("Validating configuration structure")
        
        match data:
            # Basic structure check
            case {
                "version": str() as version,
                "rules": list() as rules
            } if version == "1.0":
                # Validate each rule
                for i, rule in enumerate(rules):
                    ConfigLoader._validate_rule(rule, i)
                logger.debug(f"Validated {len(rules)} rules successfully")
                return data
                
            case {"version": version} if not isinstance(version, str) or version != "1.0":
                raise ValidationError(f"Invalid version: {version}. Expected '1.0'")
                
            case {"rules": rules} if not isinstance(rules, list):
                raise ValidationError("'rules' must be a list")
                
            case data if "version" not in data:
                raise ValidationError("Missing required field: 'version'")
                
            case data if "rules" not in data:
                raise ValidationError("Missing required field: 'rules'")
                
            case _:
                raise ValidationError(f"Invalid configuration structure")
    
    @staticmethod
    def _validate_rule(rule: Any, index: int) -> None:
        """Validate a single rule using pattern matching.
        
        Args:
            rule: Rule data to validate
            index: Rule index for error messages
            
        Raises:
            ValidationError: If rule is invalid
        """
        logger.debug(f"Validating rule {index}")
        
        match rule:
            # Complete rule with all required fields
            case {
                "name": str() as name,
                "severity": ("error" | "warning" | "info") as severity,
                "query": str() as query,
                "assertion": str() as assertion,
                "message": str() as message,
                **optional_fields
            } if name.strip() and query.strip() and assertion.strip() and message.strip():
                logger.debug(f"Rule {index} '{name}' has all required fields")
                
                # Validate optional fields if present
                if "description" in optional_fields and not isinstance(optional_fields["description"], str):
                    raise ValidationError(f"Rule {index}: 'description' must be a string")
                    
                if "variables" in optional_fields and not isinstance(optional_fields["variables"], dict):
                    raise ValidationError(f"Rule {index}: 'variables' must be a dictionary")
                    
            # Missing required fields
            case rule_data if not isinstance(rule_data, dict):
                raise ValidationError(f"Rule {index}: Must be a dictionary")
                
            case rule_data if "name" not in rule_data:
                raise ValidationError(f"Rule {index}: Missing required field 'name'")
                
            case rule_data if "severity" not in rule_data:
                raise ValidationError(f"Rule {index}: Missing required field 'severity'")
                
            case rule_data if "query" not in rule_data:
                raise ValidationError(f"Rule {index}: Missing required field 'query'")
                
            case rule_data if "assertion" not in rule_data:
                raise ValidationError(f"Rule {index}: Missing required field 'assertion'")
                
            case rule_data if "message" not in rule_data:
                raise ValidationError(f"Rule {index}: Missing required field 'message'")
                
            # Invalid field types or values
            case {"name": name} if not isinstance(name, str) or not name.strip():
                raise ValidationError(f"Rule {index}: 'name' must be a non-empty string")
                
            case {"severity": severity} if severity not in SEVERITY_LEVELS:
                raise ValidationError(f"Rule {index}: 'severity' must be one of {SEVERITY_LEVELS}, got '{severity}'")
                
            case {"query": query} if not isinstance(query, str) or not query.strip():
                raise ValidationError(f"Rule {index}: 'query' must be a non-empty string")
                
            case {"assertion": assertion} if not isinstance(assertion, str) or not assertion.strip():
                raise ValidationError(f"Rule {index}: 'assertion' must be a non-empty string")
                
            case {"message": message} if not isinstance(message, str) or not message.strip():
                raise ValidationError(f"Rule {index}: 'message' must be a non-empty string")
                
            case _:
                raise ValidationError(f"Rule {index}: Invalid rule structure")