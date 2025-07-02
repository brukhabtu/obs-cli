"""Template processing module for variable substitution in queries and configurations."""

import json
from typing import Dict, Any

from obs_cli.logging import get_logger

logger = get_logger(__name__)


class TemplateProcessor:
    """Handles template variable substitution for queries and configurations."""
    
    @staticmethod
    def substitute_variables(template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in a template string using Python's format method.
        
        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variable name -> value mappings
            
        Returns:
            String with variables substituted
            
        Example:
            >>> template = 'LIST WHERE contains({tags}, file.tags) AND size > {max_size}'
            >>> variables = {"tags": '["#daily", "#meeting"]', "max_size": 1000}
            >>> TemplateProcessor.substitute_variables(template, variables)
            'LIST WHERE contains(["#daily", "#meeting"], file.tags) AND size > 1000'
        """
        if not variables:
            logger.debug("No variables provided for substitution")
            return template
        
        logger.debug(f"Substituting variables in template: {template}")
        logger.debug(f"Variables provided: {variables}")
        
        # Convert all values to strings for template substitution
        string_vars = {}
        for key, value in variables.items():
            if isinstance(value, list):
                # Convert lists to JSON format for Dataview
                string_vars[key] = json.dumps(value)
                logger.debug(f"Converted list variable '{key}': {value} -> {string_vars[key]}")
            elif isinstance(value, str):
                # Keep strings as-is if they're already quoted, otherwise quote them
                if value.startswith('"') and value.endswith('"'):
                    string_vars[key] = value
                else:
                    string_vars[key] = json.dumps(value)
                logger.debug(f"Processed string variable '{key}': {value} -> {string_vars[key]}")
            elif isinstance(value, bool):
                # Convert booleans to lowercase for consistency with JSON/Dataview
                string_vars[key] = "true" if value else "false"
                logger.debug(f"Converted boolean variable '{key}': {value} -> {string_vars[key]}")
            else:
                # Convert other types (int, float) to string
                string_vars[key] = str(value)
                logger.debug(f"Converted variable '{key}': {value} -> {string_vars[key]}")
        
        try:
            result = template.format(**string_vars)
            logger.debug(f"Template substitution successful: {result}")
            return result
        except KeyError as e:
            logger.error(f"Undefined variable in template: {e}")
            raise ValueError(f"Undefined variable in template: {e}")
        except ValueError as e:
            logger.error(f"Template formatting error: {e}")
            raise ValueError(f"Template formatting error: {e}")