"""
Tests for named graph functionality.
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pydantic_jsonld import JsonLDModel, Term, export_mixed_graph


class PersonModel(JsonLDModel):
    """Person model for graph tests."""
    
    identifier: str = Term("schema:identifier", serialization_alias="@id", type_="@id")
    name: str = Term("schema:name")
    age: Optional[int] = Term("schema:age", type_="xsd:integer")
    skills: List[str] = Term("schema:knowsAbout", container="@set")


class ProductModel(JsonLDModel):
    """Product model for mixed graph tests."""
    
    gtin: str = Term("schema:gtin", serialization_alias="@id", type_="@id")
    name: str = Term("schema:name")
    price: float = Term("schema:price", type_="xsd:decimal")


# Configure test models
PersonModel.configure_jsonld(
    base="https://example.org/people/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

ProductModel.configure_jsonld(
    base="https://example.org/products/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


class TestSameModelGraphs:
    """Test graphs with instances of the same model."""
    
    def test_export_graph_basic(self):
        """Test basic graph export with multiple instances."""
        people = [
            PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"]),
            PersonModel(identifier="person-2", name="Bob", age=25, skills=["JavaScript", "React"])
        ]
        
        graph = PersonModel.export_graph(
            instances=people,
            graph_id="test-people-graph"
        )
        
        # Check structure
        assert "@context" in graph
        assert "@id" in graph
        assert "@type" in graph
        assert "@graph" in graph
        
        # Check values
        assert graph["@id"] == "test-people-graph"
        assert graph["@type"] == "Dataset"
        assert len(graph["@graph"]) == 2
        
        # Check individual items
        assert graph["@graph"][0]["@id"] == "person-1"
        assert graph["@graph"][0]["name"] == "Alice"
        assert graph["@graph"][1]["@id"] == "person-2"
        assert graph["@graph"][1]["name"] == "Bob"
    
    def test_export_graph_with_metadata(self):
        """Test graph export with metadata."""
        people = [
            PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        ]
        
        metadata = {
            "created": "2024-07-15T10:30:00Z",
            "source": "test-suite",
            "confidence": 0.95
        }
        
        graph = PersonModel.export_graph(
            instances=people,
            graph_id="test-with-metadata",
            metadata=metadata
        )
        
        # Check metadata is included
        assert graph["created"] == "2024-07-15T10:30:00Z"
        assert graph["source"] == "test-suite"
        assert graph["confidence"] == 0.95
        
        # Check core structure is preserved
        assert graph["@id"] == "test-with-metadata"
        assert "@graph" in graph
    
    def test_export_graph_auto_id_generation(self):
        """Test automatic graph ID generation."""
        people = [
            PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        ]
        
        graph = PersonModel.export_graph(instances=people)
        
        # Should generate an ID with timestamp
        assert graph["@id"].startswith("PersonModel-graph-")
        assert len(graph["@id"]) > len("PersonModel-graph-")
    
    def test_export_graph_auto_instance_ids(self):
        """Test automatic instance ID generation."""
        # Create a model without serialization_alias for testing auto-generation
        class PersonWithoutId(JsonLDModel):
            name: str = Term("schema:name")
            age: Optional[int] = Term("schema:age", type_="xsd:integer")
        
        PersonWithoutId.configure_jsonld(
            base="https://example.org/people/",
            prefixes={"schema": "https://schema.org/", "xsd": "http://www.w3.org/2001/XMLSchema#"}
        )
        
        people = [
            PersonWithoutId(name="Alice", age=30),
            PersonWithoutId(name="Bob", age=25)
        ]
        
        graph = PersonWithoutId.export_graph(
            instances=people,
            graph_id="test-auto-ids",
            auto_id_pattern="person-{index}"
        )
        
        # Check auto-generated IDs
        assert graph["@graph"][0]["@id"] == "person-1"
        assert graph["@graph"][1]["@id"] == "person-2"
    
    def test_export_graph_empty_instances(self):
        """Test error handling for empty instances list."""
        with pytest.raises(ValueError, match="Cannot create graph from empty instances list"):
            PersonModel.export_graph(instances=[])
    
    def test_export_graph_wrong_type_instances(self):
        """Test error handling for instances of wrong type."""
        product = ProductModel(gtin="123", name="Widget", price=19.99)
        
        with pytest.raises(ValueError, match="All instances must be of type PersonModel"):
            PersonModel.export_graph(instances=[product])
    
    def test_export_graph_context_structure(self):
        """Test that graph context matches class context."""
        people = [
            PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        ]
        
        graph = PersonModel.export_graph(instances=people, graph_id="test-context")
        class_context = PersonModel.export_context()
        
        # Context should be the same
        assert graph["@context"] == class_context["@context"]


class TestMixedModelGraphs:
    """Test graphs with instances of different models."""
    
    def test_export_mixed_graph_basic(self):
        """Test basic mixed model graph export."""
        person = PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        product = ProductModel(gtin="123456789012", name="Laptop", price=999.99)
        
        graph = export_mixed_graph(
            models=[person, product],
            graph_id="mixed-test-graph"
        )
        
        # Check structure
        assert "@context" in graph
        assert "@id" in graph
        assert "@type" in graph
        assert "@graph" in graph
        
        # Check values
        assert graph["@id"] == "mixed-test-graph"
        assert graph["@type"] == "Dataset"
        assert len(graph["@graph"]) == 2
        
        # Check items are present
        graph_items = graph["@graph"]
        person_item = next(item for item in graph_items if item.get("@id") == "person-1")
        product_item = next(item for item in graph_items if item.get("@id") == "123456789012")
        
        assert person_item["name"] == "Alice"
        assert product_item["price"] == 999.99
    
    def test_export_mixed_graph_with_metadata(self):
        """Test mixed graph with metadata."""
        person = PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        
        metadata = {
            "created": "2024-07-15",
            "source": "mixed-test"
        }
        
        graph = export_mixed_graph(
            models=[person],
            graph_id="mixed-with-metadata",
            metadata=metadata
        )
        
        assert graph["created"] == "2024-07-15"
        assert graph["source"] == "mixed-test"
    
    def test_export_mixed_graph_auto_id(self):
        """Test mixed graph auto ID generation."""
        person = PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        
        graph = export_mixed_graph(models=[person])
        
        # Should generate an ID with timestamp
        assert graph["@id"].startswith("mixed-graph-")
    
    def test_export_mixed_graph_context_merging(self):
        """Test context merging for mixed models."""
        person = PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        product = ProductModel(gtin="123456789012", name="Laptop", price=999.99)
        
        graph = export_mixed_graph(models=[person, product], graph_id="context-merge-test")
        
        context = graph["@context"]
        
        # Should contain terms from both models
        if isinstance(context, dict):
            # Single context object
            assert "name" in context  # Common to both
            assert "age" in context   # From person
            assert "price" in context # From product
        elif isinstance(context, list):
            # Array context - check the local context
            local_context = context[-1] if isinstance(context[-1], dict) else {}
            assert "name" in local_context
            # Age and price should be present (might be prefixed if conflicts)
            assert any("age" in key for key in local_context.keys())
            assert any("price" in key for key in local_context.keys())
    
    def test_export_mixed_graph_empty_models(self):
        """Test error handling for empty models list."""
        with pytest.raises(ValueError, match="Cannot create graph from empty models list"):
            export_mixed_graph(models=[])


class TestGraphValidation:
    """Test graph validation and edge cases."""
    
    def test_graph_json_ld_compliance(self):
        """Test that generated graphs are valid JSON-LD."""
        people = [
            PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"]),
            PersonModel(identifier="person-2", name="Bob", age=25, skills=["JavaScript"])
        ]
        
        graph = PersonModel.export_graph(
            instances=people,
            graph_id="validation-test"
        )
        
        # Basic JSON-LD structure requirements
        assert "@context" in graph
        assert "@graph" in graph
        
        # Each graph item should be a dict
        for item in graph["@graph"]:
            assert isinstance(item, dict)
            # Items with @id should have proper structure
            if "@id" in item:
                assert isinstance(item["@id"], str)
    
    def test_graph_serialization(self):
        """Test that graphs can be serialized to JSON."""
        import json
        
        people = [
            PersonModel(identifier="person-1", name="Alice", age=30, skills=["Python"])
        ]
        
        graph = PersonModel.export_graph(instances=people, graph_id="serialization-test")
        
        # Should be serializable
        json_str = json.dumps(graph)
        assert isinstance(json_str, str)
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["@id"] == "serialization-test"
    
    def test_large_graph_performance(self):
        """Test performance with larger graphs."""
        # Create 100 people
        people = [
            PersonModel(
                identifier=f"person-{i}",
                name=f"Person {i}",
                age=20 + (i % 50),
                skills=["Python", "JavaScript"][:i % 2 + 1]
            )
            for i in range(100)
        ]
        
        # Should complete without issues
        graph = PersonModel.export_graph(instances=people, graph_id="large-graph-test")
        
        assert len(graph["@graph"]) == 100
        assert graph["@id"] == "large-graph-test"