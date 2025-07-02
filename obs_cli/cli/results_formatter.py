"""Formatter for lint results display."""

import json
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.box import ROUNDED

from obs_cli.core.models import LintReport, LintResult, Severity


class LintResultsFormatter:
    """Formatter for displaying lint results in a clean, readable format."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the formatter.
        
        Args:
            verbose: Whether to show verbose output
        """
        self.verbose = verbose
        self.console = Console()
    
    def display(self, report: LintReport) -> None:
        """
        Display the lint report to the console.
        
        Args:
            report: The lint report to display
        """
        if not report.results:
            self._display_success()
            return
        
        # Group results by severity
        errors = [r for r in report.results if r.severity == Severity.ERROR]
        warnings = [r for r in report.results if r.severity == Severity.WARNING]
        info = [r for r in report.results if r.severity == Severity.INFO]
        
        # Display summary panel
        self._display_summary(report, errors, warnings, info)
        
        # Display results by severity
        if errors:
            self._display_results("Errors", errors, "red")
        
        if warnings:
            self._display_results("Warnings", warnings, "yellow")
        
        if self.verbose and info:
            self._display_results("Information", info, "blue")
        
        # Display statistics if verbose
        if self.verbose:
            self._display_statistics(report)
    
    def _display_success(self) -> None:
        """Display success message when no issues found."""
        panel = Panel(
            Text("✅ No issues found!", style="green bold"),
            title="Lint Results",
            border_style="green",
            box=ROUNDED
        )
        self.console.print(panel)
    
    def _display_summary(
        self,
        report: LintReport,
        errors: List[LintResult],
        warnings: List[LintResult],
        info: List[LintResult],
    ) -> None:
        """Display summary panel."""
        summary_lines = []
        
        if errors:
            summary_lines.append(f"[red]❌ {len(errors)} error{'s' if len(errors) != 1 else ''}[/red]")
        
        if warnings:
            summary_lines.append(f"[yellow]⚠️  {len(warnings)} warning{'s' if len(warnings) != 1 else ''}[/yellow]")
        
        if info and self.verbose:
            summary_lines.append(f"[blue]ℹ️  {len(info)} info message{'s' if len(info) != 1 else ''}[/blue]")
        
        total_files = 0  # Statistics not yet implemented
        summary_lines.append(f"\n[dim]Scanned {total_files} files[/dim]")
        
        panel = Panel(
            "\n".join(summary_lines),
            title="Lint Summary",
            border_style="yellow" if warnings and not errors else ("red" if errors else "green"),
            box=ROUNDED
        )
        self.console.print(panel)
        self.console.print()
    
    def _display_results(self, title: str, results: List[LintResult], color: str) -> None:
        """Display a group of results."""
        table = Table(
            title=title,
            show_header=True,
            header_style=f"bold {color}",
            border_style=color,
            box=ROUNDED,
            padding=(0, 1),
        )
        
        table.add_column("Rule", style="green", no_wrap=True)
        table.add_column("Severity", style="magenta")
        table.add_column("Message", style="white")
        
        for result in results:
            table.add_row(
                result.rule_name,
                result.severity.value,
                result.message
            )
        
        self.console.print(table)
        self.console.print()
    
    def _display_statistics(self, report: LintReport) -> None:
        """Display detailed statistics."""
        # Statistics not yet implemented in LintReport
        return
        
        table = Table(
            title="Statistics",
            show_header=False,
            border_style="dim",
            box=ROUNDED,
            padding=(0, 1),
        )
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        
        # Add statistics rows
        for key, value in stats.items():
            if key == "total_files" and isinstance(value, set):
                value = len(value)
            
            # Format the key nicely
            formatted_key = key.replace("_", " ").title()
            
            # Format the value
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,}"
            elif isinstance(value, dict):
                formatted_value = json.dumps(value, indent=2)
            else:
                formatted_value = str(value)
            
            table.add_row(formatted_key, formatted_value)
        
        self.console.print(table)
        self.console.print()