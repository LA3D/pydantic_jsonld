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


class SignableJsonLDModel(JsonLDModel):
    """
    Extension of JsonLDModel with cryptographic signing capabilities.
    
    Supports Ed25519Signature2020 for W3C Data Integrity compliance.
    """
    
    def sign(
        self, 
        private_key, 
        verification_method: Optional[str] = None,
        created: Optional[str] = None,
        proof_purpose: str = "assertionMethod"
    ) -> Dict[str, Any]:
        """
        Sign this model instance as a JSON-LD document.
        
        Args:
            private_key: Ed25519PrivateKey instance or raw bytes
            verification_method: Key identifier, auto-generated if None
            created: ISO 8601 timestamp, defaults to current time
            proof_purpose: Purpose of the proof
            
        Returns:
            Signed JSON-LD document with embedded proof
            
        Raises:
            ValueError: If signing fails
        """
        from .signatures import sign_jsonld_document
        from .crypto_utils import private_key_from_bytes
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        
        # Convert bytes to private key if needed
        if isinstance(private_key, bytes):
            private_key = private_key_from_bytes(private_key)
        elif not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("private_key must be Ed25519PrivateKey or 32-byte bytes")
        
        # Export model as JSON-LD
        context_doc = self.export_context()
        context = context_doc["@context"]
        
        # Get model data with aliases
        model_data = self.model_dump(by_alias=True)
        
        # Create JSON-LD document
        document = {
            "@context": context,
            **model_data
        }
        
        # Sign the document
        return sign_jsonld_document(
            document, 
            private_key, 
            verification_method, 
            created, 
            proof_purpose
        )
    
    @classmethod
    def verify(
        cls, 
        signed_document: Dict[str, Any], 
        public_key
    ) -> bool:
        """
        Verify a signed JSON-LD document.
        
        Args:
            signed_document: JSON-LD document with embedded proof
            public_key: Ed25519PublicKey instance or raw bytes
            
        Returns:
            True if signature is valid, False otherwise
        """
        from .signatures import verify_jsonld_document
        from .crypto_utils import public_key_from_bytes
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        
        # Convert bytes to public key if needed
        if isinstance(public_key, bytes):
            public_key = public_key_from_bytes(public_key)
        elif not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("public_key must be Ed25519PublicKey or 32-byte bytes")
        
        return verify_jsonld_document(signed_document, public_key)
    
    @classmethod
    def extract_data(cls, signed_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the original model data from a signed document.
        
        Args:
            signed_document: JSON-LD document with embedded proof
            
        Returns:
            Model data without proof or context
        """
        from .signatures import remove_proof
        
        # Remove proof
        doc_without_proof = remove_proof(signed_document)
        
        # Remove context
        data = doc_without_proof.copy()
        if "@context" in data:
            del data["@context"]
        
        return data
    
    @classmethod
    def from_signed_document(cls, signed_document: Dict[str, Any]):
        """
        Create model instance from a signed document.
        
        Args:
            signed_document: JSON-LD document with embedded proof
            
        Returns:
            Model instance (proof is not preserved in instance)
            
        Note:
            This extracts the data and creates a new model instance.
            The cryptographic proof is not preserved in the instance.
        """
        data = cls.extract_data(signed_document)
        return cls(**data)
    
    @staticmethod
    def get_proof_metadata(signed_document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract proof metadata from a signed document.
        
        Args:
            signed_document: JSON-LD document with embedded proof
            
        Returns:
            Proof metadata or None if no valid proof found
        """
        from .signatures import extract_proof_metadata
        return extract_proof_metadata(signed_document)