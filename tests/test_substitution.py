"""Tests for template string substitution."""

import pytest
from obs_cli.core.templates import TemplateProcessor


class TestTemplateProcessor:
    """Test template string substitution functionality."""
    
    def test_no_variables(self):
        """Test template with no variables returns unchanged."""
        template = "LIST FROM \"Daily\""
        result = TemplateProcessor.substitute_variables(template, {})
        assert result == template
    
    def test_simple_string_substitution(self):
        """Test substituting simple string values."""
        template = "LIST FROM {folder}"
        variables = {"folder": "Daily"}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == 'LIST FROM "Daily"'
    
    def test_list_substitution(self):
        """Test substituting list values as JSON arrays."""
        template = "LIST WHERE contains({tags}, file.tags)"
        variables = {"tags": ["#daily", "#meeting", "#urgent"]}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == 'LIST WHERE contains(["#daily", "#meeting", "#urgent"], file.tags)'
    
    def test_number_substitution(self):
        """Test substituting numeric values."""
        template = "LIST WHERE file.size > {max_size} AND file.lines < {max_lines}"
        variables = {"max_size": 1000, "max_lines": 50}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == "LIST WHERE file.size > 1000 AND file.lines < 50"
    
    def test_boolean_substitution(self):
        """Test substituting boolean values."""
        template = "LIST WHERE file.completed = {is_done}"
        variables = {"is_done": True}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == "LIST WHERE file.completed = true"
    
    def test_mixed_types_substitution(self):
        """Test substituting mixed variable types."""
        template = '''
TABLE file.name, file.tags
FROM {folder}
WHERE contains({tags}, file.tags) 
  AND file.size > {min_size}
  AND file.published = {published}
'''
        variables = {
            "folder": "Projects",
            "tags": ["#active", "#review"],
            "min_size": 500,
            "published": False
        }
        
        expected = '''
TABLE file.name, file.tags
FROM "Projects"
WHERE contains(["#active", "#review"], file.tags) 
  AND file.size > 500
  AND file.published = false
'''
        
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == expected
    
    def test_quoted_string_preserved(self):
        """Test that already quoted strings are preserved."""
        template = "LIST FROM {folder}"
        variables = {"folder": '"Already Quoted"'}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == 'LIST FROM "Already Quoted"'
    
    def test_multiple_same_variable(self):
        """Test substituting the same variable multiple times."""
        template = "LIST WHERE file.name = {name} OR file.alias = {name}"
        variables = {"name": "important"}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == 'LIST WHERE file.name = "important" OR file.alias = "important"'
    
    def test_undefined_variable_error(self):
        """Test error when template uses undefined variable."""
        template = "LIST WHERE contains({undefined_var}, file.tags)"
        variables = {"defined_var": ["#test"]}
        
        with pytest.raises(ValueError, match="Undefined variable in template"):
            TemplateProcessor.substitute_variables(template, variables)
    
    def test_empty_list_substitution(self):
        """Test substituting empty list."""
        template = "LIST WHERE contains({tags}, file.tags)"
        variables = {"tags": []}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == "LIST WHERE contains([], file.tags)"
    
    def test_nested_list_substitution(self):
        """Test substituting list with nested structures."""
        template = "LIST WHERE contains({complex_data}, file.metadata)"
        variables = {"complex_data": [{"type": "note", "priority": 1}, {"type": "task", "priority": 2}]}
        result = TemplateProcessor.substitute_variables(template, variables)
        expected = 'LIST WHERE contains([{"type": "note", "priority": 1}, {"type": "task", "priority": 2}], file.metadata)'
        assert result == expected
    
    def test_special_characters_in_string(self):
        """Test substituting strings with special characters."""
        template = "LIST WHERE file.content contains {search_term}"
        variables = {"search_term": "hello \"world\" with 'quotes'"}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == 'LIST WHERE file.content contains "hello \\"world\\" with \'quotes\'"'
    
    def test_float_substitution(self):
        """Test substituting float values."""
        template = "LIST WHERE file.rating >= {min_rating}"
        variables = {"min_rating": 4.5}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == "LIST WHERE file.rating >= 4.5"
    
    def test_zero_values(self):
        """Test substituting zero values of different types."""
        template = "LIST WHERE file.count = {zero_int} AND file.score = {zero_float} AND file.active = {zero_bool}"
        variables = {"zero_int": 0, "zero_float": 0.0, "zero_bool": False}
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == "LIST WHERE file.count = 0 AND file.score = 0.0 AND file.active = false"
    
    def test_complex_real_world_example(self):
        """Test a complex real-world validation rule."""
        template = '''
TABLE file.name, file.tags,
    filter(file.tags, (tag) => 
        !contains({exact_tags}, tag) AND
        !any(map({prefix_tags}, (prefix) => startswith(tag, prefix))) AND
        any(map({excluded_contains}, (exc) => contains(tag, exc)))
    ) as invalid_tags
FROM ""
WHERE length(invalid_tags) > 0
'''
        
        variables = {
            "exact_tags": ["#daily", "#meeting", "#urgent"],
            "prefix_tags": ["#lang/", "#person/", "#project/"],
            "excluded_contains": ["#temp", "#draft"]
        }
        
        expected = '''
TABLE file.name, file.tags,
    filter(file.tags, (tag) => 
        !contains(["#daily", "#meeting", "#urgent"], tag) AND
        !any(map(["#lang/", "#person/", "#project/"], (prefix) => startswith(tag, prefix))) AND
        any(map(["#temp", "#draft"], (exc) => contains(tag, exc)))
    ) as invalid_tags
FROM ""
WHERE length(invalid_tags) > 0
'''
        
        result = TemplateProcessor.substitute_variables(template, variables)
        assert result == expected