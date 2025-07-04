"""Tests for the vault linting functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import time

from obs_cli.core.linter import VaultLinter, RuleRunner
from obs_cli.core.models import (
    LintRule, LintResult, LintReport, Severity, 
    QueryResult, QueryData
)
from obs_cli.core.dataview import DataviewClient
from obs_cli.core.config import ValidationError


class TestRuleRunner:
    """Test RuleRunner class functionality."""

    def test_rule_execution_success(self):
        """Test successful rule execution."""
        # Mock dataview client
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {
                'values': [
                    {'path': 'note1.md', 'size': 100},
                    {'path': 'note2.md', 'size': 200}
                ]
            }
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Check file sizes",
            query="LIST WHERE file.size > 50",
            assertion="count == 2",
            message="Expected 2 files, found {count}",
            severity=Severity.WARNING
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is True
        assert result.rule_name == "Check file sizes"
        assert result.severity == Severity.WARNING
        assert result.message == ""  # No message when passed
        assert result.details is None  # No details when passed

    def test_rule_execution_failure(self):
        """Test rule execution with assertion failure."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {
                'values': [
                    {'path': 'note1.md'},
                    {'path': 'note2.md'},
                    {'path': 'note3.md'}
                ]
            }
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="No more than 2 notes",
            query="LIST",
            assertion="count <= 2",
            message="Found {count} notes, expected at most 2",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert result.rule_name == "No more than 2 notes"
        assert result.severity == Severity.ERROR
        assert result.message == "Found 3 notes, expected at most 2"
        assert result.details is not None
        assert result.details['row_count'] == 3

    def test_query_execution_error(self):
        """Test handling of query execution errors."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'error',
            'error': 'Invalid query syntax'
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Bad query",
            query="INVALID SYNTAX",
            assertion="true",
            message="Should not reach here",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Query failed: Invalid query syntax" in result.message
        assert result.details['error'] == 'Invalid query syntax'

    def test_assertion_evaluation_equals(self):
        """Test assertion evaluation with equals operator."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {'values': [1, 2, 3, 4, 5]}
        }
        
        runner = RuleRunner(mock_client)
        
        # Test exact count
        rule = LintRule(
            name="Exactly 5 items",
            query="LIST",
            assertion="count == 5",
            message="Wrong count",
            severity=Severity.INFO
        )
        
        result = runner.run_rule(rule)
        assert result.passed is True
        
        # Test not equals
        rule.assertion = "count != 10"
        result = runner.run_rule(rule)
        assert result.passed is True

    def test_assertion_evaluation_contains(self):
        """Test assertion evaluation with contains logic."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {
                'values': [
                    {'path': 'projects/todo.md'},
                    {'path': 'daily/2024-01-01.md'},
                    {'path': 'projects/ideas.md'}
                ]
            }
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Check projects folder",
            query="LIST",
            assertion="any('projects' in r.get('value', {}).get('path', '') for r in results)",
            message="No files in projects folder",
            severity=Severity.WARNING
        )
        
        result = runner.run_rule(rule)
        assert result.passed is True

    def test_assertion_evaluation_greater_than(self):
        """Test assertion evaluation with comparison operators."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {
                'values': [
                    {'size': 1000},
                    {'size': 2000},
                    {'size': 500}
                ]
            }
        }
        
        runner = RuleRunner(mock_client)
        
        # Test with max function
        rule = LintRule(
            name="Check max size",
            query="LIST",
            assertion="max(r.get('value', {}).get('size', 0) for r in results) > 1500",
            message="No large files found",
            severity=Severity.INFO
        )
        
        result = runner.run_rule(rule)
        assert result.passed is True
        
        # Test with sum
        rule.assertion = "sum(r.get('value', {}).get('size', 0) for r in results) >= 3500"
        result = runner.run_rule(rule)
        assert result.passed is True

    def test_complex_rule_with_variables(self):
        """Test rule execution with variable substitution."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {
                'values': [
                    {'path': 'Projects/app.md', 'tags': ['important', 'dev']},
                    {'path': 'Projects/design.md', 'tags': ['important']}
                ]
            }
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Check important project files",
            query='LIST FROM "{folder}" WHERE contains(file.tags, "{tag}")',
            assertion="count >= min_count",
            message="Found only {count} {tag} files in {folder}, expected at least {min_count}",
            severity=Severity.ERROR,
            variables={
                'folder': 'Projects',
                'tag': 'important',
                'min_count': 2
            }
        )
        
        result = runner.run_rule(rule)
        
        # Verify query substitution happened
        assert mock_client.execute_dataview_query.called
        called_query = mock_client.execute_dataview_query.call_args[0][0]
        assert 'Projects' in called_query
        assert 'important' in called_query
        
        assert result.passed is True

    def test_assertion_syntax_error(self):
        """Test handling of assertion syntax errors."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {'values': [1, 2, 3]}
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Bad assertion",
            query="LIST",
            assertion="count ==",  # Syntax error
            message="Test",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Assertion evaluation failed" in result.message
        assert result.details['type'] == 'SyntaxError'

    def test_assertion_name_error(self):
        """Test handling of undefined variables in assertions."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {'values': [1, 2, 3]}
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Undefined variable",
            query="LIST",
            assertion="undefined_var > 0",  # Name error
            message="Test",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Assertion evaluation failed" in result.message
        assert result.details['type'] == 'NameError'

    def test_empty_query_results(self):
        """Test handling of empty query results."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {'values': []}
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="No orphaned notes",
            query="LIST WHERE length(file.inlinks) = 0",
            assertion="count == 0",
            message="Found {count} orphaned notes",
            severity=Severity.WARNING
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is True
        assert result.message == ""

    def test_dataview_not_available(self):
        """Test handling when Dataview plugin is not available."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = None
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Test rule",
            query="LIST",
            assertion="true",
            message="Test",
            severity=Severity.INFO
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Dataview plugin not available" in result.message

    def test_result_formatting(self):
        """Test formatting of results for display."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {
                'values': [
                    {'path': 'very/long/path/to/file1.md'},
                    {'path': 'very/long/path/to/file2.md'},
                    {'path': 'very/long/path/to/file3.md'},
                    {'path': 'very/long/path/to/file4.md'},
                    {'path': 'very/long/path/to/file5.md'},
                    {'path': 'very/long/path/to/file6.md'},
                    {'path': 'very/long/path/to/file7.md'}
                ]
            }
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Too many files",
            query="LIST",
            assertion="count <= 5",
            message="Found {count} files: {results}",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Found 7 files:" in result.message
        assert "(and 2 more)" in result.message  # Should truncate after 5 items


class TestVaultLinter:
    """Test VaultLinter class functionality."""

    @patch('obs_cli.core.linter.ConfigLoader')
    def test_lint_vault_success(self, mock_config_loader, tmp_path):
        """Test successful vault linting."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.rules = [
            {
                'name': 'Rule 1',
                'query': 'LIST',
                'assertion': 'count > 0',
                'message': 'No notes found',
                'severity': 'error'
            },
            {
                'name': 'Rule 2',
                'query': 'LIST WHERE file.size > 1000',
                'assertion': 'count < 100',
                'message': 'Too many large files',
                'severity': 'warning',
                'variables': {}
            }
        ]
        
        mock_config_loader.find_config_file.return_value = tmp_path / ".obs-validate.toml"
        mock_config_loader.load.return_value = mock_config
        
        # Create linter with mocked dataview client
        linter = VaultLinter(str(tmp_path))
        
        # Mock dataview responses
        linter.dataview_client.execute_dataview_query = Mock(side_effect=[
            {'status': 'success', 'result': {'values': [1, 2, 3]}},
            {'status': 'success', 'result': {'values': list(range(50))}}
        ])
        report = linter.lint_vault()
        
        assert report.vault_path == str(tmp_path)
        assert report.total_rules == 2
        assert report.passed_count == 2
        assert report.failed_count == 0
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_lint_vault_no_config(self, tmp_path):
        """Test linting when no config file is found."""
        linter = VaultLinter(str(tmp_path))
        
        with pytest.raises(FileNotFoundError, match="No validation config file found"):
            linter.lint_vault()

    @patch('obs_cli.core.linter.ConfigLoader')
    def test_lint_vault_with_failures(self, mock_config_loader, tmp_path):
        """Test vault linting with rule failures."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.rules = [
            {
                'name': 'Error rule',
                'query': 'LIST',
                'assertion': 'count == 0',  # Will fail
                'message': 'Found {count} items',
                'severity': 'error'
            },
            {
                'name': 'Warning rule',
                'query': 'LIST',
                'assertion': 'count < 5',  # Will fail
                'message': 'Too many items',
                'severity': 'warning'
            },
            {
                'name': 'Info rule',
                'query': 'LIST',
                'assertion': 'count > 100',  # Will fail
                'message': 'Not enough items',
                'severity': 'info'
            }
        ]
        
        mock_config_loader.find_config_file.return_value = tmp_path / ".obs-validate.toml"
        mock_config_loader.load.return_value = mock_config
        
        # Create linter and mock dataview responses
        linter = VaultLinter(str(tmp_path))
        linter.dataview_client.execute_dataview_query = Mock(return_value={
            'status': 'success',
            'result': {'values': list(range(10))}
        })
        report = linter.lint_vault()
        
        assert report.total_rules == 3
        assert report.passed_count == 0
        assert report.failed_count == 3
        assert report.error_count == 1
        assert report.warning_count == 1
        assert report.info_count == 1

    @patch('obs_cli.core.linter.ConfigLoader')
    def test_lint_vault_with_custom_config(self, mock_config_loader, tmp_path):
        """Test vault linting with custom config path."""
        custom_config = tmp_path / "custom-rules.toml"
        custom_config.touch()
        
        mock_config = MagicMock()
        mock_config.rules = []
        
        mock_config_loader.find_config_file.return_value = custom_config
        mock_config_loader.load.return_value = mock_config
        
        linter = VaultLinter(str(tmp_path))
        report = linter.lint_vault(config_path=str(custom_config))
        
        # Verify custom path was used
        mock_config_loader.find_config_file.assert_called_with(str(custom_config), Path(tmp_path))
        assert report.total_rules == 0


class TestErrorHandling:
    """Test error collection and reporting."""

    def test_query_timeout_handling(self):
        """Test handling of query timeouts."""
        mock_client = Mock(spec=DataviewClient)
        
        # Simulate a slow query that times out
        def slow_query(query):
            time.sleep(0.1)  # Simulate delay
            return {'status': 'error', 'error': 'Query timeout'}
        
        mock_client.execute_dataview_query.side_effect = slow_query
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Slow query",
            query="COMPLEX QUERY",
            assertion="true",
            message="Test",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Query timeout" in result.message

    def test_circular_variable_references(self):
        """Test handling of circular variable references."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {'values': []}
        }
        
        runner = RuleRunner(mock_client)
        
        # This would cause issues if not handled properly
        rule = LintRule(
            name="Circular vars",
            query="LIST FROM {a}",
            assertion="true",
            message="Test",
            severity=Severity.INFO,
            variables={
                'a': '{b}',
                'b': '{a}'  # Circular reference
            }
        )
        
        # Should not crash, but query might not be substituted correctly
        result = runner.run_rule(rule)
        
        # The query should execute (even if not substituted perfectly)
        assert isinstance(result, LintResult)

    def test_missing_required_fields_in_query_result(self):
        """Test handling of malformed query results."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            # Missing 'result' field
        }
        
        runner = RuleRunner(mock_client)
        
        rule = LintRule(
            name="Test",
            query="LIST",
            assertion="count == 0",
            message="Test",
            severity=Severity.INFO
        )
        
        result = runner.run_rule(rule)
        
        # Should handle gracefully
        assert isinstance(result, LintResult)
        assert result.passed is True  # Empty results, count == 0

    def test_invalid_assertion_operators(self):
        """Test handling of invalid operators in assertions."""
        mock_client = Mock(spec=DataviewClient)
        mock_client.execute_dataview_query.return_value = {
            'status': 'success',
            'result': {'values': [1, 2, 3]}
        }
        
        runner = RuleRunner(mock_client)
        
        # Test with invalid operator
        rule = LintRule(
            name="Invalid operator",
            query="LIST",
            assertion="count >< 5",  # Invalid operator
            message="Test",
            severity=Severity.ERROR
        )
        
        result = runner.run_rule(rule)
        
        assert result.passed is False
        assert "Assertion evaluation failed" in result.message

    def test_complex_error_scenarios(self):
        """Test multiple error scenarios in sequence."""
        mock_client = Mock(spec=DataviewClient)
        
        # Different responses for different queries
        responses = [
            {'status': 'error', 'error': 'Syntax error in query'},
            None,  # Dataview not available
            {'status': 'success', 'result': {'values': []}},
            {'status': 'success', 'result': {'values': [1, 2, 3]}}
        ]
        mock_client.execute_dataview_query.side_effect = responses
        
        runner = RuleRunner(mock_client)
        
        rules = [
            LintRule(name="Syntax error", query="INVALID", assertion="true", 
                    message="Test", severity=Severity.ERROR),
            LintRule(name="No plugin", query="LIST", assertion="true", 
                    message="Test", severity=Severity.WARNING),
            LintRule(name="Empty results", query="LIST", assertion="count > 0", 
                    message="No items", severity=Severity.INFO),
            LintRule(name="Success", query="LIST", assertion="count == 3", 
                    message="Test", severity=Severity.INFO)
        ]
        
        results = [runner.run_rule(rule) for rule in rules]
        
        assert results[0].passed is False
        assert "Syntax error" in results[0].message
        
        assert results[1].passed is False
        assert "not available" in results[1].message
        
        assert results[2].passed is False
        assert results[2].message == "No items"
        
        assert results[3].passed is True
        assert results[3].message == ""