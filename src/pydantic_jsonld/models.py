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
        # Store in both places for compatibility
        metadata = kwargs.get('metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata[_JSONLD_META_KEY] = jsonld_meta
        kwargs['metadata'] = metadata
        
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
            
            # Skip JSON-LD keywords - they shouldn't be redefined in context
            if term_name.startswith("@"):
                continue
            
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
    
    @classmethod
    def export_graph(
        cls,
        instances: List["JsonLDModel"],
        graph_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_id_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export multiple model instances as a named JSON-LD graph.
        
        Args:
            instances: List of model instances to include in the graph
            graph_id: IRI for the named graph. If None, generates one based on class name
            metadata: Optional metadata to include at graph level (created, source, etc.)
            auto_id_pattern: Pattern for auto-generating @id values (e.g., "item-{index}")
            
        Returns:
            Dictionary containing JSON-LD document with @graph structure
        """
        if not instances:
            raise ValueError("Cannot create graph from empty instances list")
        
        # Validate all instances are of the same type as this class
        for instance in instances:
            if not isinstance(instance, cls):
                raise ValueError(f"All instances must be of type {cls.__name__}, got {type(instance).__name__}")
        
        # Generate graph ID if not provided
        if graph_id is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            graph_id = f"{cls.__name__}-graph-{timestamp}"
        
        # Get the context from the class
        context_doc = cls.export_context()
        context = context_doc["@context"]
        
        # Build the graph items
        graph_items = []
        for i, instance in enumerate(instances):
            # Get instance data with aliases
            item_data = instance.model_dump(by_alias=True)
            
            # Auto-generate @id if not present and pattern provided
            if "@id" not in item_data and auto_id_pattern:
                item_data["@id"] = auto_id_pattern.format(index=i+1, **item_data)
            
            graph_items.append(item_data)
        
        # Build the graph document
        graph_doc: Dict[str, Any] = {
            "@context": context,
            "@id": graph_id,
            "@type": "Dataset",
            "@graph": graph_items
        }
        
        # Add metadata if provided
        if metadata:
            graph_doc.update(metadata)
        
        # Validate the result if we have pyld available
        try:
            from .validation import validate_context
            validate_context({"@context": context})
        except ImportError:
            pass  # Validation is optional
        
        return graph_doc