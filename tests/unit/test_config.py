"""Tests for configuration parsing and validation."""

import pytest
from pathlib import Path
import tempfile
import tomllib

from obs_cli.core.config import ConfigLoader, ValidationConfig, ValidationError


class TestConfigLoader:
    """Test configuration loading functionality."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid TOML configuration."""
        config_content = """
version = "1.0"

[[rules]]
name = "No empty notes"
severity = "error"
query = "LIST WHERE file.size = 0"
assertion = "count == 0"
message = "Found {count} empty notes"

[[rules]]
name = "Check for missing tags"
severity = "warning"
query = "LIST WHERE length(file.tags) = 0"
assertion = "count < 10"
message = "Found {count} notes without tags"
description = "Notes should have at least one tag"
"""
        config_file = tmp_path / ".obs-validate.toml"
        config_file.write_text(config_content)
        
        config = ConfigLoader.load(str(config_file))
        
        assert isinstance(config, ValidationConfig)
        assert config.version == "1.0"
        assert len(config.rules) == 2
        assert config.rules[0]["name"] == "No empty notes"
        assert config.rules[0]["severity"] == "error"
        assert config.rules[1]["name"] == "Check for missing tags"
        assert "description" in config.rules[1]

    def test_load_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML format raises error."""
        # TOML parser is more strict than YAML, so we test with invalid TOML
        config_content = """
version = "1.0"
[[rules
name = "Invalid syntax"
"""
        config_file = tmp_path / ".obs-validate.toml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValidationError, match="Invalid TOML syntax"):
            ConfigLoader.load(str(config_file))

    def test_missing_config_file(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load("/nonexistent/config.toml")

    def test_config_schema_validation(self, tmp_path):
        """Test validation of config schema."""
        # Test missing version
        config = """
[[rules]]
name = "Test rule"
severity = "error"
query = "LIST"
assertion = "true"
message = "Test"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="Missing required field: 'version'"):
            ConfigLoader.load(str(config_file))
        
        # Test invalid version
        config = """
version = "2.0"
rules = []
"""
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="Invalid version: 2.0"):
            ConfigLoader.load(str(config_file))
        
        # Test missing rules
        config = """
version = "1.0"
"""
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="Missing required field: 'rules'"):
            ConfigLoader.load(str(config_file))

    def test_rule_validation(self, tmp_path):
        """Test validation of individual rules."""
        # Test missing required fields
        test_cases = [
            (
                """
version = "1.0"
[[rules]]
severity = "error"
query = "LIST"
assertion = "true"
message = "Test"
""",
                "Missing required field 'name'"
            ),
            (
                """
version = "1.0"
[[rules]]
name = "Test"
query = "LIST"
assertion = "true"
message = "Test"
""",
                "Missing required field 'severity'"
            ),
            (
                """
version = "1.0"
[[rules]]
name = "Test"
severity = "error"
assertion = "true"
message = "Test"
""",
                "Missing required field 'query'"
            ),
            (
                """
version = "1.0"
[[rules]]
name = "Test"
severity = "error"
query = "LIST"
message = "Test"
""",
                "Missing required field 'assertion'"
            ),
            (
                """
version = "1.0"
[[rules]]
name = "Test"
severity = "error"
query = "LIST"
assertion = "true"
""",
                "Missing required field 'message'"
            ),
        ]
        
        for config_text, expected_error in test_cases:
            config_file = tmp_path / "config.toml"
            config_file.write_text(config_text)
            
            with pytest.raises(ValidationError, match=expected_error):
                ConfigLoader.load(str(config_file))

    def test_invalid_severity(self, tmp_path):
        """Test that invalid severity values are rejected."""
        config = """
version = "1.0"
[[rules]]
name = "Test"
severity = "critical"  # Invalid severity
query = "LIST"
assertion = "true"
message = "Test"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="'severity' must be one of"):
            ConfigLoader.load(str(config_file))

    def test_empty_string_fields(self, tmp_path):
        """Test that empty string fields are rejected."""
        config = """
version = "1.0"
[[rules]]
name = ""
severity = "error"
query = "LIST"
assertion = "true"
message = "Test"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="'name' must be a non-empty string"):
            ConfigLoader.load(str(config_file))

    def test_variable_substitution(self, tmp_path):
        """Test loading config with variables."""
        config = """
version = "1.0"

[variables]
tag_limit = 5
important_folder = "Projects"

[[rules]]
name = "Check important notes"
severity = "warning"
query = 'LIST FROM "{important_folder}" WHERE length(file.tags) < {tag_limit}'
assertion = "count < 10"
message = "Found {count} notes in {important_folder} with fewer than {tag_limit} tags"
variables = { custom_var = "test" }
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config)
        
        config = ConfigLoader.load(str(config_file))
        
        assert "variables" in config.to_dict()
        assert config.variables["tag_limit"] == 5
        assert config.variables["important_folder"] == "Projects"
        assert config.rules[0]["variables"]["custom_var"] == "test"

    def test_find_config_file(self, tmp_path):
        """Test config file discovery logic."""
        # Test explicit path
        explicit_path = tmp_path / "custom.toml"
        explicit_path.touch()
        
        found = ConfigLoader.find_config_file(str(explicit_path), None)
        assert found == explicit_path
        
        # Test current directory
        cwd_config = Path.cwd() / ".obs-validate.toml"
        cwd_config.touch()
        try:
            found = ConfigLoader.find_config_file(None, None)
            assert found == cwd_config
        finally:
            cwd_config.unlink()
        
        # Test vault root
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        vault_config = vault_path / ".obs-validate.yaml"
        vault_config.touch()
        
        found = ConfigLoader.find_config_file(None, vault_path)
        assert found == vault_config
        
        # Test no config found
        found = ConfigLoader.find_config_file(None, tmp_path / "empty")
        assert found is None

    def test_optional_fields(self, tmp_path):
        """Test that optional fields are properly handled."""
        config = """
version = "1.0"

[[rules]]
name = "Rule with description"
severity = "info"
query = "LIST"
assertion = "true"
message = "Test"
description = "This is a test rule"

[[rules]]
name = "Rule with variables"
severity = "warning"
query = "LIST WHERE file.size > {threshold}"
assertion = "count < {max_count}"
message = "Found {count} files"
variables = { threshold = 1000, max_count = 5 }
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config)
        
        config = ConfigLoader.load(str(config_file))
        
        assert config.rules[0]["description"] == "This is a test rule"
        assert config.rules[1]["variables"]["threshold"] == 1000
        assert config.rules[1]["variables"]["max_count"] == 5

    def test_invalid_optional_fields(self, tmp_path):
        """Test that invalid optional fields are rejected."""
        # Test invalid description type
        config = """
version = "1.0"
[[rules]]
name = "Test"
severity = "error"
query = "LIST"
assertion = "true"
message = "Test"
description = 123  # Should be string
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="'description' must be a string"):
            ConfigLoader.load(str(config_file))
        
        # Test invalid variables type
        config = """
version = "1.0"
[[rules]]
name = "Test"
severity = "error"
query = "LIST"
assertion = "true"
message = "Test"
variables = "not a dict"  # Should be dict
"""
        config_file.write_text(config)
        
        with pytest.raises(ValidationError, match="'variables' must be a dictionary"):
            ConfigLoader.load(str(config_file))


class TestValidationConfig:
    """Test ValidationConfig class."""

    def test_config_initialization(self):
        """Test ValidationConfig initialization."""
        data = {
            "version": "1.0",
            "rules": [{"name": "test"}],
            "variables": {"var": "value"}
        }
        
        config = ValidationConfig(data)
        
        assert config.version == "1.0"
        assert config.rules == [{"name": "test"}]
        assert config.variables == {"var": "value"}
        assert config.to_dict() == data

    def test_config_defaults(self):
        """Test ValidationConfig default values."""
        data = {}
        config = ValidationConfig(data)
        
        assert config.version == "1.0"
        assert config.rules == []
        assert config.variables == {}