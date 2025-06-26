"""Base formatter class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseFormatter(ABC):
    """Base class for output formatters."""
    
    @abstractmethod
    def format(
        self, 
        data: List[Dict[str, Any]], 
        headers: Optional[List[str]] = None,
        keys: Optional[List[str]] = None
    ) -> str:
        """Format data for output."""
        pass