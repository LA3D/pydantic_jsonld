"""
Pydantic JSON-LD: Generate JSON-LD contexts and SHACL shapes from Pydantic models.

This package provides a way to annotate Pydantic models with JSON-LD metadata
and generate separate context files for semantic web applications while keeping
the original models clean for LLM function calling.
"""

from .models import JsonLDModel, SignableJsonLDModel, Term
from .validation import validate_context
from .exporters import export_context, export_shacl, export_mixed_graph
from .crypto_utils import (
    generate_ed25519_keypair,
    private_key_to_base64,
    public_key_to_base64,
    private_key_from_base64,
    public_key_from_base64,
)
from .signatures import (
    sign_jsonld_document,
    verify_jsonld_document,
    canonicalize_jsonld,
)

__version__ = "0.1.0"
__all__ = [
    "JsonLDModel",
    "SignableJsonLDModel",
    "Term", 
    "validate_context",
    "export_context",
    "export_shacl",
    "export_mixed_graph",
    "generate_ed25519_keypair",
    "private_key_to_base64",
    "public_key_to_base64", 
    "private_key_from_base64",
    "public_key_from_base64",
    "sign_jsonld_document",
    "verify_jsonld_document",
    "canonicalize_jsonld",
]