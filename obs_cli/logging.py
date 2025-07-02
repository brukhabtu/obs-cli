"""Centralized logging configuration for obs-cli.

This module provides a unified logging interface for all obs-cli components,
with support for console and file output, different log levels, and
module-specific configuration.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any


# Default format strings
CONSOLE_FORMAT = "%(levelname)-8s %(message)s"
CONSOLE_FORMAT_VERBOSE = "%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s"
CONSOLE_FORMAT_DEBUG = "%(asctime)s [%(name)-20s:%(lineno)d] %(levelname)-8s %(message)s"
FILE_FORMAT = "%(asctime)s [%(name)s:%(lineno)d] %(levelname)-8s %(message)s"

# Module-specific log levels
MODULE_LOG_LEVELS: Dict[str, str] = {
    # Core modules
    "obs_cli": "INFO",
    "obs_cli.dquery": "INFO",
    "obs_cli.core.dataview": "INFO",
    "obs_cli.core.linter": "INFO",
    "obs_cli.core.config": "INFO",
    "obs_cli.cli": "INFO",
    
    # Third-party modules (quieter by default)
    "urllib3": "WARNING",
    "requests": "WARNING",
}


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    debug: bool = False
) -> None:
    """Configure the root logger and handlers for the application.
    
    Args:
        level: Base log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        verbose: Enable verbose console output (includes timestamps)
        debug: Enable debug mode (overrides level to DEBUG, includes line numbers)
    """
    # Convert level string to logging constant
    if debug:
        level = "DEBUG"
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Remove any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(logging.DEBUG)  # Capture everything at root level
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    
    # Choose console format based on mode
    if debug:
        console_format = CONSOLE_FORMAT_DEBUG
    elif verbose:
        console_format = CONSOLE_FORMAT_VERBOSE
    else:
        console_format = CONSOLE_FORMAT
    
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if requested)
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent unbounded growth
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(FILE_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Apply module-specific log levels
    for module_name, module_level in MODULE_LOG_LEVELS.items():
        module_logger = logging.getLogger(module_name)
        module_numeric_level = getattr(logging, module_level.upper(), logging.INFO)
        module_logger.setLevel(module_numeric_level)
    
    # Log initial configuration
    logger = get_logger(__name__)
    logger.debug(f"Logging configured: level={level}, verbose={verbose}, debug={debug}, log_file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def enable_debug_logging() -> None:
    """Enable debug logging for all obs_cli modules.
    
    This is a convenience function for quickly enabling debug output
    during development or troubleshooting.
    """
    # Set root logger to DEBUG
    logging.getLogger().setLevel(logging.DEBUG)
    
    # Set all obs_cli loggers to DEBUG
    for logger_name in logging.getLogger().manager.loggerDict:
        if logger_name.startswith("obs_cli"):
            logging.getLogger(logger_name).setLevel(logging.DEBUG)
    
    # Update console handler to show debug format
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(logging.Formatter(CONSOLE_FORMAT_DEBUG))


def configure_module_logging(module_levels: Dict[str, str]) -> None:
    """Configure log levels for specific modules.
    
    Args:
        module_levels: Dictionary mapping module names to log levels
    """
    for module_name, level in module_levels.items():
        logger = logging.getLogger(module_name)
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)


def add_log_handler(handler: logging.Handler) -> None:
    """Add a custom log handler to the root logger.
    
    Args:
        handler: Configured logging handler
    """
    logging.getLogger().addHandler(handler)


def remove_console_handler() -> None:
    """Remove the console handler from the root logger.
    
    Useful for testing or when console output should be suppressed.
    """
    root_logger = logging.getLogger()
    root_logger.handlers = [
        h for h in root_logger.handlers 
        if not isinstance(h, logging.StreamHandler)
    ]


# Convenience functions for common log operations
def log_exception(logger: logging.Logger, msg: str, exc_info: bool = True) -> None:
    """Log an exception with traceback.
    
    Args:
        logger: Logger instance
        msg: Error message
        exc_info: Include exception traceback (default: True)
    """
    logger.error(msg, exc_info=exc_info)


def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """Log a performance metric.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        duration: Duration in seconds
    """
    logger.info(f"{operation} completed in {duration:.3f}s")