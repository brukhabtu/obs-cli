"""Tests for TOML configuration validation."""

import pytest
from pathlib import Path
import tempfile
from obs_cli.core.config import ConfigLoader, ValidationError


class TestValidateConfig:
    """Test TOML config validation using match statements."""
    
    def test_valid_config(self):
        """Test validation of a complete valid config."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "Test Rule",
                    "severity": "error",
                    "query": "LIST FROM \"\"",
                    "assertion": "len(results) == 0",
                    "message": "Found {len(results)} files"
                }
            ]
        }
        
        result = ConfigLoader._validate_config(config)
        assert result == config
    
    def test_valid_config_with_optional_fields(self):
        """Test validation with optional description and variables."""
        config = {
            "version": "1.0", 
            "rules": [
                {
                    "name": "Tag Validation",
                    "description": "Validate tag patterns",
                    "severity": "warning",
                    "query": "LIST WHERE contains({tags}, file.tags)",
                    "assertion": "len(results) == 0",
                    "message": "Invalid tags found",
                    "variables": {
                        "tags": ["#daily", "#meeting"]
                    }
                }
            ]
        }
        
        result = ConfigLoader._validate_config(config)
        assert result == config
    
    def test_missing_version(self):
        """Test error when version is missing."""
        config = {
            "rules": []
        }
        
        with pytest.raises(ValidationError, match="Missing required field: 'version'"):
            ConfigLoader._validate_config(config)
    
    def test_invalid_version(self):
        """Test error when version is wrong."""
        config = {
            "version": "2.0",
            "rules": []
        }
        
        with pytest.raises(ValidationError, match="Invalid version: 2.0. Expected '1.0'"):
            ConfigLoader._validate_config(config)
    
    def test_missing_rules(self):
        """Test error when rules are missing."""
        config = {
            "version": "1.0"
        }
        
        with pytest.raises(ValidationError, match="Missing required field: 'rules'"):
            ConfigLoader._validate_config(config)
    
    def test_rules_not_list(self):
        """Test error when rules is not a list."""
        config = {
            "version": "1.0",
            "rules": "not a list"
        }
        
        with pytest.raises(ValidationError, match="'rules' must be a list"):
            ConfigLoader._validate_config(config)
    
    def test_rule_missing_name(self):
        """Test error when rule is missing name."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "severity": "error",
                    "query": "LIST",
                    "assertion": "True",
                    "message": "test"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: Missing required field 'name'"):
            ConfigLoader._validate_config(config)
    
    def test_rule_missing_severity(self):
        """Test error when rule is missing severity."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "Test",
                    "query": "LIST",
                    "assertion": "True", 
                    "message": "test"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: Missing required field 'severity'"):
            ConfigLoader._validate_config(config)
    
    def test_rule_invalid_severity(self):
        """Test error when severity has invalid value."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "Test",
                    "severity": "critical",
                    "query": "LIST",
                    "assertion": "True",
                    "message": "test"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match=r"Rule 0: 'severity' must be one of \['error', 'warning', 'info'\], got 'critical'"):
            ConfigLoader._validate_config(config)
    
    def test_rule_empty_name(self):
        """Test error when name is empty string."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "",
                    "severity": "error",
                    "query": "LIST",
                    "assertion": "True",
                    "message": "test"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: 'name' must be a non-empty string"):
            ConfigLoader._validate_config(config)
    
    def test_rule_empty_query(self):
        """Test error when query is empty."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "Test",
                    "severity": "error",
                    "query": "   ",
                    "assertion": "True",
                    "message": "test"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: 'query' must be a non-empty string"):
            ConfigLoader._validate_config(config)
    
    def test_rule_invalid_description_type(self):
        """Test error when description is not a string."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "Test",
                    "description": 123,
                    "severity": "error",
                    "query": "LIST",
                    "assertion": "True",
                    "message": "test"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: 'description' must be a string"):
            ConfigLoader._validate_config(config)
    
    def test_rule_invalid_variables_type(self):
        """Test error when variables is not a dict."""
        config = {
            "version": "1.0",
            "rules": [
                {
                    "name": "Test",
                    "severity": "error", 
                    "query": "LIST",
                    "assertion": "True",
                    "message": "test",
                    "variables": "not a dict"
                }
            ]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: 'variables' must be a dictionary"):
            ConfigLoader._validate_config(config)
    
    def test_rule_not_dict(self):
        """Test error when rule is not a dictionary."""
        config = {
            "version": "1.0",
            "rules": ["not a dict"]
        }
        
        with pytest.raises(ValidationError, match="Rule 0: Must be a dictionary"):
            ConfigLoader._validate_config(config)


class TestLoadConfig:
    """Test loading and validating TOML files."""
    
    def test_load_valid_toml_file(self):
        """Test loading a valid TOML configuration file."""
        toml_content = '''
version = "1.0"

[[rules]]
name = "Test Rule"
severity = "error"
query = "LIST FROM \\"\\""
assertion = "len(results) == 0"
message = "Test message"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = ConfigLoader.load(f.name)
            
            assert config.version == "1.0"
            assert len(config.rules) == 1
            assert config.rules[0]["name"] == "Test Rule"
        
        # Clean up
        Path(f.name).unlink()
    
    def test_load_nonexistent_file(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            ConfigLoader.load("/nonexistent/path.toml")
    
    def test_load_invalid_toml_syntax(self):
        """Test error when TOML syntax is invalid."""
        invalid_toml = '''
version = "1.0"
[unclosed table
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(invalid_toml)
            f.flush()
            
            with pytest.raises(ValidationError, match="Invalid TOML syntax"):
                ConfigLoader.load(f.name)
        
        # Clean up
        Path(f.name).unlink()


class TestFindConfigFile:
    """Test configuration file discovery."""
    
    def test_explicit_config_path(self):
        """Test using explicit --config path."""
        result = ConfigLoader.find_config_file(config_path="/explicit/path.toml", vault_path=None)
        assert result == Path("/explicit/path.toml")
    
    def test_find_in_current_directory(self):
        """Test finding config in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            config_file = tmpdir_path / ".obs-validate.toml"
            config_file.touch()
            
            # Change to temp directory
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = ConfigLoader.find_config_file(config_path=None, vault_path=None)
                assert result == Path.cwd() / ".obs-validate.toml"
            finally:
                os.chdir(old_cwd)
    
    def test_find_in_vault_root(self):
        """Test finding config in vault root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            config_file = vault_path / ".obs-validate.yaml"
            config_file.touch()
            
            result = ConfigLoader.find_config_file(config_path=None, vault_path=vault_path)
            assert result == config_file
    
    def test_no_config_found(self):
        """Test when no config file is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            result = ConfigLoader.find_config_file(config_path=None, vault_path=vault_path)
            assert result is None
    
    def test_prefer_toml_over_yaml(self):
        """Test that we find files in the right order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            yaml_file = tmpdir_path / ".obs-validate.yaml"
            toml_file = tmpdir_path / ".obs-validate.toml"
            
            # Create YAML first
            yaml_file.touch()
            
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Should find YAML when only YAML exists
                result = ConfigLoader.find_config_file(config_path=None, vault_path=None)
                assert result == Path.cwd() / ".obs-validate.yaml"
                
                # Create TOML
                toml_file.touch()
                
                # Should now find YAML (first in list)
                result = ConfigLoader.find_config_file(config_path=None, vault_path=None)
                assert result == Path.cwd() / ".obs-validate.yaml"
            finally:
                os.chdir(old_cwd)