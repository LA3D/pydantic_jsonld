"""
JSON-LD context validation logic.
"""

from typing import Any, Dict, List, Union
from pydantic import BaseModel, ValidationError, field_validator


class ContextTerm(BaseModel):
    """
    Validates individual terms in a JSON-LD context.
    """
    
    term_definition: Dict[str, Any]
    
    @field_validator("term_definition")
    @classmethod
    def validate_term_definition(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a term definition follows JSON-LD specifications.
        """
        if not isinstance(v, dict):
            raise ValueError("Term definition must be a dictionary")
        
        # Check for required @id
        if "@id" not in v:
            raise ValueError("Term definition must have @id property")
        
        # Check for allowed JSON-LD keywords
        allowed_keywords = {
            "@id", "@type", "@language", "@container", "@context", 
            "@reverse", "@nest", "@prefix", "@protected"
        }
        
        unknown_keywords = set(v.keys()) - allowed_keywords
        if unknown_keywords:
            raise ValueError(f"Unknown JSON-LD keywords: {unknown_keywords}")
        
        # Validate @type values
        if "@type" in v:
            type_value = v["@type"]
            if not isinstance(type_value, str):
                raise ValueError("@type must be a string")
        
        # Validate @container values
        if "@container" in v:
            container_value = v["@container"]
            valid_containers = {"@list", "@set", "@index", "@language", "@id", "@type"}
            if isinstance(container_value, str):
                if container_value not in valid_containers:
                    raise ValueError(f"Invalid @container value: {container_value}")
            elif isinstance(container_value, list):
                for item in container_value:
                    if item not in valid_containers:
                        raise ValueError(f"Invalid @container value: {item}")
            else:
                raise ValueError("@container must be a string or list")
        
        # Validate @language values
        if "@language" in v:
            language_value = v["@language"]
            if not isinstance(language_value, str):
                raise ValueError("@language must be a string")
        
        return v


class JsonLDContext(BaseModel):
    """
    Validates a complete JSON-LD context structure.
    """
    
    context: Union[Dict[str, Any], List[Union[Dict[str, Any], str]]]
    
    @field_validator("context")
    @classmethod
    def validate_context(cls, v: Union[Dict[str, Any], List[Union[Dict[str, Any], str]]]) -> Union[Dict[str, Any], List[Union[Dict[str, Any], str]]]:
        """
        Validate the context structure.
        """
        if isinstance(v, list):
            # Array context - validate each item
            for i, item in enumerate(v):
                if isinstance(item, str):
                    # Remote context URL - basic validation
                    if not item.startswith(("http://", "https://")):
                        raise ValueError(f"Remote context at index {i} must be a valid URL")
                elif isinstance(item, dict):
                    # Local context object
                    cls._validate_context_object(item)
                else:
                    raise ValueError(f"Context array item at index {i} must be string or dict")
        elif isinstance(v, dict):
            # Single context object
            cls._validate_context_object(v)
        else:
            raise ValueError("Context must be a dictionary or array")
        
        return v
    
    @classmethod
    def _validate_context_object(cls, context_obj: Dict[str, Any]) -> None:
        """
        Validate a single context object.
        """
        for key, value in context_obj.items():
            if key.startswith("@") and key not in ["@id", "@type", "@value", "@language", "@index", "@list", "@set", "@reverse", "@graph", "@context"]:
                # JSON-LD keyword (but not terms that can be defined)
                if key == "@version":
                    if not isinstance(value, (int, float)) or value != 1.1:
                        raise ValueError("@version must be 1.1")
                elif key == "@base":
                    if not isinstance(value, str):
                        raise ValueError("@base must be a string")
                elif key == "@vocab":
                    if not isinstance(value, str):
                        raise ValueError("@vocab must be a string")
                elif key == "@language":
                    if not isinstance(value, str):
                        raise ValueError("@language must be a string")
                elif key == "@import":
                    if not isinstance(value, str):
                        raise ValueError("@import must be a string")
                elif key == "@protected":
                    if not isinstance(value, bool):
                        raise ValueError("@protected must be a boolean")
                else:
                    raise ValueError(f"Unknown JSON-LD keyword: {key}")
            else:
                # Term definition (including @id, @type, etc. which can be redefined)
                if isinstance(value, str):
                    # Simple string mapping (IRI)
                    continue
                elif isinstance(value, dict):
                    # Complex term definition
                    ContextTerm(term_definition=value)
                else:
                    raise ValueError(f"Term '{key}' must be string or dict")


def validate_context(context_data: Dict[str, Any]) -> None:
    """
    Validate a complete JSON-LD context document.
    
    Args:
        context_data: The context document to validate
        
    Raises:
        ValidationError: If the context is invalid
    """
    if "@context" not in context_data:
        raise ValueError("Document must have @context property")
    
    try:
        JsonLDContext(context=context_data["@context"])
    except ValidationError as e:
        raise ValueError(f"Invalid JSON-LD context: {e}") from e