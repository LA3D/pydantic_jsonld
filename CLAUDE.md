# Pydantic JSON-LD Context Generator

## Project Overview

This project creates an installable Python package that enables developers to generate JSON-LD contexts and SHACL shapes from Pydantic models. The package implements the "JSON-LD-first Pydantic" workflow described in `pydantic-context.md`.

## Goals

1. **Single Source of Truth**: Pydantic models become the authoritative source for both data validation and semantic web artifacts
2. **Clean JSON Schema**: Maintain standard JSON and JSON Schema compatibility for LLM function calling without JSON-LD pollution
3. **Separate Context Export**: Generate JSON-LD contexts as separate artifacts, not embedded in model JSON
4. **Developer Experience**: Maintain familiar Pydantic patterns while adding JSON-LD capabilities
5. **Standards Compliance**: Generate valid JSON-LD contexts and SHACL shapes automatically
6. **CI/CD Integration**: Enable automated artifact generation in continuous integration workflows

## Package Architecture

### Core Components

1. **JsonLDModel Base Class**: Extends `BaseModel` with JSON-LD export capabilities
2. **Term Field Helper**: Annotates fields with IRI and type information
3. **Context Validation**: Ensures generated contexts are valid JSON-LD
4. **Export Methods**: Generate contexts and SHACL shapes from model metadata
5. **CLI Tools**: Command-line interface for batch generation

### Key Features

- **Non-invasive Design**: JSON-LD metadata stored in field metadata, invisible to normal JSON serialization
- **Clean Function Calling**: Model.model_json_schema() produces standard JSON Schema without JSON-LD artifacts
- **Separate Context Export**: Use `Model.export_context()` to generate standalone JSON-LD context files
- **Field-level Annotations**: Use `Term()` helper to annotate fields with IRI and type information
- **Automatic Context Generation**: Generate proper @context structure with remote imports and prefixes
- **SHACL Shape Generation**: Derive SHACL shapes from Pydantic field constraints
- **Validation First**: All generated artifacts validated before export
- **CLI Integration**: Command-line tools for batch processing and CI workflows

## Implementation Notes

- **No Plugin System**: Avoids experimental Pydantic plugin API in favor of stable base class approach
- **Metadata Storage**: Uses Pydantic field metadata to store JSON-LD annotations (invisible to JSON schema)
- **Dual-Purpose Models**: Same model works for both LLM function calling and semantic web publishing
- **Context Separation**: JSON-LD contexts generated as separate files, never embedded in model JSON
- **Validation First**: All generated artifacts are validated before export
- **Extensible Design**: Modular architecture allows for additional export formats

## Usage Examples

```python
# Define model with JSON-LD annotations
class Document(JsonLDModel):
    title: str = Term("schema:name")
    content: str = Term("schema:text")
    
# Use normally for LLM function calling
doc = Document(title="Hello", content="World")
doc.model_dump()  # {"title": "Hello", "content": "World"}
doc.model_json_schema()  # Clean JSON Schema, no JSON-LD artifacts

# Export context separately for semantic web
context = Document.export_context()
# {"@context": {"title": {"@id": "schema:name"}, ...}}
```

## Development Commands

- `python -m pytest`: Run test suite
- `python -m pydantic_jsonld.cli`: CLI interface for context generation
- `pip install -e .`: Install package in development mode

## Testing Strategy

- Unit tests for core functionality
- Integration tests with real-world JSON-LD processors
- Validation tests for generated artifacts
- Performance tests for large models