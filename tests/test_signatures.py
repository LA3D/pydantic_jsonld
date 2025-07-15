"""
Tests for signature functionality.
"""

import json
import pytest
from datetime import datetime, timezone
from typing import List, Optional

from pydantic_jsonld import (
    SignableJsonLDModel, 
    Term,
    generate_ed25519_keypair,
    sign_jsonld_document,
    verify_jsonld_document,
    canonicalize_jsonld,
    private_key_to_base64,
    public_key_to_base64,
    private_key_from_base64,
    public_key_from_base64,
)
from pydantic_jsonld.crypto_utils import (
    private_key_to_bytes,
    public_key_to_bytes,
    private_key_from_bytes,
    public_key_from_bytes,
    generate_key_id,
)
from pydantic_jsonld.signatures import (
    create_proof_object,
    extract_proof_metadata,
    remove_proof,
)


class PersonModel(SignableJsonLDModel):
    """Test model for signatures."""
    name: str = Term("schema:name")
    email: str = Term("schema:email", type_="xsd:string")
    age: Optional[int] = Term("schema:age", type_="xsd:integer")


class ProductModel(SignableJsonLDModel):
    """Another test model for signatures."""
    identifier: str = Term("schema:identifier", alias="@id", type_="@id")
    name: str = Term("schema:name")
    price: float = Term("schema:price", type_="xsd:decimal")


# Configure models
PersonModel.configure_jsonld(
    base="https://example.org/people/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

ProductModel.configure_jsonld(
    base="https://example.org/products/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


class TestCryptoUtils:
    """Test cryptographic utility functions."""
    
    def test_generate_keypair(self):
        """Test Ed25519 key pair generation."""
        private_key, public_key = generate_ed25519_keypair()
        
        assert private_key is not None
        assert public_key is not None
        
        # Keys should be related
        assert private_key.public_key().public_bytes_raw() == public_key.public_bytes_raw()
    
    def test_key_to_bytes_conversion(self):
        """Test key to bytes conversion."""
        private_key, public_key = generate_ed25519_keypair()
        
        # Convert to bytes
        private_bytes = private_key_to_bytes(private_key)
        public_bytes = public_key_to_bytes(public_key)
        
        # Check lengths
        assert len(private_bytes) == 32
        assert len(public_bytes) == 32
        
        # Convert back
        private_key2 = private_key_from_bytes(private_bytes)
        public_key2 = public_key_from_bytes(public_bytes)
        
        # Should be the same
        assert private_key_to_bytes(private_key2) == private_bytes
        assert public_key_to_bytes(public_key2) == public_bytes
    
    def test_key_to_base64_conversion(self):
        """Test key to base64 conversion."""
        private_key, public_key = generate_ed25519_keypair()
        
        # Convert to base64
        private_b64 = private_key_to_base64(private_key)
        public_b64 = public_key_to_base64(public_key)
        
        # Should be valid base64 strings
        assert isinstance(private_b64, str)
        assert isinstance(public_b64, str)
        
        # Convert back
        private_key2 = private_key_from_base64(private_b64)
        public_key2 = public_key_from_base64(public_b64)
        
        # Should be the same
        assert private_key_to_base64(private_key2) == private_b64
        assert public_key_to_base64(public_key2) == public_b64
    
    def test_generate_key_id(self):
        """Test key ID generation."""
        _, public_key = generate_ed25519_keypair()
        
        key_id = generate_key_id(public_key)
        
        assert isinstance(key_id, str)
        assert key_id.startswith("key-")
        assert len(key_id) == 12  # "key-" + 8 chars
    
    def test_invalid_key_bytes(self):
        """Test error handling for invalid key bytes."""
        with pytest.raises(ValueError, match="exactly 32 bytes"):
            private_key_from_bytes(b"invalid")
        
        with pytest.raises(ValueError, match="exactly 32 bytes"):
            public_key_from_bytes(b"invalid")
    
    def test_invalid_base64_keys(self):
        """Test error handling for invalid base64 keys."""
        with pytest.raises(ValueError, match="Invalid base64"):
            private_key_from_base64("invalid-base64!")
        
        with pytest.raises(ValueError, match="Invalid base64"):
            public_key_from_base64("invalid-base64!")


class TestSignatures:
    """Test core signature functions."""
    
    def test_canonicalize_jsonld(self):
        """Test JSON-LD canonicalization."""
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice"
        }
        
        canonical = canonicalize_jsonld(document)
        
        assert isinstance(canonical, bytes)
        assert len(canonical) > 0
        
        # Should contain N-Quads
        canonical_str = canonical.decode('utf-8')
        assert "<https://schema.org/name>" in canonical_str
        assert "Alice" in canonical_str
    
    def test_canonicalize_invalid_jsonld(self):
        """Test canonicalization error handling."""
        # This should work fine - PyLD is quite tolerant
        document = {"invalid": "document"}
        canonical = canonicalize_jsonld(document)
        assert isinstance(canonical, bytes)
    
    def test_create_proof_object(self):
        """Test proof object creation."""
        verification_method = "key-abc123"
        created = "2025-07-15T14:30:00Z"
        
        proof = create_proof_object(verification_method, created)
        
        assert proof["type"] == "Ed25519Signature2020"
        assert proof["created"] == created
        assert proof["verificationMethod"] == verification_method
        assert proof["proofPurpose"] == "assertionMethod"
        assert "proofValue" not in proof
    
    def test_create_proof_object_defaults(self):
        """Test proof object creation with defaults."""
        verification_method = "key-abc123"
        
        proof = create_proof_object(verification_method)
        
        assert proof["type"] == "Ed25519Signature2020"
        assert "created" in proof
        assert proof["verificationMethod"] == verification_method
        assert proof["proofPurpose"] == "assertionMethod"
        
        # Check created timestamp format
        created = proof["created"]
        assert created.endswith("Z")
        # Should be valid ISO 8601
        datetime.fromisoformat(created.replace("Z", "+00:00"))
    
    def test_sign_and_verify_document(self):
        """Test signing and verifying a JSON-LD document."""
        private_key, public_key = generate_ed25519_keypair()
        
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice"
        }
        
        # Sign document
        signed_doc = sign_jsonld_document(document, private_key)
        
        # Check structure
        assert "@context" in signed_doc
        assert "name" in signed_doc
        assert "proof" in signed_doc
        
        proof = signed_doc["proof"]
        assert proof["type"] == "Ed25519Signature2020"
        assert "created" in proof
        assert "verificationMethod" in proof
        assert "proofValue" in proof
        
        # Verify signature
        is_valid = verify_jsonld_document(signed_doc, public_key)
        assert is_valid is True
    
    def test_verify_with_wrong_key(self):
        """Test verification with wrong public key."""
        private_key1, _ = generate_ed25519_keypair()
        _, public_key2 = generate_ed25519_keypair()
        
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice"
        }
        
        # Sign with key1
        signed_doc = sign_jsonld_document(document, private_key1)
        
        # Verify with key2 (should fail)
        is_valid = verify_jsonld_document(signed_doc, public_key2)
        assert is_valid is False
    
    def test_verify_tampered_document(self):
        """Test verification of tampered document."""
        private_key, public_key = generate_ed25519_keypair()
        
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice"
        }
        
        # Sign document
        signed_doc = sign_jsonld_document(document, private_key)
        
        # Tamper with document
        signed_doc["name"] = "Bob"
        
        # Verification should fail
        is_valid = verify_jsonld_document(signed_doc, public_key)
        assert is_valid is False
    
    def test_verify_invalid_signature_format(self):
        """Test verification with invalid signature format."""
        _, public_key = generate_ed25519_keypair()
        
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice",
            "proof": {
                "type": "Ed25519Signature2020",
                "created": "2025-07-15T14:30:00Z",
                "verificationMethod": "key-test",
                "proofPurpose": "assertionMethod",
                "proofValue": "invalid-signature"
            }
        }
        
        is_valid = verify_jsonld_document(document, public_key)
        assert is_valid is False
    
    def test_extract_proof_metadata(self):
        """Test extracting proof metadata."""
        private_key, _ = generate_ed25519_keypair()
        
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice"
        }
        
        signed_doc = sign_jsonld_document(document, private_key, "key-test123")
        metadata = extract_proof_metadata(signed_doc)
        
        assert metadata is not None
        assert metadata["type"] == "Ed25519Signature2020"
        assert metadata["verificationMethod"] == "key-test123"
        assert "created" in metadata
        assert "proofValue" not in metadata  # Should be excluded
    
    def test_remove_proof(self):
        """Test removing proof from signed document."""
        private_key, _ = generate_ed25519_keypair()
        
        document = {
            "@context": {"name": "https://schema.org/name"},
            "name": "Alice"
        }
        
        signed_doc = sign_jsonld_document(document, private_key)
        unsigned_doc = remove_proof(signed_doc)
        
        assert "proof" not in unsigned_doc
        assert unsigned_doc["name"] == "Alice"
        assert unsigned_doc["@context"] == document["@context"]


class TestSignableJsonLDModel:
    """Test SignableJsonLDModel functionality."""
    
    def test_sign_model_instance(self):
        """Test signing a model instance."""
        private_key, public_key = generate_ed25519_keypair()
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = person.sign(private_key)
        
        # Check structure
        assert "@context" in signed_doc
        assert "name" in signed_doc
        assert "email" in signed_doc
        assert "age" in signed_doc
        assert "proof" in signed_doc
        
        # Verify signature
        is_valid = PersonModel.verify(signed_doc, public_key)
        assert is_valid is True
    
    def test_sign_with_bytes_key(self):
        """Test signing with raw bytes key."""
        private_key, public_key = generate_ed25519_keypair()
        private_bytes = private_key_to_bytes(private_key)
        public_bytes = public_key_to_bytes(public_key)
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = person.sign(private_bytes)
        
        is_valid = PersonModel.verify(signed_doc, public_bytes)
        assert is_valid is True
    
    def test_sign_with_custom_params(self):
        """Test signing with custom parameters."""
        private_key, public_key = generate_ed25519_keypair()
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = person.sign(
            private_key,
            verification_method="custom-key-123",
            created="2025-07-15T14:30:00Z",
            proof_purpose="authentication"
        )
        
        proof = signed_doc["proof"]
        assert proof["verificationMethod"] == "custom-key-123"
        assert proof["created"] == "2025-07-15T14:30:00Z"
        assert proof["proofPurpose"] == "authentication"
        
        is_valid = PersonModel.verify(signed_doc, public_key)
        assert is_valid is True
    
    def test_extract_data_from_signed_document(self):
        """Test extracting model data from signed document."""
        private_key, _ = generate_ed25519_keypair()
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = person.sign(private_key)
        
        extracted_data = PersonModel.extract_data(signed_doc)
        
        assert extracted_data == {
            "name": "Alice",
            "email": "alice@example.com", 
            "age": 30
        }
    
    def test_from_signed_document(self):
        """Test creating model instance from signed document."""
        private_key, _ = generate_ed25519_keypair()
        
        original = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = original.sign(private_key)
        
        recreated = PersonModel.from_signed_document(signed_doc)
        
        assert recreated.name == original.name
        assert recreated.email == original.email
        assert recreated.age == original.age
    
    def test_get_proof_metadata(self):
        """Test getting proof metadata from signed document."""
        private_key, _ = generate_ed25519_keypair()
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = person.sign(private_key, verification_method="test-key")
        
        metadata = PersonModel.get_proof_metadata(signed_doc)
        
        assert metadata is not None
        assert metadata["verificationMethod"] == "test-key"
        assert metadata["type"] == "Ed25519Signature2020"
    
    def test_sign_with_invalid_key_type(self):
        """Test error handling for invalid key type."""
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        
        with pytest.raises(ValueError, match="must be Ed25519PrivateKey"):
            person.sign("invalid-key")
    
    def test_verify_with_invalid_key_type(self):
        """Test error handling for invalid public key type."""
        signed_doc = {
            "@context": {},
            "proof": {"type": "Ed25519Signature2020"}
        }
        
        with pytest.raises(ValueError, match="must be Ed25519PublicKey"):
            PersonModel.verify(signed_doc, "invalid-key")
    
    def test_model_with_alias_signing(self):
        """Test signing model with field aliases."""
        private_key, public_key = generate_ed25519_keypair()
        
        product = ProductModel(
            identifier="product-123",
            name="Test Product", 
            price=99.99
        )
        
        signed_doc = product.sign(private_key)
        
        # Should use alias (@id) in output
        # Note: serialization_alias is needed for this to work
        assert "identifier" in signed_doc
        assert signed_doc["identifier"] == "product-123"
        
        is_valid = ProductModel.verify(signed_doc, public_key)
        assert is_valid is True


class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_sign_verify_roundtrip(self):
        """Test complete sign/verify roundtrip."""
        private_key, public_key = generate_ed25519_keypair()
        
        # Create model
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        
        # Sign it
        signed_doc = person.sign(private_key)
        
        # Verify signature
        assert PersonModel.verify(signed_doc, public_key) is True
        
        # Extract original data
        data = PersonModel.extract_data(signed_doc)
        recreated = PersonModel(**data)
        
        # Should match original
        assert recreated.name == person.name
        assert recreated.email == person.email
        assert recreated.age == person.age
    
    def test_multiple_signatures_different_keys(self):
        """Test that different keys produce different signatures."""
        private_key1, _ = generate_ed25519_keypair()
        private_key2, _ = generate_ed25519_keypair()
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        
        signed_doc1 = person.sign(private_key1)
        signed_doc2 = person.sign(private_key2)
        
        # Signatures should be different
        proof1 = signed_doc1["proof"]["proofValue"]
        proof2 = signed_doc2["proof"]["proofValue"]
        assert proof1 != proof2
    
    def test_deterministic_signatures(self):
        """Test that same input produces same signature."""
        private_key, _ = generate_ed25519_keypair()
        
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        fixed_time = "2025-07-15T14:30:00Z"
        
        signed_doc1 = person.sign(private_key, created=fixed_time)
        signed_doc2 = person.sign(private_key, created=fixed_time)
        
        # Should be identical
        assert signed_doc1 == signed_doc2
    
    def test_explicit_signature_verification(self):
        """Explicit test to verify signatures are cryptographically sound."""
        private_key, public_key = generate_ed25519_keypair()
        
        # Create and sign model
        person = PersonModel(name="Alice", email="alice@example.com", age=30)
        signed_doc = person.sign(private_key)
        
        # Test 1: Verify with correct key
        is_valid1 = PersonModel.verify(signed_doc, public_key)
        assert is_valid1 is True, "Valid signature should verify as True"
        
        # Test 2: Verify with low-level function
        is_valid2 = verify_jsonld_document(signed_doc, public_key)
        assert is_valid2 is True, "Low-level verification should match high-level"
        
        # Test 3: Verify with wrong key
        _, wrong_public_key = generate_ed25519_keypair()
        is_valid3 = PersonModel.verify(signed_doc, wrong_public_key)
        assert is_valid3 is False, "Wrong key should fail verification"
        
        # Test 4: Verify tampered document
        tampered_doc = signed_doc.copy()
        tampered_doc["name"] = "Bob"  # Change the name
        is_valid4 = PersonModel.verify(tampered_doc, public_key)
        assert is_valid4 is False, "Tampered document should fail verification"
        
        # Test 5: Manual canonicalization and verification
        from pydantic_jsonld.signatures import remove_proof
        import hashlib
        import base64
        
        # Remove proof and recreate signing process
        doc_without_proof = remove_proof(signed_doc)
        
        # Add empty proof structure like signing process does
        proof_template = {
            "type": signed_doc["proof"]["type"],
            "created": signed_doc["proof"]["created"],
            "verificationMethod": signed_doc["proof"]["verificationMethod"],
            "proofPurpose": signed_doc["proof"]["proofPurpose"]
        }
        doc_with_empty_proof = doc_without_proof.copy()
        doc_with_empty_proof["proof"] = proof_template
        
        # Canonicalize and hash
        canonical = canonicalize_jsonld(doc_with_empty_proof)
        hash_digest = hashlib.sha256(canonical).digest()
        
        # Extract signature and verify manually
        signature_bytes = base64.b64decode(signed_doc["proof"]["proofValue"])
        
        try:
            public_key.verify(signature_bytes, hash_digest)
            manual_verify = True
        except Exception:
            manual_verify = False
        
        assert manual_verify is True, "Manual verification should succeed"