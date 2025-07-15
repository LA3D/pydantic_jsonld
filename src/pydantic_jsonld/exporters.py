"""
Export functions for JSON-LD contexts and SHACL shapes.
"""

from typing import Any, Dict, List, Optional, Type, Union, get_origin, get_args
from pydantic import BaseModel
from pydantic.fields import FieldInfo
import re


def export_context(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Export JSON-LD context for a Pydantic model.
    
    Args:
        model_class: The Pydantic model class to export context for
        
    Returns:
        Dictionary containing the @context for the model
    """
    # Delegate to the model's export_context method
    if hasattr(model_class, 'export_context'):
        return model_class.export_context()
    else:
        raise ValueError(f"Model {model_class.__name__} does not support context export")


def export_shacl(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Export SHACL shape for a Pydantic model.
    
    Args:
        model_class: The Pydantic model class to export SHACL for
        
    Returns:
        Dictionary containing SHACL shape definition
    """
    from .models import _JSONLD_META_KEY
    
    # Get the model's namespace info
    base_iri = getattr(model_class, '_json_ld_base', 'https://example.org/')
    prefixes = getattr(model_class, '_json_ld_prefixes', {})
    
    # Build the shape IRI
    shape_iri = f"{base_iri}shapes/{model_class.__name__}Shape"
    
    # Get target class IRI (could be from class-level annotation or inferred)
    target_class_iri = f"{base_iri}{model_class.__name__}"
    
    # Build property shapes
    property_shapes = []
    
    for field_name, field_info in model_class.model_fields.items():
        # Get JSON-LD metadata from field
        jsonld_meta = getattr(field_info, 'jsonld_meta', None)
        if not jsonld_meta:
            continue
            
        property_shape = _build_property_shape(
            field_name, field_info, jsonld_meta, base_iri
        )
        if property_shape:
            property_shapes.append(property_shape)
    
    # Build the complete shape
    shape_definition = {
        "@id": shape_iri,
        "@type": "sh:NodeShape",
        "sh:targetClass": {"@id": target_class_iri},
        "sh:closed": True,
        "sh:property": [{"@id": prop["@id"]} for prop in property_shapes]
    }
    
    # Build the complete graph
    graph = [shape_definition] + property_shapes
    
    # Build context with common SHACL prefixes
    context = {
        "sh": "http://www.w3.org/ns/shacl#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    }
    context.update(prefixes)
    
    return {
        "@context": context,
        "@graph": graph
    }


def _build_property_shape(
    field_name: str,
    field_info: FieldInfo,
    jsonld_meta: Dict[str, Any],
    base_iri: str
) -> Optional[Dict[str, Any]]:
    """
    Build a SHACL property shape from a Pydantic field.
    
    Args:
        field_name: The field name
        field_info: Pydantic field information
        jsonld_meta: JSON-LD metadata for the field
        base_iri: Base IRI for the shape
        
    Returns:
        Dictionary containing the property shape, or None if not applicable
    """
    property_iri = jsonld_meta.get("iri")
    if not property_iri:
        return None
    
    # Generate a unique ID for this property shape
    property_shape_id = f"{base_iri}shapes/{field_name}PropertyShape"
    
    # Start building the property shape
    property_shape = {
        "@id": property_shape_id,
        "@type": "sh:PropertyShape",
        "sh:path": {"@id": property_iri}
    }
    
    # Add cardinality constraints
    if field_info.is_required():
        property_shape["sh:minCount"] = 1
    
    # Get the field type for datatype constraints
    field_type = field_info.annotation
    
    # Handle Optional types
    if get_origin(field_type) is Union:
        args = get_args(field_type)
        if len(args) == 2 and type(None) in args:
            # This is Optional[T] which is Union[T, None]
            field_type = args[0] if args[1] is type(None) else args[1]
    
    # Add datatype constraints
    if jsonld_meta.get("type"):
        jsonld_type = jsonld_meta["type"]
        if jsonld_type == "@id":
            property_shape["sh:nodeKind"] = {"@id": "sh:IRI"}
        elif jsonld_type.startswith("xsd:"):
            property_shape["sh:datatype"] = {"@id": jsonld_type}
    else:
        # Infer datatype from Python type
        datatype = _python_type_to_xsd(field_type)
        if datatype:
            property_shape["sh:datatype"] = {"@id": datatype}
    
    # Add container constraints
    if jsonld_meta.get("container"):
        container = jsonld_meta["container"]
        if container == "@set":
            # For sets, we might want to add uniqueness constraints
            pass
        elif container == "@list":
            # For lists, order matters
            pass
    
    # Add field-specific constraints from Pydantic
    _add_field_constraints(property_shape, field_info, field_type)
    
    return property_shape


def _python_type_to_xsd(python_type: Any) -> Optional[str]:
    """
    Map Python types to XSD datatypes.
    
    Args:
        python_type: The Python type to map
        
    Returns:
        XSD datatype string, or None if not mappable
    """
    type_mapping = {
        str: "xsd:string",
        int: "xsd:integer",
        float: "xsd:double",
        bool: "xsd:boolean",
    }
    
    # Handle generic types
    origin = get_origin(python_type)
    if origin is list:
        # For lists, we don't change the datatype, just the cardinality
        args = get_args(python_type)
        if args:
            return _python_type_to_xsd(args[0])
        return None
    elif origin is dict:
        # Dictionaries are complex, might need special handling
        return None
    
    return type_mapping.get(python_type)


def _add_field_constraints(
    property_shape: Dict[str, Any],
    field_info: FieldInfo,
    field_type: Any
) -> None:
    """
    Add SHACL constraints based on Pydantic field constraints.
    
    Args:
        property_shape: The property shape to add constraints to
        field_info: Pydantic field information
        field_type: The field type
    """
    # Handle string constraints
    if field_type is str:
        if hasattr(field_info, 'max_length') and field_info.max_length is not None:
            property_shape["sh:maxLength"] = field_info.max_length
        if hasattr(field_info, 'min_length') and field_info.min_length is not None:
            property_shape["sh:minLength"] = field_info.min_length
        if hasattr(field_info, 'pattern') and field_info.pattern is not None:
            property_shape["sh:pattern"] = field_info.pattern
    
    # Handle numeric constraints
    elif field_type in (int, float):
        if hasattr(field_info, 'ge') and field_info.ge is not None:
            property_shape["sh:minInclusive"] = field_info.ge
        if hasattr(field_info, 'gt') and field_info.gt is not None:
            property_shape["sh:minExclusive"] = field_info.gt
        if hasattr(field_info, 'le') and field_info.le is not None:
            property_shape["sh:maxInclusive"] = field_info.le
        if hasattr(field_info, 'lt') and field_info.lt is not None:
            property_shape["sh:maxExclusive"] = field_info.lt
    
    # Handle list constraints
    origin = get_origin(field_type)
    if origin is list:
        if hasattr(field_info, 'max_length') and field_info.max_length is not None:
            property_shape["sh:maxCount"] = field_info.max_length
        if hasattr(field_info, 'min_length') and field_info.min_length is not None:
            property_shape["sh:minCount"] = field_info.min_length