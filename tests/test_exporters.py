"""
Tests for the exporters module.
"""

import pytest
from typing import List, Optional

from pydantic_jsonld import JsonLDModel, Term
from pydantic_jsonld.exporters import export_context, export_shacl, _python_type_to_xsd


class TestExportContext:
    """Test the export_context function."""
    
    def test_export_context_delegates_to_model(self):
        """Test that export_context delegates to model's export_context method."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
        
        context = export_context(TestModel)
        model_context = TestModel.export_context()
        
        assert context == model_context
    
    def test_export_context_with_non_jsonld_model(self):
        """Test export_context with non-JsonLDModel class."""
        from pydantic import BaseModel
        
        class RegularModel(BaseModel):
            name: str
        
        with pytest.raises(ValueError) as exc_info:
            export_context(RegularModel)
        
        assert "does not support context export" in str(exc_info.value)


class TestExportShacl:
    """Test the export_shacl function."""
    
    def test_basic_shacl_export(self):
        """Test basic SHACL export."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: int = Term("schema:age", type_="xsd:integer")
        
        shacl = export_shacl(TestModel)
        
        assert "@context" in shacl
        assert "@graph" in shacl
        
        # Check context has required prefixes
        ctx = shacl["@context"]
        assert "sh" in ctx
        assert "xsd" in ctx
        assert "rdf" in ctx
        assert "rdfs" in ctx
        
        # Check graph structure
        graph = shacl["@graph"]
        assert len(graph) >= 1
        
        # Find the node shape
        node_shape = None
        for item in graph:
            if item.get("@type") == "sh:NodeShape":
                node_shape = item
                break
        
        assert node_shape is not None
        assert "sh:targetClass" in node_shape
        assert "sh:property" in node_shape
        assert node_shape["sh:closed"] is True
    
    def test_shacl_with_configured_base(self):
        """Test SHACL export with configured base IRI."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
        
        TestModel.configure_jsonld(base="https://example.org/")
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Find the node shape
        node_shape = None
        for item in graph:
            if item.get("@type") == "sh:NodeShape":
                node_shape = item
                break
        
        assert node_shape is not None
        assert node_shape["@id"].startswith("https://example.org/shapes/")
        assert node_shape["sh:targetClass"]["@id"].startswith("https://example.org/")
    
    def test_shacl_with_custom_prefixes(self):
        """Test SHACL export with custom prefixes."""
        class TestModel(JsonLDModel):
            name: str = Term("ex:name")
        
        TestModel.configure_jsonld(
            prefixes={"ex": "https://example.org/vocab/"}
        )
        
        shacl = export_shacl(TestModel)
        ctx = shacl["@context"]
        
        assert ctx["ex"] == "https://example.org/vocab/"
    
    def test_shacl_property_shapes(self):
        """Test SHACL property shapes generation."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: int = Term("schema:age", type_="xsd:integer")
            email: Optional[str] = Term("schema:email", type_="xsd:string")
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Should have node shape + property shapes
        property_shapes = [item for item in graph if item.get("@type") == "sh:PropertyShape"]
        assert len(property_shapes) >= 2  # At least name and age (email is optional)
        
        # Check property shapes have required properties
        for prop_shape in property_shapes:
            assert "sh:path" in prop_shape
            assert "@id" in prop_shape["sh:path"]
    
    def test_shacl_with_id_type(self):
        """Test SHACL export with @id type."""
        class TestModel(JsonLDModel):
            identifier: str = Term("schema:identifier", type_="@id")
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Find property shape for identifier
        id_prop_shape = None
        for item in graph:
            if (item.get("@type") == "sh:PropertyShape" and 
                item.get("sh:path", {}).get("@id") == "schema:identifier"):
                id_prop_shape = item
                break
        
        assert id_prop_shape is not None
        assert id_prop_shape["sh:nodeKind"]["@id"] == "sh:IRI"
    
    def test_shacl_with_xsd_datatype(self):
        """Test SHACL export with XSD datatype."""
        class TestModel(JsonLDModel):
            count: int = Term("ex:count", type_="xsd:integer")
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Find property shape for count
        count_prop_shape = None
        for item in graph:
            if (item.get("@type") == "sh:PropertyShape" and 
                item.get("sh:path", {}).get("@id") == "ex:count"):
                count_prop_shape = item
                break
        
        assert count_prop_shape is not None
        assert count_prop_shape["sh:datatype"]["@id"] == "xsd:integer"
    
    def test_shacl_inferred_datatypes(self):
        """Test SHACL export with inferred datatypes."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            age: int = Term("schema:age")
            weight: float = Term("schema:weight")
            active: bool = Term("schema:active")
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Check inferred datatypes
        expected_datatypes = {
            "schema:name": "xsd:string",
            "schema:age": "xsd:integer",
            "schema:weight": "xsd:double",
            "schema:active": "xsd:boolean"
        }
        
        for item in graph:
            if item.get("@type") == "sh:PropertyShape":
                path_id = item.get("sh:path", {}).get("@id")
                if path_id in expected_datatypes:
                    expected_datatype = expected_datatypes[path_id]
                    assert item.get("sh:datatype", {}).get("@id") == expected_datatype
    
    def test_shacl_with_list_fields(self):
        """Test SHACL export with list fields."""
        class TestModel(JsonLDModel):
            keywords: List[str] = Term("schema:keywords", container="@set")
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Find property shape for keywords
        keywords_prop_shape = None
        for item in graph:
            if (item.get("@type") == "sh:PropertyShape" and 
                item.get("sh:path", {}).get("@id") == "schema:keywords"):
                keywords_prop_shape = item
                break
        
        assert keywords_prop_shape is not None
        # Should infer datatype from list element type
        assert keywords_prop_shape.get("sh:datatype", {}).get("@id") == "xsd:string"
    
    def test_shacl_skips_unannotated_fields(self):
        """Test that SHACL export skips fields without JSON-LD annotations."""
        class TestModel(JsonLDModel):
            name: str = Term("schema:name")
            internal_field: str = "default"  # No Term() annotation
        
        shacl = export_shacl(TestModel)
        graph = shacl["@graph"]
        
        # Should only have property shape for name
        property_shapes = [item for item in graph if item.get("@type") == "sh:PropertyShape"]
        assert len(property_shapes) == 1
        
        prop_shape = property_shapes[0]
        assert prop_shape["sh:path"]["@id"] == "schema:name"


class TestPythonTypeToXsd:
    """Test the _python_type_to_xsd function."""
    
    def test_basic_types(self):
        """Test basic Python type mappings."""
        assert _python_type_to_xsd(str) == "xsd:string"
        assert _python_type_to_xsd(int) == "xsd:integer"
        assert _python_type_to_xsd(float) == "xsd:double"
        assert _python_type_to_xsd(bool) == "xsd:boolean"
    
    def test_unknown_type(self):
        """Test unknown type returns None."""
        class CustomType:
            pass
        
        assert _python_type_to_xsd(CustomType) is None
    
    def test_list_type(self):
        """Test list type maps to element type."""
        assert _python_type_to_xsd(List[str]) == "xsd:string"
        assert _python_type_to_xsd(List[int]) == "xsd:integer"
    
    def test_dict_type(self):
        """Test dict type returns None."""
        from typing import Dict
        assert _python_type_to_xsd(Dict[str, str]) is None
    
    def test_empty_list_type(self):
        """Test empty list type returns None."""
        assert _python_type_to_xsd(list) is None


class TestBuildPropertyShape:
    """Test the _build_property_shape function."""
    
    def test_property_shape_with_required_field(self):
        """Test property shape generation for required field."""
        from pydantic_jsonld.exporters import _build_property_shape
        from pydantic.fields import FieldInfo
        
        field_info = FieldInfo()
        # Mock required field
        field_info._attributes_set = {"annotation"}
        field_info.annotation = str
        
        jsonld_meta = {"iri": "schema:name"}
        
        prop_shape = _build_property_shape("name", field_info, jsonld_meta, "https://example.org/")
        
        assert prop_shape is not None
        assert prop_shape["sh:path"]["@id"] == "schema:name"
        assert "sh:minCount" in prop_shape  # Required field should have minCount
    
    def test_property_shape_with_no_iri(self):
        """Test property shape generation with no IRI returns None."""
        from pydantic_jsonld.exporters import _build_property_shape
        from pydantic.fields import FieldInfo
        
        field_info = FieldInfo()
        jsonld_meta = {}  # No IRI
        
        prop_shape = _build_property_shape("name", field_info, jsonld_meta, "https://example.org/")
        
        assert prop_shape is None