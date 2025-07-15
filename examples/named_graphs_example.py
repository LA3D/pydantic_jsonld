"""
Named Graphs Example for Pydantic JSON-LD

This example demonstrates how to create named JSON-LD graphs from Pydantic models,
including the LLM function calling → JSON-LD workflow.

Named graphs enable:
- Multiple models in one JSON-LD document  
- Graph-level metadata (provenance, timestamps, source attribution)
- Dataset organization for SPARQL querying
- Federated data with clear boundaries
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add the src directory to the path so we can import pydantic_jsonld
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic_jsonld import JsonLDModel, Term, export_mixed_graph


# =============================================================================
# Example Models for Different Scenarios
# =============================================================================

class Person(JsonLDModel):
    """Person model suitable for LLM function calling and semantic web."""
    
    identifier: str = Term("schema:identifier", serialization_alias="@id", type_="@id")
    name: str = Term("schema:name")
    email: str = Term("schema:email", type_="xsd:string")
    age: Optional[int] = Term("schema:age", type_="xsd:integer")
    skills: List[str] = Term("schema:knowsAbout", container="@set")


class Product(JsonLDModel):
    """Product model for e-commerce scenarios."""
    
    gtin: str = Term("schema:gtin", serialization_alias="@id", type_="@id")
    name: str = Term("schema:name")
    description: str = Term("schema:description")
    price: float = Term("schema:price", type_="xsd:decimal")
    category: str = Term("schema:category")
    in_stock: bool = Term("schema:availability", type_="xsd:boolean")


class SensorReading(JsonLDModel):
    """IoT sensor reading for temporal data scenarios."""
    
    reading_id: str = Term("ex:readingId", serialization_alias="@id", type_="@id")
    sensor_id: str = Term("sosa:madeBySensor", type_="@id")
    timestamp: str = Term("sosa:resultTime", type_="xsd:dateTime")
    value: float = Term("sosa:hasSimpleResult", type_="xsd:decimal")
    unit: str = Term("ex:unit")


# Configure models
Person.configure_jsonld(
    base="https://example.org/people/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

Product.configure_jsonld(
    base="https://example.org/products/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

SensorReading.configure_jsonld(
    base="https://iot.example.org/readings/",
    prefixes={
        "sosa": "http://www.w3.org/ns/sosa/",
        "ex": "https://iot.example.org/vocab/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 1: LLM Function Calling → Named Graph Workflow
# =============================================================================

def demonstrate_llm_to_graph_workflow():
    """Demonstrate the complete LLM function calling to JSON-LD graph workflow."""
    print("=" * 70)
    print("LLM FUNCTION CALLING → JSON-LD GRAPH WORKFLOW")
    print("=" * 70)
    
    # Step 1: Simulate LLM function calling
    print("\n1. LLM Function Schema (Clean JSON for LLM):")
    schema = Person.model_json_schema()
    print(json.dumps(schema, indent=2)[:400] + "...")
    
    # Step 2: Simulate LLM response (extracted people)
    print("\n2. Simulated LLM Response (Multiple People Extracted):")
    llm_response = [
        {"identifier": "person-001", "name": "Alice Johnson", "email": "alice@example.com", "age": 30, "skills": ["Python", "Machine Learning"]},
        {"identifier": "person-002", "name": "Bob Smith", "email": "bob@example.com", "age": 28, "skills": ["JavaScript", "React"]},
        {"identifier": "person-003", "name": "Carol Davis", "email": "carol@example.com", "age": 35, "skills": ["Data Science", "SQL"]}
    ]
    
    for i, person_data in enumerate(llm_response, 1):
        print(f"  Person {i}: {person_data}")
    
    # Step 3: Validate with Pydantic
    print("\n3. Pydantic Validation:")
    people = []
    for person_data in llm_response:
        person = Person(**person_data)
        people.append(person)
        print(f"  ✓ Validated: {person.name}")
    
    # Step 4: Individual model usage (still works normally)
    print("\n4. Individual Model Usage (Clean JSON):")
    print(f"  Alice as JSON: {people[0].model_dump()}")
    
    # Step 5: Export as Named Graph with metadata
    print("\n5. Export as Named JSON-LD Graph:")
    metadata = {
        "created": datetime.now().isoformat(),
        "source": "llm-extraction",
        "model": "gpt-4",
        "confidence": 0.95,
        "extractedFrom": "company-directory-text"
    }
    
    graph = Person.export_graph(
        instances=people,
        graph_id="https://example.org/graphs/llm-extracted-people-2024",
        metadata=metadata
    )
    
    print(json.dumps(graph, indent=2))
    
    print("\n6. Key Benefits:")
    print("  ✓ Same model works for LLM function calling AND semantic web")
    print("  ✓ Clean JSON schema for LLMs (no JSON-LD pollution)")
    print("  ✓ Rich semantic context for knowledge graphs")
    print("  ✓ Graph-level provenance and metadata")
    print("  ✓ Standards-compliant JSON-LD output")


# =============================================================================
# Example 2: Same-Model Graph with Auto-Generated IDs
# =============================================================================

def demonstrate_same_model_graph():
    """Demonstrate creating graphs from multiple instances of the same model."""
    print("\n" + "=" * 70)
    print("SAME-MODEL GRAPH WITH AUTO-GENERATED IDS")
    print("=" * 70)
    
    # Create products without explicit IDs
    products = [
        Product(gtin="temp-1", name="Laptop", description="Gaming laptop", price=1299.99, category="Electronics", in_stock=True),
        Product(gtin="temp-2", name="Mouse", description="Wireless mouse", price=29.99, category="Electronics", in_stock=True),
        Product(gtin="temp-3", name="Keyboard", description="Mechanical keyboard", price=149.99, category="Electronics", in_stock=False)
    ]
    
    print("1. Products Created:")
    for product in products:
        print(f"  - {product.name}: ${product.price}")
    
    # Export with auto-generated IDs
    print("\n2. Export with Auto-Generated IDs:")
    graph = Product.export_graph(
        instances=products,
        graph_id="product-catalog-2024",
        auto_id_pattern="product-{index}",
        metadata={
            "catalog": "electronics",
            "lastUpdated": "2024-07-15",
            "currency": "USD"
        }
    )
    
    print(json.dumps(graph, indent=2))


# =============================================================================
# Example 3: Mixed-Model Graph
# =============================================================================

def demonstrate_mixed_model_graph():
    """Demonstrate creating graphs with multiple model types."""
    print("\n" + "=" * 70)
    print("MIXED-MODEL GRAPH (MULTIPLE MODEL TYPES)")
    print("=" * 70)
    
    # Create instances of different models
    person = Person(
        identifier="alice-001",
        name="Alice Johnson", 
        email="alice@iot-company.com",
        age=30,
        skills=["IoT", "Python"]
    )
    
    product = Product(
        gtin="987654321",
        name="Temperature Sensor",
        description="High-precision temperature sensor", 
        price=89.99,
        category="IoT Devices",
        in_stock=True
    )
    
    sensor_reading = SensorReading(
        reading_id="reading-20240715-001",
        sensor_id="sensor-temp-01",
        timestamp="2024-07-15T14:30:00Z",
        value=23.5,
        unit="celsius"
    )
    
    print("1. Mixed Model Instances:")
    print(f"  Person: {person.name}")
    print(f"  Product: {product.name}")
    print(f"  Sensor Reading: {sensor_reading.value}{sensor_reading.unit}")
    
    # Export as mixed graph
    print("\n2. Export as Mixed Graph:")
    mixed_graph = export_mixed_graph(
        models=[person, product, sensor_reading],
        graph_id="iot-ecosystem-demo",
        metadata={
            "description": "Demonstration of IoT ecosystem with person, product, and sensor data",
            "created": "2024-07-15T14:30:00Z",
            "domain": "IoT"
        }
    )
    
    print(json.dumps(mixed_graph, indent=2))


# =============================================================================
# Example 4: Large Dataset Graph
# =============================================================================

def demonstrate_large_dataset_graph():
    """Demonstrate creating graphs with larger datasets."""
    print("\n" + "=" * 70)
    print("LARGE DATASET GRAPH (PERFORMANCE DEMO)")
    print("=" * 70)
    
    # Generate 50 sensor readings
    import random
    readings = []
    base_time = datetime.fromisoformat("2024-07-15T00:00:00")
    
    for i in range(50):
        minutes_elapsed = i * 30
        hour = (minutes_elapsed // 60) % 24  # Wrap around at 24 hours
        minute = minutes_elapsed % 60
        timestamp = base_time.replace(minute=minute, hour=hour)
        readings.append(SensorReading(
            reading_id=f"reading-{i+1:03d}",
            sensor_id=f"sensor-{(i % 5) + 1:02d}",
            timestamp=timestamp.isoformat() + "Z",
            value=round(20 + random.uniform(-5, 10), 2),
            unit="celsius"
        ))
    
    print(f"1. Generated {len(readings)} sensor readings")
    print(f"   First reading: {readings[0].timestamp}, {readings[0].value}°C")
    print(f"   Last reading: {readings[-1].timestamp}, {readings[-1].value}°C")
    
    # Export as large graph
    print("\n2. Export Large Graph:")
    large_graph = SensorReading.export_graph(
        instances=readings,
        graph_id="sensor-dataset-24h",
        metadata={
            "description": "24-hour temperature sensor dataset",
            "measurementPeriod": "24 hours",
            "sensorCount": 5,
            "readingCount": len(readings),
            "dataType": "temperature",
            "units": "celsius"
        }
    )
    
    # Show summary instead of full graph
    print(f"   Graph ID: {large_graph['@id']}")
    print(f"   Context type: {type(large_graph['@context'])}")
    print(f"   Graph items: {len(large_graph['@graph'])}")
    print(f"   Metadata keys: {[k for k in large_graph.keys() if not k.startswith('@')]}")
    print(f"   Sample reading: {large_graph['@graph'][0]}")


# =============================================================================
# Example 5: Graph Composition and Metadata Patterns
# =============================================================================

def demonstrate_graph_metadata_patterns():
    """Demonstrate different metadata patterns for graphs."""
    print("\n" + "=" * 70)
    print("GRAPH METADATA PATTERNS")
    print("=" * 70)
    
    people = [
        Person(identifier="emp-001", name="Alice", email="alice@company.com", age=30, skills=["Python"]),
        Person(identifier="emp-002", name="Bob", email="bob@company.com", age=28, skills=["JavaScript"])
    ]
    
    # Pattern 1: Provenance metadata
    print("1. Provenance Metadata Pattern:")
    provenance_graph = Person.export_graph(
        instances=people,
        graph_id="employee-data-extract-v1",
        metadata={
            "prov:wasGeneratedBy": "hr-system-export",
            "prov:generatedAtTime": datetime.now().isoformat(),
            "prov:wasDerivedFrom": "hr-database-2024",
            "prov:wasAttributedTo": "data-pipeline-v2.1",
            "dcterms:license": "https://creativecommons.org/licenses/by/4.0/",
            "dcterms:rights": "Internal use only"
        }
    )
    print(f"   Graph with provenance: {list(provenance_graph.keys())}")
    
    # Pattern 2: Quality and confidence metadata
    print("\n2. Quality Metadata Pattern:")
    quality_graph = Person.export_graph(
        instances=people,
        graph_id="validated-employee-data",
        metadata={
            "qualityScore": 0.95,
            "validationStatus": "passed",
            "completenessScore": 0.88,
            "validatedBy": "data-quality-service",
            "validationRules": ["email-format", "age-range", "required-fields"],
            "lastValidated": datetime.now().isoformat()
        }
    )
    print(f"   Graph with quality metrics: {list(quality_graph.keys())}")
    
    # Pattern 3: Dataset description metadata
    print("\n3. Dataset Description Pattern:")
    dataset_graph = Person.export_graph(
        instances=people,
        graph_id="employee-skills-dataset",
        metadata={
            "dcterms:title": "Employee Skills Dataset",
            "dcterms:description": "Curated dataset of employee skills and contact information",
            "dcterms:creator": "HR Analytics Team",
            "dcterms:created": "2024-07-15",
            "dcterms:format": "application/ld+json",
            "dcterms:language": "en",
            "dcat:keyword": ["employees", "skills", "hr"],
            "dcat:theme": "human-resources",
            "schema:version": "1.0.0"
        }
    )
    print(f"   Graph with dataset description: {list(dataset_graph.keys())}")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Run all named graph demonstrations."""
    print("Pydantic JSON-LD Named Graphs Examples")
    print("=" * 70)
    print("Demonstrating named graph creation for various scenarios")
    
    # Run all demonstrations
    demonstrate_llm_to_graph_workflow()
    demonstrate_same_model_graph()
    demonstrate_mixed_model_graph()
    demonstrate_large_dataset_graph()
    demonstrate_graph_metadata_patterns()
    
    print("\n" + "=" * 70)
    print("SUMMARY OF NAMED GRAPH CAPABILITIES")
    print("=" * 70)
    print("✅ Named graphs enable:")
    print("  • LLM function calling → JSON-LD workflow")
    print("  • Multiple model instances in one document")
    print("  • Mixed model types with merged contexts")
    print("  • Graph-level metadata and provenance")
    print("  • Dataset organization for SPARQL queries")
    print("  • Performance with large datasets")
    print("  • Standards-compliant JSON-LD output")
    print("\n✅ Key benefits:")
    print("  • Same models work for LLMs AND semantic web")
    print("  • Clean separation of concerns")
    print("  • Rich metadata support")
    print("  • Scalable to production datasets")
    print("  • Maintains Pydantic developer experience")
    print("\n🚀 Ready for production use cases!")


if __name__ == "__main__":
    main()