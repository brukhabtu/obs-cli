"""Custom exceptions for obs-cli."""


class ObsCliError(Exception):
    """Base exception for obs-cli."""
    pass


class VaultNotFoundError(ObsCliError):
    """Raised when the Obsidian vault cannot be found."""
    pass


class DataviewNotAvailableError(ObsCliError):
    """Raised when Dataview functionality is not available."""
    pass


class QueryTimeoutError(ObsCliError):
    """Raised when a query takes too long to execute."""
    pass


class DatabaseCorruptedError(ObsCliError):
    """Raised when the metadata database is corrupted or invalid."""
    pass