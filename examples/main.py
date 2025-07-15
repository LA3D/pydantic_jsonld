"""
Example usage of pydantic-jsonld package.

This demonstrates how to use the package to create Pydantic models with JSON-LD
annotations and export contexts and SHACL shapes.
"""

from typing import List, Optional
from pydantic_jsonld import JsonLDModel, Term


# Example 1: Basic document model
class Document(JsonLDModel):
    """A basic document model with JSON-LD annotations."""
    
    # Use alias for JSON-LD @id
    identifier: str = Term("schema:identifier", alias="@id", type_="@id")
    
    # Basic text fields
    title: str = Term("schema:name")
    content: str = Term("schema:text")
    
    # Optional fields
    description: Optional[str] = Term("schema:description")
    
    # List fields with containers
    keywords: List[str] = Term("schema:keywords", container="@set")
    authors: List[str] = Term("schema:author", container="@list")


# Configure JSON-LD settings
Document.configure_jsonld(
    base="https://example.org/documents/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://example.org/vocab/"
    }
)


# Example 2: More complex model with custom vocabulary
class Person(JsonLDModel):
    """A person model using custom vocabulary."""
    
    identifier: str = Term("ex:personId", alias="@id", type_="@id")
    name: str = Term("schema:name")
    email: str = Term("schema:email", type_="xsd:string")
    age: Optional[int] = Term("schema:age", type_="xsd:integer")
    
    # Custom properties
    security_clearance: Optional[str] = Term("ex:securityClearance")
    department: Optional[str] = Term("ex:department")
    
    # Relationships
    manager: Optional[str] = Term("ex:reportsTo", type_="@id", default=None)
    direct_reports: List[str] = Term("ex:manages", container="@set", type_="@id", default=[])


# Configure Person model
Person.configure_jsonld(
    base="https://company.example.org/people/",
    vocab="https://company.example.org/vocab/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://company.example.org/vocab/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# Example 3: Model inheritance
class PublishedDocument(Document):
    """A published document that extends the base Document model."""
    
    publication_date: str = Term("schema:datePublished", type_="xsd:date")
    isbn: Optional[str] = Term("schema:isbn")
    publisher: Optional[str] = Term("schema:publisher")
    
    # Override keywords to use different container
    keywords: List[str] = Term("schema:keywords", container="@list")


def main():
    """Demonstrate the package functionality."""
    print("Pydantic JSON-LD Example")
    print("=" * 40)
    
    # Create instances - clean JSON for LLM function calling
    print("\n1. Creating model instances (clean JSON)")
    print("-" * 40)
    
    doc = Document(
        identifier="doc-1",
        title="Introduction to JSON-LD",
        content="JSON-LD is a method of encoding Linked Data using JSON.",
        description="A comprehensive guide to JSON-LD",
        keywords=["json-ld", "linked-data", "semantic-web"],
        authors=["Alice Smith", "Bob Jones"]
    )
    
    person = Person(
        identifier="person-123",
        name="Alice Smith",
        email="alice@example.com",
        age=30,
        security_clearance="SECRET",
        department="Engineering"
    )
    
    # Show clean JSON output
    print("Document JSON:")
    print(doc.model_dump_json(indent=2))
    
    print("\nPerson JSON:")
    print(person.model_dump_json(indent=2))
    
    # Show clean JSON schema
    print("\n2. JSON Schema (clean for LLM function calling)")
    print("-" * 40)
    
    print("Document Schema:")
    import json
    print(json.dumps(Document.model_json_schema(), indent=2))
    
    # Export JSON-LD contexts
    print("\n3. JSON-LD Context Export")
    print("-" * 40)
    
    print("Document Context:")
    doc_context = Document.export_context()
    print(json.dumps(doc_context, indent=2))
    
    print("\nPerson Context:")
    person_context = Person.export_context()
    print(json.dumps(person_context, indent=2))
    
    # Export SHACL shapes
    print("\n4. SHACL Shape Export")
    print("-" * 40)
    
    print("Document SHACL Shape:")
    doc_shacl = Document.export_shacl()
    print(json.dumps(doc_shacl, indent=2))
    
    print("\nPerson SHACL Shape:")
    person_shacl = Person.export_shacl()
    print(json.dumps(person_shacl, indent=2))
    
    # Demonstrate inheritance
    print("\n5. Model Inheritance")
    print("-" * 40)
    
    pub_doc = PublishedDocument(
        identifier="pub-doc-1",
        title="Advanced JSON-LD Techniques",
        content="This document covers advanced JSON-LD features.",
        description="An advanced guide to JSON-LD techniques",
        keywords=["json-ld", "advanced", "techniques"],
        authors=["Charlie Brown"],
        publication_date="2024-01-15",
        isbn="978-0123456789",
        publisher="Tech Books Inc."
    )
    
    print("Published Document JSON:")
    print(pub_doc.model_dump_json(indent=2))
    
    print("\nPublished Document Context:")
    pub_doc_context = PublishedDocument.export_context()
    print(json.dumps(pub_doc_context, indent=2))
    
    print("\n6. Validation Example")
    print("-" * 40)
    
    try:
        # This will work
        valid_doc = Document(
            identifier="valid-doc",
            title="Valid Document",
            content="This is a valid document.",
            keywords=["valid"],
            authors=["Author"]
        )
        print("✓ Valid document created successfully")
        
        # This will fail validation
        invalid_doc = Document(
            identifier="invalid-doc",
            # Missing required fields: title, content, keywords, authors
        )
        print("✗ This should not print")
        
    except Exception as e:
        print(f"✓ Validation error caught: {e}")
    
    print("\n7. Usage Summary")
    print("-" * 40)
    print("• Use models normally for LLM function calling - clean JSON")
    print("• Export contexts separately for semantic web applications")
    print("• Generate SHACL shapes for validation")
    print("• Single source of truth for both JSON and JSON-LD")


if __name__ == "__main__":
    main()