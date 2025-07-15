"""
Tests for the models module.
"""

import pytest
from typing import List, Optional
from pydantic import ValidationError

from pydantic_jsonld import JsonLDModel, Term


class TestTerm:
    """Test the Term field helper function."""
    
    def test_term_basic(self):
        """Test basic Term usage."""
        field = Term("schema:name")
        assert field.metadata["__jsonld__"]["iri"] == "schema:name"
        assert field.metadata["__jsonld__"]["type"] is None
        assert field.metadata["__jsonld__"]["container"] is None
        assert field.metadata["__jsonld__"]["language"] is None
    
    def test_term_with_type(self):
        """Test Term with type annotation."""
        field = Term("schema:name", type_="xsd:string")
        assert field.metadata["__jsonld__"]["iri"] == "schema:name"
        assert field.metadata["__jsonld__"]["type"] == "xsd:string"
    
    def test_term_with_container(self):
        """Test Term with container annotation."""
        field = Term("schema:keywords", container="@set")
        assert field.metadata["__jsonld__"]["container"] == "@set"
    
    def test_term_with_language(self):
        """Test Term with language annotation."""
        field = Term("schema:name", language="en")
        assert field.metadata["__jsonld__"]["language"] == "en"
    
    def test_term_with_field_kwargs(self):
        """Test Term with additional field kwargs."""
        field = Term("schema:name", description="The name field", default="test")
        assert field.metadata["__jsonld__"]["iri"] == "schema:name"
        assert field.description == "The name field"
        assert field.default == "test"


class TestJsonLDModel:
    """Test the JsonLDModel base class."""
    
    def test_basic_model(self):
        """Test basic model creation and usage."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: int = Term("schema:age", type_="xsd:integer")
        
        # Test normal Pydantic usage
        instance = TestModel(name="Alice", age=30)
        assert instance.name == "Alice"
        assert instance.age == 30
        
        # Test JSON serialization is clean
        json_data = instance.model_dump()
        assert json_data == {"name": "Alice", "age": 30}
        
        # Test JSON schema is clean
        schema = TestModel.model_json_schema()
        assert "@context" not in schema
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
    
    def test_model_with_alias(self):
        """Test model with field aliases."""
        class TestModel(JsonLDModel):
            identifier: str = Term("schema:identifier", alias="@id", type_="@id")
            name: str = Term("schema:name")
        
        instance = TestModel(identifier="http://example.org/1", name="Alice")
        
        # Test with alias
        json_data = instance.model_dump(by_alias=True)
        assert json_data == {"@id": "http://example.org/1", "name": "Alice"}
        
        # Test without alias
        json_data = instance.model_dump(by_alias=False)
        assert json_data == {"identifier": "http://example.org/1", "name": "Alice"}
    
    def test_configure_jsonld(self):
        """Test JSON-LD configuration."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
        
        TestModel.configure_jsonld(
            base="https://example.org/",
            vocab="https://example.org/vocab/",
            remote_contexts=["https://schema.org/"],
            prefixes={"ex": "https://example.org/"}
        )
        
        assert TestModel._json_ld_base == "https://example.org/"
        assert TestModel._json_ld_vocab == "https://example.org/vocab/"
        assert TestModel._json_ld_remote_contexts == ["https://schema.org/"]
        assert TestModel._json_ld_prefixes == {"ex": "https://example.org/"}
    
    def test_export_context_basic(self):
        """Test basic context export."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: int = Term("schema:age", type_="xsd:integer")
        
        context = TestModel.export_context()
        
        assert "@context" in context
        ctx = context["@context"]
        
        assert "name" in ctx
        assert ctx["name"]["@id"] == "schema:name"
        assert "@type" not in ctx["name"]  # No type specified
        
        assert "age" in ctx
        assert ctx["age"]["@id"] == "schema:age"
        assert ctx["age"]["@type"] == "xsd:integer"
    
    def test_export_context_with_configuration(self):
        """Test context export with configuration."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
        
        TestModel.configure_jsonld(
            base="https://example.org/",
            vocab="https://example.org/vocab/",
            prefixes={"schema": "https://schema.org/"}
        )
        
        context = TestModel.export_context()
        ctx = context["@context"]
        
        assert ctx["@base"] == "https://example.org/"
        assert ctx["@vocab"] == "https://example.org/vocab/"
        assert ctx["schema"] == "https://schema.org/"
        assert ctx["name"]["@id"] == "schema:name"
    
    def test_export_context_with_remote_contexts(self):
        """Test context export with remote contexts."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
        
        TestModel.configure_jsonld(
            remote_contexts=["https://schema.org/", "https://example.org/context.jsonld"],
            prefixes={"ex": "https://example.org/"}
        )
        
        context = TestModel.export_context()
        ctx = context["@context"]
        
        # Should be an array with remote contexts first, then local
        assert isinstance(ctx, list)
        assert len(ctx) == 3
        assert ctx[0] == "https://schema.org/"
        assert ctx[1] == "https://example.org/context.jsonld"
        assert isinstance(ctx[2], dict)
        assert ctx[2]["ex"] == "https://example.org/"
        assert ctx[2]["name"]["@id"] == "schema:name"
    
    def test_export_context_with_aliases(self):
        """Test context export with field aliases."""
        class TestModel(JsonLDModel):
            identifier: str = Term("schema:identifier", alias="@id", type_="@id")
            name: str = Term("schema:name")
        
        context = TestModel.export_context()
        ctx = context["@context"]
        
        # Should use alias in context
        assert "@id" in ctx
        assert ctx["@id"]["@id"] == "schema:identifier"
        assert ctx["@id"]["@type"] == "@id"
        
        # Original field name should not be in context
        assert "identifier" not in ctx
    
    def test_export_context_with_containers(self):
        """Test context export with containers."""
        class TestModel(JsonLDModel):
            keywords: List[str] = Term("schema:keywords", container="@set")
            items: List[str] = Term("schema:itemList", container="@list")
        
        context = TestModel.export_context()
        ctx = context["@context"]
        
        assert ctx["keywords"]["@container"] == "@set"
        assert ctx["items"]["@container"] == "@list"
    
    def test_export_context_with_language(self):
        """Test context export with language."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name", language="en")
        
        context = TestModel.export_context()
        ctx = context["@context"]
        
        assert ctx["name"]["@language"] == "en"
    
    def test_export_context_skips_unannotated_fields(self):
        """Test that context export skips fields without JSON-LD annotations."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            internal_field: str = "default"  # No Term() annotation
        
        context = TestModel.export_context()
        ctx = context["@context"]
        
        assert "name" in ctx
        assert "internal_field" not in ctx
    
    def test_export_shacl(self):
        """Test SHACL export."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: int = Term("schema:age", type_="xsd:integer")
        
        shacl = TestModel.export_shacl()
        
        assert "@context" in shacl
        assert "@graph" in shacl
        
        # Check context has SHACL prefixes
        ctx = shacl["@context"]
        assert "sh" in ctx
        assert "xsd" in ctx
        
        # Check graph structure
        graph = shacl["@graph"]
        assert len(graph) >= 1  # At least the node shape
        
        # Find the node shape
        node_shape = None
        for item in graph:
            if item.get("@type") == "sh:NodeShape":
                node_shape = item
                break
        
        assert node_shape is not None
        assert "sh:targetClass" in node_shape
        assert "sh:property" in node_shape


class TestComplexModel:
    """Test complex model scenarios."""
    
    def test_inheritance(self):
        """Test model inheritance."""
        class BaseModel(JsonLDModel):
            name: str = Term("schema:name")
        
        class ExtendedModel(BaseModel):
            age: int = Term("schema:age", type_="xsd:integer")
        
        context = ExtendedModel.export_context()
        ctx = context["@context"]
        
        # Should include fields from both base and extended
        assert "name" in ctx
        assert "age" in ctx
    
    def test_optional_fields(self):
        """Test optional fields."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: Optional[int] = Term("schema:age", type_="xsd:integer")
        
        # Test with optional field
        instance = TestModel(name="Alice", age=30)
        assert instance.age == 30
        
        # Test without optional field
        instance = TestModel(name="Alice")
        assert instance.age is None
        
        # Context should still include optional fields
        context = TestModel.export_context()
        ctx = context["@context"]
        assert "age" in ctx
    
    def test_list_fields(self):
        """Test list fields."""
        class TestModel(JsonLDModel):
            keywords: List[str] = Term("schema:keywords", container="@set")
        
        instance = TestModel(keywords=["python", "json-ld"])
        assert instance.keywords == ["python", "json-ld"]
        
        # JSON should be clean
        json_data = instance.model_dump()
        assert json_data == {"keywords": ["python", "json-ld"]}
        
        # Context should include container
        context = TestModel.export_context()
        ctx = context["@context"]
        assert ctx["keywords"]["@container"] == "@set"