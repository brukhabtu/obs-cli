"""Core data models for obs-cli."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime

from obs_cli.logging import get_logger


logger = get_logger(__name__)


class Severity(str, Enum):
    """Severity levels for linting rules."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintRule:
    """Configuration for a single validation rule.
    
    Attributes:
        name: Unique identifier for the rule
        query: Dataview query to execute
        assertion: Condition to evaluate (e.g., "count == 0", "all tags present")
        message: User-friendly message describing the rule
        severity: Rule severity level (error, warning, info)
        variables: Optional variables to substitute in query
    """
    name: str
    query: str
    assertion: str
    message: str
    severity: Severity = Severity.INFO
    variables: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate severity level."""
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity.lower())


@dataclass
class LintResult:
    """Result of executing one linting rule.
    
    Migrated from ValidationResult, represents the outcome of a single rule execution.
    """
    rule_name: str
    severity: Severity
    passed: bool
    message: str = ""
    details: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate severity level."""
        if isinstance(self.severity, str):
            self.severity = Severity(self.severity.lower())
    
    @property
    def failed(self) -> bool:
        """Check if the rule failed."""
        return not self.passed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LintReport:
    """Aggregated results from multiple linting rules.
    
    Provides summary statistics and methods for analyzing linting results.
    """
    results: List[LintResult] = field(default_factory=list)
    vault_path: Optional[str] = None
    run_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_rules(self) -> int:
        """Total number of rules executed."""
        return len(self.results)
    
    @property
    def passed_count(self) -> int:
        """Number of rules that passed."""
        return sum(1 for result in self.results if result.passed)
    
    @property
    def failed_count(self) -> int:
        """Number of rules that failed."""
        return sum(1 for result in self.results if result.failed)
    
    @property
    def error_count(self) -> int:
        """Number of failed rules with error severity."""
        return sum(1 for result in self.results 
                  if result.failed and result.severity == Severity.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Number of failed rules with warning severity."""
        return sum(1 for result in self.results 
                  if result.failed and result.severity == Severity.WARNING)
    
    @property
    def info_count(self) -> int:
        """Number of failed rules with info severity."""
        return sum(1 for result in self.results 
                  if result.failed and result.severity == Severity.INFO)
    
    @property
    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return self.error_count > 0
    
    @property
    def has_failures(self) -> bool:
        """Check if any rules failed."""
        return self.failed_count > 0
    
    def add_result(self, result: LintResult) -> None:
        """Add a single result to the report."""
        self.results.append(result)
    
    def get_failures(self) -> List[LintResult]:
        """Get all failed results."""
        return [result for result in self.results if result.failed]
    
    def get_by_severity(self, severity: Severity) -> List[LintResult]:
        """Get results filtered by severity."""
        return [result for result in self.results if result.severity == severity]
    
    def summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "vault_path": self.vault_path,
            "run_timestamp": self.run_timestamp.isoformat(),
            "total_rules": self.total_rules,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "info": self.info_count,
            "has_errors": self.has_errors,
            "has_failures": self.has_failures
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire report to dictionary."""
        return {
            "summary": self.summary(),
            "results": [result.to_dict() for result in self.results]
        }


@dataclass
class QueryResult:
    """Raw response from Dataview query execution.
    
    Represents the unprocessed result of executing a Dataview query.
    """
    query: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    result_count: Optional[int] = None
    
    @property
    def has_data(self) -> bool:
        """Check if query returned data."""
        return self.success and self.data is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "result_count": self.result_count
        }


@dataclass
class QueryData:
    """Structured data extracted from query results.
    
    Provides typed access to Dataview query results with support for
    different query types (LIST, TABLE, TASK).
    """
    query_type: str  # LIST, TABLE, TASK
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Optional[Any] = None
    
    @classmethod
    def from_query_result(cls, result: QueryResult, query_type: str = "LIST") -> "QueryData":
        """Create QueryData from a QueryResult."""
        if not result.has_data:
            return cls(query_type=query_type)
        
        # Parse data based on query type
        data = cls(query_type=query_type, raw_data=result.data)
        
        if isinstance(result.data, list):
            if query_type == "TABLE" and result.data:
                # For TABLE queries, first item might be headers
                if isinstance(result.data[0], dict):
                    data.columns = list(result.data[0].keys())
                    data.rows = result.data
                elif len(result.data) > 1:
                    # Assume first row is headers
                    data.columns = result.data[0] if isinstance(result.data[0], list) else []
                    data.rows = [dict(zip(data.columns, row)) for row in result.data[1:] 
                               if isinstance(row, list)]
            else:
                # For LIST queries, create simple rows
                data.rows = [{"value": item} for item in result.data]
                data.columns = ["value"]
        elif isinstance(result.data, dict):
            # Single dictionary result
            data.columns = list(result.data.keys())
            data.rows = [result.data]
        
        return data
    
    @property
    def row_count(self) -> int:
        """Number of data rows."""
        return len(self.rows)
    
    @property
    def is_empty(self) -> bool:
        """Check if query returned no data."""
        return self.row_count == 0
    
    def get_column(self, column_name: str) -> List[Any]:
        """Extract values from a specific column."""
        if column_name not in self.columns:
            raise ValueError(f"Column '{column_name}' not found. Available columns: {self.columns}")
        return [row.get(column_name) for row in self.rows]
    
    def filter_rows(self, predicate) -> List[Dict[str, Any]]:
        """Filter rows based on a predicate function."""
        return [row for row in self.rows if predicate(row)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_type": self.query_type,
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count
        }