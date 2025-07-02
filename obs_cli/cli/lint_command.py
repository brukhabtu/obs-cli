"""Lint command implementation for obs-cli."""

import logging
import sys
from pathlib import Path
from typing import Optional

from obs_cli.core.linter import VaultLinter
from obs_cli.core.models import LintReport
from obs_cli.logging import setup_logging
from obs_cli.cli.results_formatter import LintResultsFormatter


logger = logging.getLogger(__name__)


def lint_command(
    vault: Optional[str] = None,
    config: Optional[str] = None,
    debug: bool = False,
    verbose: bool = False,
) -> None:
    """
    Execute the lint command on an Obsidian vault.
    
    Args:
        vault: Path to the Obsidian vault
        config: Path to the validation configuration file
        debug: Enable debug mode
        verbose: Enable verbose output
    """
    # Setup logging first
    log_level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
    setup_logging(level=log_level)
    
    logger.debug("Starting lint command")
    logger.debug(f"Vault: {vault}")
    logger.debug(f"Config: {config}")
    logger.debug(f"Debug: {debug}")
    logger.debug(f"Verbose: {verbose}")
    
    try:
        # Validate inputs
        if not vault:
            logger.error("No vault path provided")
            print("Error: No vault path provided. Use --vault or set OBSIDIAN_VAULT environment variable.")
            sys.exit(1)
        
        vault_path = Path(vault).expanduser().resolve()
        if not vault_path.exists() or not vault_path.is_dir():
            logger.error(f"Invalid vault path: {vault_path}")
            print(f"Error: Vault path does not exist or is not a directory: {vault_path}")
            sys.exit(1)
        
        config_path = None
        if config:
            config_path = Path(config).expanduser().resolve()
            if not config_path.exists() or not config_path.is_file():
                logger.error(f"Invalid config path: {config_path}")
                print(f"Error: Config file does not exist: {config_path}")
                sys.exit(1)
        
        # Create VaultLinter instance
        logger.info(f"Creating VaultLinter for vault: {vault_path}")
        linter = VaultLinter(str(vault_path))
        
        # Run linting
        logger.info("Running vault linting...")
        report = linter.lint_vault(config_path=str(config_path) if config_path else None)
        
        # Format and display results
        formatter = LintResultsFormatter(verbose=verbose)
        formatter.display(report)
        
        # Exit with appropriate code
        exit_code = 1 if report.has_errors else 0
        logger.debug(f"Exiting with code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.exception("Unexpected error during linting")
        print(f"Error: {str(e)}")
        sys.exit(1)