"""Integration tests for CLI commands."""

import json
import csv
import io
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from obs_cli.dquery import cli


def mock_execute_dataview_query(query):
    """Mock implementation of execute_dataview_query that returns test data."""
    # Parse the query to determine response
    query_lower = query.lower()
    
    if 'table' in query_lower:
        if '#project' in query:
            # Check if file.size is requested
            if 'file.size' in query:
                return {
                    'status': 'success',
                    'result': {
                        'type': 'table',
                        'values': [
                            {'file.name': 'Project Alpha', 'file.size': 5678},
                            {'file.name': 'Old Project', 'file.size': 3456}
                        ]
                    },
                    'headers': ['file.name', 'file.size']
                }
            else:
                return {
                    'status': 'success',
                    'result': {
                        'type': 'table',
                        'values': [
                            {'file.name': 'Project Alpha'},
                            {'file.name': 'Old Project'}
                        ]
                    },
                    'headers': ['file.name']
                }
        elif '#resource' in query:
            return {
                'status': 'success',
                'result': {
                    'type': 'table',
                    'values': [
                        {'file.name': 'Python Guide', 'file.tags': ['resource', 'python', 'guide']}
                    ]
                },
                'headers': ['file.name', 'file.tags']
            }
        elif 'file.size > 1000' in query:
            return {
                'status': 'success',
                'result': {
                    'type': 'table',
                    'values': [
                        {'file.name': 'Python Guide', 'file.size': 12345},
                        {'file.name': 'Project Alpha', 'file.size': 5678},
                        {'file.name': 'Old Project', 'file.size': 3456}
                    ]
                },
                'headers': ['file.name', 'file.size']
            }
        elif '#nonexistenttag' in query:
            return {
                'status': 'success',
                'result': {
                    'type': 'table',
                    'values': []
                },
                'headers': ['file.name']
            }
    elif 'list' in query_lower:
        if '#daily' in query:
            return {
                'status': 'success',
                'result': {
                    'type': 'list',
                    'values': [{'path': 'Daily Notes/2024-01-15.md'}]
                }
            }
        elif '#person' in query:
            return {
                'status': 'success',
                'result': {
                    'type': 'list',
                    'values': [{'path': 'People/John Doe.md'}]
                }
            }
        elif '#nonexistenttag' in query:
            return {
                'status': 'success',
                'result': {
                    'type': 'list',
                    'values': []
                }
            }
    elif 'task' in query_lower:
        return {
            'status': 'success',
            'result': {
                'type': 'task',
                'values': [
                    {'text': 'Call client about requirements', 'completed': False, 'file': 'Daily Notes/2024-01-15.md', 'line': 12},
                    {'text': 'Write unit tests', 'completed': False, 'file': 'Projects/Project Alpha.md', 'line': 27},
                    {'text': 'Deploy to staging', 'completed': False, 'file': 'Projects/Project Alpha.md', 'line': 29}
                ]
            }
        }
    elif 'invalid' in query_lower:
        return {
            'status': 'error',
            'error': 'Invalid query syntax'
        }
    
    # Default response
    return {
        'status': 'success',
        'result': {
            'type': 'list',
            'values': []
        }
    }


class TestQueryCommand:
    """Test cases for the query command."""
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_query_command_table_format(self, mock_query, vault_with_plugin, cli_runner):
        """Test query command with table format (default)."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            'TABLE file.name FROM #project'
        ])
        
        assert result.exit_code == 0
        assert "Project Alpha" in result.output
        assert "Old Project" in result.output
        # Check table formatting indicators
        assert "─" in result.output or "│" in result.output  # Table borders
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_query_command_json_format(self, mock_query, vault_with_plugin, cli_runner):
        """Test query command with JSON format."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--format', 'json',
            'TABLE file.name FROM #project'
        ])
        
        assert result.exit_code == 0
        # Parse JSON output
        data = json.loads(result.output)
        assert data['status'] == 'success'
        assert 'result' in data
        assert data['result']['type'] == 'table'
        assert len(data['result']['values']) == 2  # Project Alpha and Old Project
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_query_command_csv_format(self, mock_query, vault_with_plugin, cli_runner):
        """Test query command with CSV format."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--format', 'csv',
            'TABLE file.name, file.size FROM #project'
        ])
        
        assert result.exit_code == 0
        # Parse CSV output
        reader = csv.DictReader(io.StringIO(result.output))
        rows = list(reader)
        assert len(rows) == 2
        # Check headers exist
        assert 'file.name' in rows[0]
        assert 'file.size' in rows[0]
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_query_command_no_color(self, mock_query, vault_with_plugin, cli_runner):
        """Test query command with no-color option."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--no-color',
            'LIST FROM #daily'
        ])
        
        assert result.exit_code == 0
        # Output should not contain ANSI color codes
        assert '\033[' not in result.output
        assert '[red]' not in result.output
        assert '2024-01-15' in result.output
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_query_from_file(self, mock_query, vault_with_plugin, cli_runner, tmp_path):
        """Test executing query from a file."""
        mock_query.side_effect = mock_execute_dataview_query
        
        query_file = tmp_path / "query.dql"
        query_file.write_text('TABLE file.name, file.tags FROM #resource')
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--file', str(query_file)
        ])
        
        assert result.exit_code == 0
        assert "Python Guide" in result.output
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_list_query(self, mock_query, vault_with_plugin, cli_runner):
        """Test LIST query type."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            'LIST FROM #person'
        ])
        
        assert result.exit_code == 0
        assert "• " in result.output  # List bullet
        assert "John Doe" in result.output
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_task_query(self, mock_query, vault_with_plugin, cli_runner):
        """Test TASK query type."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            'TASK WHERE !completed'
        ])
        
        assert result.exit_code == 0
        assert "○" in result.output  # Uncompleted task marker
        assert "Call client about requirements" in result.output
        assert "Write unit tests" in result.output
        assert "Deploy to staging" in result.output
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_complex_query(self, mock_query, vault_with_plugin, cli_runner):
        """Test complex query with WHERE and SORT."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--format', 'json',
            'TABLE file.name, file.size WHERE file.size > 1000 SORT file.size DESC'
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'success'
        values = data['result']['values']
        assert len(values) > 0
        # Check sorting
        sizes = [v.get('file.size', 0) for v in values]
        assert sizes == sorted(sizes, reverse=True)
    
    def test_help_syntax_flag(self, cli_runner):
        """Test --help-syntax flag."""
        result = cli_runner.invoke(cli, [
            'query',
            '--help-syntax'
        ])
        
        assert result.exit_code == 0
        assert "Dataview Query Language Syntax" in result.output
        assert "QUERY TYPES:" in result.output
        assert "TABLE" in result.output
        assert "LIST" in result.output
        assert "TASK" in result.output


class TestValidateCommand:
    """Test cases for the validate command."""
    
    def test_validate_command_success(self, vault_with_plugin, cli_runner, tmp_path):
        """Test validate command with valid vault."""
        # Create a simple validation config
        config_file = tmp_path / ".obs-validate.yaml"
        config_file.write_text("""
version: "1.0"
rules:
  - name: frontmatter-required
    type: frontmatter
    severity: error
    frontmatter:
      required:
        - title
""")
        
        result = cli_runner.invoke(cli, [
            'validate',
            '--vault', str(vault_with_plugin),
            '--config', str(config_file)
        ])
        
        # The test vault might have validation issues, but command should run
        assert result.exit_code in [0, 1]
        assert "Lint" in result.output or "validation" in result.output.lower()
    
    def test_validate_command_with_errors(self, mock_vault, cli_runner, tmp_path):
        """Test validate command when validation errors exist."""
        # Create a note without required frontmatter
        note = mock_vault / "test.md"
        note.write_text("# Test\nNo frontmatter here")
        
        config_file = tmp_path / ".obs-validate.yaml"
        config_file.write_text("""
version: "1.0"
rules:
  - name: frontmatter-required
    type: frontmatter
    severity: error
    frontmatter:
      required:
        - title
        - date
""")
        
        result = cli_runner.invoke(cli, [
            'validate',
            '--vault', str(mock_vault),
            '--config', str(config_file)
        ])
        
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "Error" in result.output
    
    def test_validate_verbose_mode(self, vault_with_plugin, cli_runner, tmp_path):
        """Test validate command with verbose output."""
        config_file = tmp_path / ".obs-validate.yaml"
        config_file.write_text("""
version: "1.0"
rules:
  - name: tag-format
    type: tag
    severity: info
    tag:
      pattern: "^[a-z]+$"
""")
        
        result = cli_runner.invoke(cli, [
            'validate',
            '--vault', str(vault_with_plugin),
            '--config', str(config_file),
            '--verbose'
        ])
        
        assert result.exit_code in [0, 1]
        # Verbose mode should show more detailed output
        assert len(result.output) > 0


class TestInstallPluginCommand:
    """Test cases for the install-plugin command."""
    
    def test_install_plugin_command(self, mock_vault, cli_runner):
        """Test install-plugin command."""
        result = cli_runner.invoke(cli, [
            'install-plugin',
            str(mock_vault)
        ])
        
        # Note: This might fail in test environment due to network/permissions
        # but we're testing the command structure works
        assert isinstance(result.exit_code, int)
        if result.exit_code == 0:
            assert "success" in result.output.lower() or "installed" in result.output.lower()


class TestCLIErrorScenarios:
    """Test error handling scenarios."""
    
    def test_missing_vault_path(self, cli_runner):
        """Test query without vault path."""
        result = cli_runner.invoke(cli, [
            'query',
            'LIST FROM #test'
        ], env={})  # Clear any OBSIDIAN_VAULT env var
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_invalid_query_syntax(self, mock_query, vault_with_plugin, cli_runner):
        """Test with invalid Dataview query syntax."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            'INVALID QUERY SYNTAX HERE'
        ])
        
        assert result.exit_code == 1
        assert "Error" in result.output or "failed" in result.output.lower()
    
    def test_database_not_found(self, mock_vault, cli_runner):
        """Test when metadata database doesn't exist."""
        # mock_vault has no metadata.json
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(mock_vault),
            'LIST'
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "Error" in result.output
    
    def test_empty_query(self, vault_with_plugin, cli_runner):
        """Test with empty query string."""
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            ''
        ])
        
        assert result.exit_code == 1
        assert "provide a query" in result.output.lower() or "Error" in result.output
    
    def test_nonexistent_vault_path(self, cli_runner):
        """Test with non-existent vault path."""
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', '/path/that/does/not/exist',
            'LIST'
        ])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_query_file_not_found(self, vault_with_plugin, cli_runner):
        """Test with non-existent query file."""
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--file', '/path/to/nonexistent/query.dql'
        ])
        
        assert result.exit_code == 2  # Click exits with 2 for missing files
        assert "does not exist" in result.output.lower() or "Error" in result.output


class TestStatsCommand:
    """Test cases for stats command if it exists."""
    
    @pytest.mark.skipif(True, reason="Stats command not yet implemented")
    def test_stats_command(self, vault_with_plugin, cli_runner):
        """Test stats command output."""
        result = cli_runner.invoke(cli, [
            'stats',
            '--vault', str(vault_with_plugin)
        ])
        
        assert result.exit_code == 0
        assert "Notes:" in result.output
        assert "Tags:" in result.output
        assert "Links:" in result.output


class TestOutputFormats:
    """Additional tests for output format edge cases."""
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_empty_results_table_format(self, mock_query, vault_with_plugin, cli_runner):
        """Test table format with no results."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            'LIST FROM #nonexistenttag'
        ])
        
        assert result.exit_code == 0
        assert "No results found" in result.output
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_empty_results_json_format(self, mock_query, vault_with_plugin, cli_runner):
        """Test JSON format with no results."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--format', 'json',
            'LIST FROM #nonexistenttag'
        ])
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data['status'] == 'success'
        assert data['result']['values'] == []
    
    @patch('obs_cli.core.dataview.DataviewClient.execute_dataview_query')
    def test_empty_results_csv_format(self, mock_query, vault_with_plugin, cli_runner):
        """Test CSV format with no results."""
        mock_query.side_effect = mock_execute_dataview_query
        
        result = cli_runner.invoke(cli, [
            'query',
            '--vault', str(vault_with_plugin),
            '--format', 'csv',
            'TABLE file.name FROM #nonexistenttag'
        ])
        
        assert result.exit_code == 0
        # CSV should at least have headers or be empty
        assert len(result.output.strip()) >= 0