"""
PyLD Local Validation Example

This example demonstrates PyLD validation using only local contexts
(no remote context loading) to show successful JSON-LD processing.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

# Add the src directory to the path so we can import pydantic_jsonld
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic_jsonld import JsonLDModel, Term

try:
    import pyld
    from pyld import jsonld
    PYLD_AVAILABLE = True
except ImportError:
    PYLD_AVAILABLE = False


class LocalPerson(JsonLDModel):
    """Person model using only local context (no remote imports)."""
    
    identifier: str = Term("https://schema.org/identifier", alias="@id", serialization_alias="@id", type_="@id")
    name: str = Term("https://schema.org/name")
    email: str = Term("https://schema.org/email", type_="http://www.w3.org/2001/XMLSchema#string")
    age: Optional[int] = Term("https://schema.org/age", type_="http://www.w3.org/2001/XMLSchema#integer")


# Configure without remote contexts
LocalPerson.configure_jsonld(
    base="https://example.org/people/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


def demonstrate_successful_validation():
    """Demonstrate successful PyLD validation and processing."""
    print("=" * 60)
    print("SUCCESSFUL PYLD VALIDATION (LOCAL CONTEXTS)")
    print("=" * 60)
    
    if not PYLD_AVAILABLE:
        print("❌ PyLD not available")
        return
    
    # Create person
    person = LocalPerson(
        identifier="person-123",
        name="Alice Johnson", 
        email="alice@example.com",
        age=30
    )
    
    # Get context (no remote imports)
    context = LocalPerson.export_context()
    
    print("\n1. Generated Local Context:")
    print(json.dumps(context, indent=2))
    
    # Validate context with PyLD
    print("\n2. Context Validation:")
    try:
        jsonld.expand(context)
        print("✅ Context is valid JSON-LD")
    except Exception as e:
        print(f"❌ Context validation failed: {e}")
        return
    
    # Get person data with aliases (so @id appears)
    person_data = person.model_dump(by_alias=True)
    print("\n3. Person Data:")
    print(json.dumps(person_data, indent=2))
    
    # Combine data with context
    doc_with_context = {**person_data, "@context": context["@context"]}
    
    # Expand document
    print("\n4. Expanded Document:")
    try:
        expanded = jsonld.expand(doc_with_context)
        print(json.dumps(expanded, indent=2))
    except Exception as e:
        print(f"❌ Expansion failed: {e}")
        return
    
    # Compact document
    print("\n5. Compacted Document:")
    try:
        compacted = jsonld.compact(expanded, context["@context"])
        print(json.dumps(compacted, indent=2))
    except Exception as e:
        print(f"❌ Compaction failed: {e}")
        return
    
    # Generate N-Quads
    print("\n6. N-Quads:")
    try:
        nquads = jsonld.to_rdf(doc_with_context, {'format': 'application/n-quads'})
        print(nquads)
    except Exception as e:
        print(f"❌ N-Quads generation failed: {e}")
        return
    
    print("✅ All PyLD operations successful!")


if __name__ == "__main__":
    demonstrate_successful_validation()