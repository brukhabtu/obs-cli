"""Main linting engine for executing validation rules against Obsidian vaults."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import time

from obs_cli.core.models import LintRule, LintResult, LintReport, Severity, QueryResult, QueryData
from obs_cli.core.dataview import DataviewClient
from obs_cli.core.config import ConfigLoader, ValidationConfig, ValidationError
from obs_cli.core.templates import TemplateProcessor
from obs_cli.logging import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_QUERY_TIMEOUT = 30000  # milliseconds
MAX_RESULT_DISPLAY_LENGTH = 500  # characters


class VaultLinter:
    """Main orchestrator for linting an Obsidian vault.
    
    This class coordinates the entire linting process:
    1. Loads configuration using ConfigLoader
    2. Creates RuleRunner instances for each rule
    3. Executes rules and collects results
    4. Generates a comprehensive LintReport
    """
    
    def __init__(self, vault_path: str):
        """Initialize the linter with a vault path.
        
        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.dataview_client = DataviewClient(vault_path=vault_path)
        logger.info(f"Initialized VaultLinter for vault: {self.vault_path}")
    
    def lint_vault(self, config_path: Optional[str] = None) -> LintReport:
        """Execute all linting rules against the vault.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            LintReport containing all results
            
        Raises:
            ValidationError: If configuration is invalid
            FileNotFoundError: If config file not found
        """
        logger.info(f"Starting vault linting. Config path: {config_path}")
        start_time = time.time()
        
        # Find and load configuration
        config_file = ConfigLoader.find_config_file(config_path, self.vault_path)
        if config_file is None:
            raise FileNotFoundError(
                "No validation config file found. Expected .obs-validate.yaml or "
                ".obs-validate.toml in vault root or current directory."
            )
        
        config = ConfigLoader.load(str(config_file))
        logger.info(f"Loaded {len(config.rules)} rules from configuration")
        
        # Create report
        report = LintReport(vault_path=str(self.vault_path))
        
        # Create RuleRunner
        rule_runner = RuleRunner(self.dataview_client)
        
        # Execute each rule
        for rule_data in config.rules:
            # Convert rule data to LintRule model
            rule = LintRule(
                name=rule_data['name'],
                query=rule_data['query'],
                assertion=rule_data['assertion'],
                message=rule_data['message'],
                severity=rule_data['severity'],
                variables=rule_data.get('variables', {})
            )
            
            logger.debug(f"Executing rule: {rule.name}")
            result = rule_runner.run_rule(rule)
            report.add_result(result)
            
            # Log progress
            if result.failed:
                logger.warning(f"Rule '{rule.name}' failed: {result.message}")
            else:
                logger.debug(f"Rule '{rule.name}' passed")
        
        # Log summary
        elapsed = time.time() - start_time
        logger.info(
            f"Linting completed in {elapsed:.2f}s. "
            f"Total: {report.total_rules}, Passed: {report.passed_count}, "
            f"Failed: {report.failed_count} (Errors: {report.error_count}, "
            f"Warnings: {report.warning_count}, Info: {report.info_count})"
        )
        
        return report


class RuleRunner:
    """Executes individual linting rules.
    
    This class handles the execution of a single rule:
    1. Substitutes variables in the query
    2. Executes the Dataview query
    3. Evaluates the assertion
    4. Formats the result message
    """
    
    def __init__(self, dataview_client: DataviewClient):
        """Initialize the rule runner.
        
        Args:
            dataview_client: Client for executing Dataview queries
        """
        self.dataview_client = dataview_client
        logger.debug("Initialized RuleRunner")
    
    def run_rule(self, rule: LintRule) -> LintResult:
        """Execute a single linting rule.
        
        Args:
            rule: The rule to execute
            
        Returns:
            LintResult with the outcome
        """
        logger.debug(f"Running rule: {rule.name}")
        
        try:
            # Execute query
            query_result = self._execute_query(rule)
            
            if not query_result.success:
                return self._create_query_error_result(rule, query_result)
            
            # Extract data
            query_data = QueryData.from_query_result(query_result)
            
            # Evaluate assertion
            assertion_passed = self._evaluate_assertion(rule, query_data)
            
            # Format message
            message = self._format_message(rule, query_data, assertion_passed)
            
            return LintResult(
                rule_name=rule.name,
                severity=rule.severity,
                passed=assertion_passed,
                message=message if not assertion_passed else "",
                details=query_data.to_dict() if not assertion_passed else None
            )
            
        except Exception as e:
            logger.error(f"Rule execution failed for '{rule.name}': {e}", exc_info=True)
            return self._create_exception_result(rule, e)
    
    def _execute_query(self, rule: LintRule) -> QueryResult:
        """Execute the Dataview query for a rule.
        
        Args:
            rule: Rule containing the query
            
        Returns:
            QueryResult with execution outcome
        """
        query = rule.query
        
        # Substitute variables if present
        if rule.variables:
            query = TemplateProcessor.substitute_variables(query, rule.variables)
            logger.debug(f"Query after substitution: {query}")
        
        # Execute query
        start_time = time.time()
        raw_result = self.dataview_client.execute_dataview_query(query)
        execution_time = time.time() - start_time
        
        # Convert to QueryResult
        if raw_result is None:
            return QueryResult(
                query=query,
                success=False,
                error="Dataview plugin not available or query execution failed",
                execution_time=execution_time
            )
        
        if raw_result.get('status') == 'success':
            result_data = raw_result.get('result', {})
            values = result_data.get('values', [])
            
            return QueryResult(
                query=query,
                success=True,
                data=values,
                execution_time=execution_time,
                result_count=len(values)
            )
        else:
            return QueryResult(
                query=query,
                success=False,
                error=raw_result.get('error', 'Unknown query error'),
                execution_time=execution_time
            )
    
    def _evaluate_assertion(self, rule: LintRule, data: QueryData) -> bool:
        """Evaluate the assertion for a rule.
        
        Args:
            rule: Rule containing the assertion
            data: Query results to evaluate against
            
        Returns:
            True if assertion passes, False otherwise
        """
        assertion = rule.assertion
        
        # Build evaluation context
        context = {
            'results': data.rows,
            'count': data.row_count,
            'len': len,
            'any': any,
            'all': all,
            'sum': sum,
            'min': min,
            'max': max,
        }
        
        # Add variables to context
        if rule.variables:
            context.update(rule.variables)
        
        # Add convenient aliases
        context['result_count'] = data.row_count
        context['is_empty'] = data.is_empty
        
        try:
            # Evaluate assertion safely
            result = eval(assertion, {"__builtins__": {}}, context)
            logger.debug(f"Assertion '{assertion}' evaluated to: {result}")
            return bool(result)
        except Exception as e:
            logger.error(f"Assertion evaluation failed: {e}")
            raise
    
    def _format_message(self, rule: LintRule, data: QueryData, assertion_passed: bool) -> str:
        """Format the message for a rule result.
        
        Args:
            rule: Rule containing the message template
            data: Query results for variable substitution
            assertion_passed: Whether the assertion passed
            
        Returns:
            Formatted message string
        """
        if assertion_passed:
            return ""
        
        message = rule.message
        
        # Build substitution variables
        variables = {
            'count': data.row_count,
            'results': self._format_results_for_display(data.rows)
        }
        
        # Add rule variables
        if rule.variables:
            variables.update(rule.variables)
        
        try:
            return TemplateProcessor.substitute_variables(message, variables)
        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Message substitution failed: {e}")
            # Return unsubstituted message as fallback
            return message
    
    def _format_results_for_display(self, results: List[Dict[str, Any]], max_items: int = 5) -> str:
        """Format query results for readable display in error messages.
        
        Args:
            results: List of result rows
            max_items: Maximum number of items to display
            
        Returns:
            Formatted string representation
        """
        if not results:
            return "[]"
        
        # Extract meaningful display values
        display_items = []
        
        for result in results[:max_items]:
            # Try to find the most meaningful field to display
            if 'path' in result:
                display_items.append(result['path'])
            elif 'file' in result and isinstance(result['file'], dict) and 'path' in result['file']:
                display_items.append(result['file']['path'])
            elif 'name' in result:
                display_items.append(result['name'])
            elif 'value' in result:
                display_items.append(str(result['value']))
            else:
                # Use first non-empty value
                for value in result.values():
                    if value:
                        display_items.append(str(value))
                        break
        
        if display_items:
            display = ", ".join(display_items)
            if len(results) > max_items:
                display += f" (and {len(results) - max_items} more)"
            return display
        else:
            # Fallback to string representation
            return str(results)[:MAX_RESULT_DISPLAY_LENGTH] + ("..." if len(str(results)) > MAX_RESULT_DISPLAY_LENGTH else "")
    
    def _create_query_error_result(self, rule: LintRule, query_result: QueryResult) -> LintResult:
        """Create a LintResult for query errors.
        
        Args:
            rule: The rule that failed
            query_result: Query result with error information
            
        Returns:
            LintResult indicating query failure
        """
        return LintResult(
            rule_name=rule.name,
            severity=rule.severity,
            passed=False,
            message=f"Query failed: {query_result.error}",
            details={'query': query_result.query, 'error': query_result.error}
        )
    
    def _create_exception_result(self, rule: LintRule, exception: Exception) -> LintResult:
        """Create a LintResult for exceptions.
        
        Args:
            rule: The rule that failed
            exception: The exception that occurred
            
        Returns:
            LintResult indicating execution failure
        """
        if isinstance(exception, (SyntaxError, NameError)):
            message = f"Assertion evaluation failed: {exception}"
        else:
            message = f"Rule execution failed: {exception}"
        
        return LintResult(
            rule_name=rule.name,
            severity=rule.severity,
            passed=False,
            message=message,
            details={'error': str(exception), 'type': type(exception).__name__}
        )