# Pydantic JSON-LD Examples

This directory contains comprehensive examples demonstrating how to use pydantic-jsonld for various real-world scenarios.

## Examples Overview

### Core Examples

- **[main.py](./main.py)** - Basic usage patterns and fundamental concepts
- **[examples.py](./examples.py)** - Extended real-world examples across multiple domains

### Advanced Examples

- **[pyld_validation_example.py](./pyld_validation_example.py)** - JSON-LD validation using PyLD processor
- **[named_graphs_example.py](./named_graphs_example.py)** - Named graphs and LLM → JSON-LD workflows

## Running Examples

All examples can be run directly from this directory:

```bash
# Basic usage examples
uv run python main.py

# Extended domain examples  
uv run python examples.py

# PyLD validation and processing
uv run python pyld_validation_example.py

# Named graphs and LLM workflows
uv run python named_graphs_example.py
```

## Example Categories

### 1. Basic Usage (`main.py`)
- Simple document model
- Person model with custom vocabulary
- Model inheritance
- Field validation
- Context export
- SHACL generation

### 2. Domain-Specific Models (`examples.py`)
- **Scientific Research**: Research papers with citations and metadata
- **E-commerce**: Product catalogs with variants and specifications
- **Healthcare**: Patient records with privacy considerations
- **Finance**: Transaction records with compliance tracking
- **IoT**: Sensor readings with temporal/spatial context
- **Education**: Course models with prerequisites and outcomes
- **Supply Chain**: Item tracking with provenance

### 3. JSON-LD Processing (`pyld_validation_example.py`)
- Context validation with PyLD
- Document expansion and compaction
- N-Quads generation for RDF
- Round-trip testing
- Context merging
- Error handling and edge cases

### 4. Named Graphs (`named_graphs_example.py`)
- LLM function calling → JSON-LD graph workflow
- Same-model graphs with auto-generated IDs
- Mixed-model graphs with context merging
- Large dataset performance demonstration
- Graph metadata patterns (provenance, quality, dataset description)
- Production-ready examples

## Key Concepts Demonstrated

### Clean JSON for LLMs
```python
# Standard Pydantic usage - clean JSON output
person = Person(name="Alice", age=30)
print(person.model_dump_json())
# {"name": "Alice", "age": 30}
```

### Semantic Web Integration
```python
# Separate context export for JSON-LD
context = Person.export_context()
# Full JSON-LD context with vocabularies and mappings
```

### Validation and Processing
```python
# PyLD validation of generated contexts
validate_context_with_pyld(context)
# Standards-compliant JSON-LD processing
```

## Prerequisites

Basic examples require only pydantic-jsonld:
```bash
uv add pydantic-jsonld
```

PyLD examples require the PyLD processor:
```bash
uv add pyld
```

## Example Output

Each example produces:
1. **Clean JSON** - For LLM function calling
2. **JSON Schema** - Standard validation schema
3. **JSON-LD Context** - Semantic web context
4. **SHACL Shapes** - RDF validation shapes
5. **N-Quads** - RDF triple representation (PyLD examples)

## Best Practices Shown

- **Vocabulary Selection**: Using established vocabularies (Schema.org, SOSA, etc.)
- **Term Mapping**: Proper IRI mapping and type specification
- **Container Usage**: @set vs @list for collections
- **Alias Configuration**: Using @id aliases appropriately
- **Remote Contexts**: Importing standard contexts
- **Prefix Management**: Organizing namespace prefixes
- **Validation Strategy**: Multiple validation layers
- **Error Handling**: Graceful failure modes

## Next Steps

After exploring these examples:

1. **Adapt models** to your domain requirements
2. **Configure vocabularies** for your use case
3. **Integrate validation** into your workflow
4. **Export artifacts** for semantic web applications
5. **Test with PyLD** for standards compliance

## Contributing Examples

To add new examples:

1. Create focused, well-documented examples
2. Include both basic and advanced usage
3. Demonstrate real-world scenarios
4. Add validation and error handling
5. Update this README with new examples

## Support

For questions about examples:
- Check existing example code and comments
- Review the main [README](../README.md)
- Open an issue for specific use cases