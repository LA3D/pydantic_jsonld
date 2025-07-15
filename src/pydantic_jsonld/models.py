"""
Core models and field helpers for JSON-LD context generation.
"""

from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo
from .validation import validate_context


_JSONLD_META_KEY = "__jsonld__"


class JsonLDFieldInfo(FieldInfo):
    """Extended FieldInfo that can store JSON-LD metadata."""
    
    def __init__(self, jsonld_meta: Dict[str, Any], **kwargs: Any):
        super().__init__(**kwargs)
        self.jsonld_meta = jsonld_meta


def Term(
    iri: str,
    type_: Optional[str] = None,
    container: Optional[str] = None,
    language: Optional[str] = None,
    **field_kwargs: Any,
) -> JsonLDFieldInfo:
    """
    Create a Pydantic field with JSON-LD metadata.
    
    Args:
        iri: The IRI for this term in the JSON-LD context
        type_: Optional @type for the term (e.g., "@id", "xsd:string")
        container: Optional @container for the term (e.g., "@set", "@list")
        language: Optional @language for the term
        **field_kwargs: Additional arguments passed to Field()
    
    Returns:
        A JsonLDFieldInfo with JSON-LD metadata stored
    """
    # Store JSON-LD metadata
    jsonld_meta = {
        "iri": iri,
        "type": type_,
        "container": container,
        "language": language,
    }
    
    # Create the field with metadata
    return JsonLDFieldInfo(jsonld_meta=jsonld_meta, **field_kwargs)


class JsonLDModel(BaseModel):
    """
    Base class for Pydantic models with JSON-LD context export capabilities.
    
    This class extends BaseModel to add methods for exporting JSON-LD contexts
    and SHACL shapes while keeping the original model JSON clean for LLM usage.
    """
    
    model_config = ConfigDict(
        # Keep the model JSON clean - no extra fields
        extra="forbid",
        # Allow custom configuration for JSON-LD settings
        arbitrary_types_allowed=True,
    )
    
    
    @classmethod
    def configure_jsonld(
        cls,
        base: Optional[str] = None,
        vocab: Optional[str] = None,
        remote_contexts: Optional[List[str]] = None,
        prefixes: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Configure JSON-LD settings for this model.
        
        Args:
            base: Base IRI for @base
            vocab: Vocabulary IRI for @vocab
            remote_contexts: List of remote context URLs to import
            prefixes: Dictionary of prefix mappings
        """
        if base is not None:
            cls._json_ld_base = base
        if vocab is not None:
            cls._json_ld_vocab = vocab
        if remote_contexts is not None:
            cls._json_ld_remote_contexts = remote_contexts
        if prefixes is not None:
            cls._json_ld_prefixes = prefixes
    
    @classmethod
    def export_context(cls) -> Dict[str, Any]:
        """
        Export JSON-LD context for this model.
        
        Returns:
            Dictionary containing the @context for this model
        """
        # Start with local context object
        local_context: Dict[str, Any] = {}
        
        # Add base and vocab if configured
        if hasattr(cls, '_json_ld_base') and cls._json_ld_base:
            local_context["@base"] = cls._json_ld_base
        if hasattr(cls, '_json_ld_vocab') and cls._json_ld_vocab:
            local_context["@vocab"] = cls._json_ld_vocab
        
        # Add prefix mappings
        if hasattr(cls, '_json_ld_prefixes') and cls._json_ld_prefixes:
            local_context.update(cls._json_ld_prefixes)
        
        # Process model fields to build term mappings
        for field_name, field_info in cls.model_fields.items():
            # Get JSON-LD metadata from field
            jsonld_meta = getattr(field_info, 'jsonld_meta', None)
            if not jsonld_meta:
                continue
                
            # Use alias if available, otherwise field name
            term_name = field_info.alias or field_name
            
            # Build term definition
            term_def: Dict[str, Any] = {"@id": jsonld_meta["iri"]}
            
            # Add optional properties
            if jsonld_meta.get("type"):
                term_def["@type"] = jsonld_meta["type"]
            if jsonld_meta.get("container"):
                term_def["@container"] = jsonld_meta["container"]
            if jsonld_meta.get("language"):
                term_def["@language"] = jsonld_meta["language"]
            
            local_context[term_name] = term_def
        
        # Build final context structure
        if hasattr(cls, '_json_ld_remote_contexts') and cls._json_ld_remote_contexts:
            # Array format: [remote_context, local_context]
            context = cls._json_ld_remote_contexts + [local_context]
        else:
            # Single local context
            context = local_context
        
        result = {"@context": context}
        
        # Validate the context before returning
        validate_context(result)
        
        return result
    
    @classmethod
    def export_shacl(cls) -> Dict[str, Any]:
        """
        Export SHACL shape for this model.
        
        Returns:
            Dictionary containing SHACL shape definition
        """
        # This will be implemented in a separate file
        from .exporters import export_shacl
        return export_shacl(cls)