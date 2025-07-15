"""
Pydantic JSON-LD: Generate JSON-LD contexts and SHACL shapes from Pydantic models.

This package provides a way to annotate Pydantic models with JSON-LD metadata
and generate separate context files for semantic web applications while keeping
the original models clean for LLM function calling.
"""

from .models import JsonLDModel, Term
from .validation import validate_context
from .exporters import export_context, export_shacl, export_mixed_graph

__version__ = "0.1.0"
__all__ = ["JsonLDModel", "Term", "validate_context", "export_context", "export_shacl", "export_mixed_graph"]