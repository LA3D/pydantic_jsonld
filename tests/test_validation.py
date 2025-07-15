"""
Tests for the validation module.
"""

import pytest
from pydantic import ValidationError

from pydantic_jsonld.validation import validate_context, ContextTerm, JsonLDContext


class TestContextTerm:
    """Test the ContextTerm validation."""
    
    def test_valid_term(self):
        """Test valid term definition."""
        term = ContextTerm(term_definition={"@id": "schema:name"})
        assert term.term_definition["@id"] == "schema:name"
    
    def test_valid_term_with_type(self):
        """Test valid term with type."""
        term = ContextTerm(term_definition={
            "@id": "schema:name",
            "@type": "xsd:string"
        })
        assert term.term_definition["@type"] == "xsd:string"
    
    def test_valid_term_with_container(self):
        """Test valid term with container."""
        term = ContextTerm(term_definition={
            "@id": "schema:keywords",
            "@container": "@set"
        })
        assert term.term_definition["@container"] == "@set"
    
    def test_valid_term_with_language(self):
        """Test valid term with language."""
        term = ContextTerm(term_definition={
            "@id": "schema:name",
            "@language": "en"
        })
        assert term.term_definition["@language"] == "en"
    
    def test_missing_id(self):
        """Test term without @id raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ContextTerm(term_definition={"@type": "xsd:string"})
        
        assert "must have @id property" in str(exc_info.value)
    
    def test_unknown_keyword(self):
        """Test term with unknown keyword raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ContextTerm(term_definition={
                "@id": "schema:name",
                "@unknown": "value"
            })
        
        assert "Unknown JSON-LD keywords" in str(exc_info.value)
    
    def test_invalid_type_value(self):
        """Test term with invalid @type value."""
        with pytest.raises(ValidationError) as exc_info:
            ContextTerm(term_definition={
                "@id": "schema:name",
                "@type": 123  # Should be string
            })
        
        assert "@type must be a string" in str(exc_info.value)
    
    def test_invalid_container_value(self):
        """Test term with invalid @container value."""
        with pytest.raises(ValidationError) as exc_info:
            ContextTerm(term_definition={
                "@id": "schema:name",
                "@container": "invalid"
            })
        
        assert "Invalid @container value" in str(exc_info.value)
    
    def test_valid_container_list(self):
        """Test term with valid @container list."""
        term = ContextTerm(term_definition={
            "@id": "schema:name",
            "@container": ["@set", "@language"]
        })
        assert term.term_definition["@container"] == ["@set", "@language"]
    
    def test_invalid_container_list(self):
        """Test term with invalid @container list."""
        with pytest.raises(ValidationError) as exc_info:
            ContextTerm(term_definition={
                "@id": "schema:name",
                "@container": ["@set", "invalid"]
            })
        
        assert "Invalid @container value" in str(exc_info.value)
    
    def test_invalid_language_value(self):
        """Test term with invalid @language value."""
        with pytest.raises(ValidationError) as exc_info:
            ContextTerm(term_definition={
                "@id": "schema:name",
                "@language": 123  # Should be string
            })
        
        assert "@language must be a string" in str(exc_info.value)


class TestJsonLDContext:
    """Test the JsonLDContext validation."""
    
    def test_valid_simple_context(self):
        """Test valid simple context."""
        context = JsonLDContext(context={
            "name": {"@id": "schema:name"},
            "age": {"@id": "schema:age", "@type": "xsd:integer"}
        })
        assert "name" in context.context
        assert "age" in context.context
    
    def test_valid_context_with_keywords(self):
        """Test valid context with JSON-LD keywords."""
        context = JsonLDContext(context={
            "@version": 1.1,
            "@base": "https://example.org/",
            "@vocab": "https://schema.org/",
            "name": {"@id": "schema:name"}
        })
        assert context.context["@version"] == 1.1
        assert context.context["@base"] == "https://example.org/"
        assert context.context["@vocab"] == "https://schema.org/"
    
    def test_valid_context_array(self):
        """Test valid context array."""
        context = JsonLDContext(context=[
            "https://schema.org/",
            {
                "name": {"@id": "schema:name"},
                "age": {"@id": "schema:age", "@type": "xsd:integer"}
            }
        ])
        assert isinstance(context.context, list)
        assert len(context.context) == 2
    
    def test_valid_string_mappings(self):
        """Test valid string mappings in context."""
        context = JsonLDContext(context={
            "schema": "https://schema.org/",
            "name": "schema:name"  # Simple string mapping
        })
        assert context.context["schema"] == "https://schema.org/"
        assert context.context["name"] == "schema:name"
    
    def test_invalid_version(self):
        """Test invalid @version value."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "@version": 2.0,  # Should be 1.1
                "name": {"@id": "schema:name"}
            })
        
        assert "@version must be 1.1" in str(exc_info.value)
    
    def test_invalid_base(self):
        """Test invalid @base value."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "@base": 123,  # Should be string
                "name": {"@id": "schema:name"}
            })
        
        assert "@base must be a string" in str(exc_info.value)
    
    def test_invalid_vocab(self):
        """Test invalid @vocab value."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "@vocab": 123,  # Should be string
                "name": {"@id": "schema:name"}
            })
        
        assert "@vocab must be a string" in str(exc_info.value)
    
    def test_invalid_language(self):
        """Test invalid @language value."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "@language": 123,  # Should be string
                "name": {"@id": "schema:name"}
            })
        
        assert "@language must be a string" in str(exc_info.value)
    
    def test_invalid_protected(self):
        """Test invalid @protected value."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "@protected": "true",  # Should be boolean
                "name": {"@id": "schema:name"}
            })
        
        assert "@protected must be a boolean" in str(exc_info.value)
    
    def test_unknown_keyword(self):
        """Test unknown JSON-LD keyword."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "@unknown": "value",
                "name": {"@id": "schema:name"}
            })
        
        assert "Unknown JSON-LD keyword" in str(exc_info.value)
    
    def test_invalid_term_value(self):
        """Test invalid term value."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context={
                "name": 123  # Should be string or dict
            })
        
        assert "must be string or dict" in str(exc_info.value)
    
    def test_invalid_context_array_item(self):
        """Test invalid item in context array."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context=[
                "https://schema.org/",
                123  # Should be string or dict
            ])
        
        assert "must be string or dict" in str(exc_info.value)
    
    def test_invalid_remote_context_url(self):
        """Test invalid remote context URL."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context=[
                "invalid-url",  # Should be valid URL
                {"name": {"@id": "schema:name"}}
            ])
        
        assert "must be a valid URL" in str(exc_info.value)
    
    def test_invalid_context_type(self):
        """Test invalid context type."""
        with pytest.raises(ValidationError) as exc_info:
            JsonLDContext(context="invalid")  # Should be dict or list
        
        assert "Context must be a dictionary or array" in str(exc_info.value)


class TestValidateContext:
    """Test the validate_context function."""
    
    def test_valid_context_document(self):
        """Test valid context document."""
        context_doc = {
            "@context": {
                "name": {"@id": "schema:name"},
                "age": {"@id": "schema:age", "@type": "xsd:integer"}
            }
        }
        
        # Should not raise any exception
        validate_context(context_doc)
    
    def test_valid_context_with_array(self):
        """Test valid context document with array."""
        context_doc = {
            "@context": [
                "https://schema.org/",
                {
                    "name": {"@id": "schema:name"},
                    "age": {"@id": "schema:age", "@type": "xsd:integer"}
                }
            ]
        }
        
        # Should not raise any exception
        validate_context(context_doc)
    
    def test_missing_context_property(self):
        """Test document without @context property."""
        context_doc = {
            "name": {"@id": "schema:name"}
        }
        
        with pytest.raises(ValueError) as exc_info:
            validate_context(context_doc)
        
        assert "must have @context property" in str(exc_info.value)
    
    def test_invalid_context_content(self):
        """Test document with invalid context content."""
        context_doc = {
            "@context": {
                "name": {"@invalid": "value"}  # Invalid term
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            validate_context(context_doc)
        
        assert "Invalid JSON-LD context" in str(exc_info.value)
    
    def test_propagates_validation_error(self):
        """Test that validation errors are properly propagated."""
        context_doc = {
            "@context": {
                "name": {}  # Missing @id
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            validate_context(context_doc)
        
        assert "Invalid JSON-LD context" in str(exc_info.value)
        assert "must have @id property" in str(exc_info.value)