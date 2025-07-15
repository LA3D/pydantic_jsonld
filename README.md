# Pydantic JSON-LD

Generate JSON-LD contexts and SHACL shapes from Pydantic models while keeping your JSON clean for LLM function calling.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🤔 Why Pydantic JSON-LD?

Modern applications often need to work with both **LLMs** (which expect clean JSON) and **semantic web** technologies (which need JSON-LD contexts). This package lets you:

-  **Define once, use everywhere**: Single Pydantic models for both use cases
-  **Clean JSON for LLMs**: No JSON-LD pollution in your model JSON output
-  **Rich semantics**: Export separate JSON-LD contexts and SHACL shapes
-  **Cryptographic signatures**: W3C Data Integrity compliant Ed25519 signatures
-  **Standards compliant**: Generate valid JSON-LD and SHACL automatically
-  **Type safe**: Full type hints and validation throughout

## 🚀 Quick Start

### Installation

```bash
pip install pydantic-jsonld
```

### Basic Usage

```python
from pydantic_jsonld import JsonLDModel, Term

class Person(JsonLDModel):
    name: str = Term("schema:name")
    email: str = Term("schema:email", type_="xsd:string")
    age: int = Term("schema:age", type_="xsd:integer")

# Configure JSON-LD settings
Person.configure_jsonld(
    base="https://example.org/people/",
    remote_contexts=["https://schema.org/"],
    prefixes={"schema": "https://schema.org/", "xsd": "http://www.w3.org/2001/XMLSchema#"}
)

# Use normally for LLM function calling - clean JSON!
person = Person(name="Alice", email="alice@example.com", age=30)
print(person.model_dump_json())
# {"name": "Alice", "email": "alice@example.com", "age": 30}

# Export context separately for semantic web applications
context = Person.export_context()
print(context)
# {
#   "@context": [
#     "https://schema.org/",
#     {
#       "@base": "https://example.org/people/",
#       "schema": "https://schema.org/",
#       "xsd": "http://www.w3.org/2001/XMLSchema#",
#       "name": {"@id": "schema:name"},
#       "email": {"@id": "schema:email", "@type": "xsd:string"},
#       "age": {"@id": "schema:age", "@type": "xsd:integer"}
#     }
#   ]
# }

# Generate SHACL shapes for validation
shacl = Person.export_shacl()
# Full SHACL shape with constraints from Pydantic field definitions
```

### Cryptographic Signatures (W3C Data Integrity)

Sign your Pydantic models with Ed25519 cryptographic signatures for verification and provenance:

```python
from pydantic_jsonld import SignableJsonLDModel, generate_ed25519_keypair

class Person(SignableJsonLDModel):
    name: str = Term("schema:name")
    email: str = Term("schema:email")
    role: str = Term("schema:jobTitle")

Person.configure_jsonld(
    prefixes={"schema": "https://schema.org/"}
)

# Generate signing keys
private_key, public_key = generate_ed25519_keypair()

# Create and sign model
person = Person(name="Alice", email="alice@example.com", role="Researcher")
signed_doc = person.sign(private_key, verification_method="researcher-key-001")

# Verify signature
is_valid = Person.verify(signed_doc, public_key)
# True - signature is cryptographically valid

# Signed document includes W3C compliant proof:
# {
#   "@context": {...},
#   "name": "Alice",
#   "email": "alice@example.com", 
#   "role": "Researcher",
#   "proof": {
#     "type": "Ed25519Signature2020",
#     "created": "2025-07-15T14:30:00Z",
#     "verificationMethod": "researcher-key-001",
#     "proofPurpose": "assertionMethod",
#     "proofValue": "eyJ0eXAiOiJKV1Q..."
#   }
# }
```

### Named Graphs for Multiple Instances

Create JSON-LD graphs containing multiple model instances:

```python
# LLM extracts multiple people from text
people = [
    Person(name="Alice", email="alice@example.com", age=30),
    Person(name="Bob", email="bob@example.com", age=28)
]

# Export as named graph with metadata
graph = Person.export_graph(
    instances=people,
    graph_id="team-dataset",
    metadata={
        "created": "2024-07-15T10:30:00Z",
        "source": "llm-extraction",
        "confidence": 0.95
    }
)
# {
#   "@context": {...},
#   "@id": "team-dataset", 
#   "@type": "Dataset",
#   "@graph": [
#     {"@id": "person-1", "name": "Alice", ...},
#     {"@id": "person-2", "name": "Bob", ...}
#   ],
#   "created": "2024-07-15T10:30:00Z",
#   "source": "llm-extraction"
# }

# Mixed-model graphs
from pydantic_jsonld import export_mixed_graph
mixed_graph = export_mixed_graph(
    models=[person, product, sensor_reading],
    graph_id="iot-ecosystem",
    metadata={"domain": "IoT"}
)
```

## ⭐ Key Features

### Field Annotations with `Term()`

Annotate fields with JSON-LD metadata that doesn't interfere with normal Pydantic usage:

```python
class Product(JsonLDModel):
    # Basic term mapping
    name: str = Term("schema:name")
    
    # With type specification
    price: float = Term("schema:price", type_="xsd:decimal")
    
    # With containers for collections
    tags: List[str] = Term("schema:keywords", container="@set")
    categories: List[str] = Term("schema:category", container="@list")
    
    # With aliases (useful for @id)
    identifier: str = Term("schema:identifier", alias="@id", type_="@id")
    
    # With language specification
    description: str = Term("schema:description", language="en")
```

### Model Configuration

Configure JSON-LD settings at the class level:

```python
class Document(JsonLDModel):
    title: str = Term("schema:name")
    content: str = Term("schema:text")

# Set up namespaces and remote contexts
Document.configure_jsonld(
    base="https://docs.example.org/",
    vocab="https://example.org/vocab/", 
    remote_contexts=[
        "https://schema.org/",
        "https://w3id.org/security/v1"
    ],
    prefixes={
        "schema": "https://schema.org/",
        "sec": "https://w3id.org/security#",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)
```

### Multiple Export Formats

Export your models to different semantic formats:

```python
# JSON-LD Context
context = MyModel.export_context()

# SHACL Shapes (with constraints from Pydantic fields)
shapes = MyModel.export_shacl()

# Named Graphs (multiple instances with metadata)
graph = MyModel.export_graph(instances=[obj1, obj2], graph_id="dataset")

# Mixed-model graphs
mixed_graph = export_mixed_graph(models=[person, product], graph_id="mixed")

# Cryptographic signatures (W3C Data Integrity)
signed_doc = MyModel.sign(private_key, verification_method="my-key")

# Standard JSON Schema (clean, no JSON-LD artifacts)
schema = MyModel.model_json_schema()
```

## 📚 Advanced Examples

### Signed LLM Outputs for Agentic Workflows

```python
class LLMResponse(SignableJsonLDModel):
    query: str = Term("ex:query")
    response: str = Term("ex:response") 
    model: str = Term("ex:model")
    confidence: float = Term("ex:confidence", type_="xsd:decimal")
    timestamp: str = Term("schema:dateCreated", type_="xsd:dateTime")

LLMResponse.configure_jsonld(
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://ai.example.org/vocab/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

# Agent generates response
agent_private_key, agent_public_key = generate_ed25519_keypair()
llm_output = LLMResponse(
    query="What are the benefits of renewable energy?",
    response="Renewable energy reduces carbon emissions, provides energy independence...",
    model="claude-3-5-sonnet-20241022",
    confidence=0.92,
    timestamp="2025-07-15T14:30:00Z"
)

# Sign for verification in downstream systems
signed_output = llm_output.sign(
    agent_private_key, 
    verification_method="agent-001",
    proof_purpose="assertionMethod"
)

# Downstream system verifies authenticity
is_authentic = LLMResponse.verify(signed_output, agent_public_key)
# True - cryptographically verified LLM output

# Tamper detection
signed_output["confidence"] = 0.99  # Modify confidence
is_tampered = LLMResponse.verify(signed_output, agent_public_key)  
# False - tampering detected
```

### Scientific Research Paper

```python
class ResearchPaper(JsonLDModel):
    doi: str = Term("schema:doi", alias="@id", type_="@id")
    title: str = Term("schema:name")
    authors: List[str] = Term("schema:author", container="@list")
    keywords: List[str] = Term("schema:keywords", container="@set")
    citation_count: int = Term("ex:citationCount", type_="xsd:integer")
    is_open_access: bool = Term("ex:isOpenAccess", type_="xsd:boolean")

ResearchPaper.configure_jsonld(
    base="https://doi.org/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://example.org/research/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)
```

### IoT Sensor Data

```python
class SensorReading(JsonLDModel):
    reading_id: str = Term("ex:readingId", alias="@id", type_="@id")
    sensor_id: str = Term("sosa:madeBySensor", type_="@id")
    timestamp: str = Term("sosa:resultTime", type_="xsd:dateTime")
    value: float = Term("sosa:hasSimpleResult", type_="xsd:decimal")
    location_lat: float = Term("schema:latitude", type_="xsd:decimal")
    location_lon: float = Term("schema:longitude", type_="xsd:decimal")

SensorReading.configure_jsonld(
    base="https://sensors.example.org/readings/",
    prefixes={
        "sosa": "http://www.w3.org/ns/sosa/",
        "schema": "https://schema.org/",
        "ex": "https://sensors.example.org/vocab/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)
```

### E-commerce Product Catalog

```python
class Product(JsonLDModel):
    gtin: str = Term("schema:gtin", alias="@id", type_="@id")
    name: str = Term("schema:name")
    brand: str = Term("schema:brand")
    price: float = Term("schema:price", type_="xsd:decimal")
    currency: str = Term("schema:priceCurrency")
    availability: str = Term("schema:availability")
    categories: List[str] = Term("schema:category", container="@set")
    eco_friendly: bool = Term("ex:isEcoFriendly", type_="xsd:boolean")

Product.configure_jsonld(
    base="https://products.example.com/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://example.com/ecommerce/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)
```

## 🔧 Command Line Interface

Export contexts and SHACL shapes from your models using the CLI:

```bash
# Export JSON-LD contexts
pydantic-jsonld export-contexts myapp.models --output-dir ./contexts

# Export SHACL shapes  
pydantic-jsonld export-shacl myapp.models --output-dir ./shacl

# Inspect models and their annotations
pydantic-jsonld inspect myapp.models

# Export specific models only
pydantic-jsonld export-contexts myapp.models -m Person -m Product

# Generate named graphs from datasets
pydantic-jsonld export-graphs myapp.data --output-dir ./graphs

# Sign model instances (future feature)
pydantic-jsonld sign myapp.models --key-file ./private.key
```

## ✅ Testing and Validation

The package includes comprehensive validation to ensure your contexts are valid JSON-LD:

```python
from pydantic_jsonld.validation import validate_context

# Contexts are automatically validated on export
try:
    context = MyModel.export_context()
    print("✓ Context is valid JSON-LD")
except ValueError as e:
    print(f"✗ Invalid context: {e}")

# Manual validation
validate_context({"@context": {"name": {"@id": "schema:name"}}})
```

## 🔄 Integration with CI/CD

Automate context generation in your workflows:

```yaml
# .github/workflows/generate-contexts.yml
name: Generate JSON-LD Contexts
on: [push]
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pydantic-jsonld
      - name: Generate contexts
        run: |
          pydantic-jsonld export-contexts myapp.models --output-dir ./contexts
          pydantic-jsonld export-shacl myapp.models --output-dir ./shacl
      - name: Commit generated files
        run: |
          git add contexts/ shacl/
          git commit -m "Update generated contexts and shapes" || exit 0
          git push
```

## 🌟 Real-World Use Cases

- **🤖 LLM Applications**: Clean JSON for function calling while maintaining semantic meaning
- **🔐 Agentic Workflows**: Cryptographically signed LLM outputs with verification chains
- **🕸️ Knowledge Graphs**: Generate contexts for RDF/semantic web integration  
- **🔗 Data Integration**: Standardize data exchange between systems
- **📊 Dataset Publishing**: Named graphs for organizing multiple model instances with provenance metadata
- **⚖️ Compliance & Auditing**: Tamper-evident records with cryptographic integrity
- **🏥 Healthcare Systems**: Model clinical data with FHIR and HL7 compatibility
- **🛒 E-commerce**: Product catalogs with Schema.org markup
- **🔬 Research Data**: Scientific datasets with domain ontologies and cryptographic verification
- **📡 IoT Platforms**: Sensor data with SOSA/SSN ontologies in temporal graph structures
- **🎓 Educational Content**: Learning materials with educational ontologies
- **🏢 Enterprise Data**: Mixed-model graphs combining people, products, and processes

## 📖 Documentation

- **[API Reference](./docs/api.md)** - Complete API documentation
- **[Extended Examples](./examples.py)** - Real-world examples across domains
- **[Migration Guide](./docs/migration.md)** - Upgrading from other JSON-LD libraries
- **[Best Practices](./docs/best-practices.md)** - Patterns and recommendations

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/crcresearch/pydantic-jsonld
cd pydantic-jsonld
pip install -e ".[dev]"
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- **Pydantic** - For the excellent validation library this builds upon
- **JSON-LD Community** - For the standards and specifications
- **W3C** - For SHACL and semantic web standards

## 🚀 What's Next?

- [x] Named graphs for multiple model instances ✅
- [x] Mixed-model graphs with context merging ✅
- [x] PyLD integration for standards compliance ✅
- [x] Cryptographic signatures (W3C Data Integrity Ed25519) ✅
- [ ] BBS+ signatures for selective disclosure
- [ ] CLI signature commands for workflows
- [ ] Support for more SHACL constraint types
- [ ] Integration with popular graph databases
- [ ] Visual context/shape editors
- [ ] Performance optimizations for large schemas
- [ ] Additional export formats (TTL, N-Triples, etc.)
- [ ] Graph query helpers and SPARQL integration

---

**Made with ❤️ for the semantic web and AI communities**