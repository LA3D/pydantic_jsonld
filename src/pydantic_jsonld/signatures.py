"""
Core signing and verification functions for JSON-LD documents.

Implements W3C Data Integrity specification with Ed25519Signature2020.
"""

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

import pyld
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

from .crypto_utils import generate_key_id


def canonicalize_jsonld(document: Dict[str, Any]) -> bytes:
    """
    Canonicalize a JSON-LD document using RDF Dataset Normalization.
    
    Args:
        document: JSON-LD document to canonicalize
        
    Returns:
        Canonical representation as bytes
        
    Raises:
        ValueError: If document cannot be canonicalized
    """
    try:
        # Use PyLD to normalize the document
        canonical = pyld.jsonld.normalize(
            document,
            {
                'algorithm': 'URDNA2015',
                'format': 'application/n-quads'
            }
        )
        
        # Convert to bytes for hashing
        if isinstance(canonical, str):
            return canonical.encode('utf-8')
        else:
            return canonical
            
    except Exception as e:
        raise ValueError(f"Failed to canonicalize JSON-LD document: {e}")


def create_proof_object(
    verification_method: str,
    created: Optional[str] = None,
    proof_purpose: str = "assertionMethod"
) -> Dict[str, Any]:
    """
    Create a proof object template for Ed25519Signature2020.
    
    Args:
        verification_method: Identifier for the verification method/key
        created: ISO 8601 timestamp, defaults to current time
        proof_purpose: Purpose of the proof, typically "assertionMethod"
        
    Returns:
        Proof object without proofValue
    """
    if created is None:
        created = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    return {
        "type": "Ed25519Signature2020",
        "created": created,
        "verificationMethod": verification_method,
        "proofPurpose": proof_purpose
    }


def sign_jsonld_document(
    document: Dict[str, Any],
    private_key: Ed25519PrivateKey,
    verification_method: Optional[str] = None,
    created: Optional[str] = None,
    proof_purpose: str = "assertionMethod"
) -> Dict[str, Any]:
    """
    Sign a JSON-LD document with Ed25519Signature2020.
    
    Args:
        document: JSON-LD document to sign
        private_key: Ed25519 private key for signing
        verification_method: Key identifier, auto-generated if None
        created: ISO 8601 timestamp, defaults to current time
        proof_purpose: Purpose of the proof
        
    Returns:
        Signed JSON-LD document with embedded proof
        
    Raises:
        ValueError: If signing fails
    """
    # Make a copy to avoid modifying original
    doc_copy = json.loads(json.dumps(document))
    
    # Remove any existing proof
    if "proof" in doc_copy:
        del doc_copy["proof"]
    
    # Generate verification method if not provided
    if verification_method is None:
        public_key = private_key.public_key()
        verification_method = generate_key_id(public_key)
    
    # Create proof object
    proof = create_proof_object(verification_method, created, proof_purpose)
    
    # Create document with proof (but no proofValue yet)
    doc_with_proof = doc_copy.copy()
    doc_with_proof["proof"] = proof
    
    try:
        # Canonicalize the document with proof (minus proofValue)
        canonical_bytes = canonicalize_jsonld(doc_with_proof)
        
        # Hash the canonical representation
        hash_digest = hashlib.sha256(canonical_bytes).digest()
        
        # Sign the hash
        signature_bytes = private_key.sign(hash_digest)
        
        # Encode signature as base64
        signature_b64 = base64.b64encode(signature_bytes).decode('ascii')
        
        # Add proofValue to proof
        proof["proofValue"] = signature_b64
        doc_with_proof["proof"] = proof
        
        return doc_with_proof
        
    except Exception as e:
        raise ValueError(f"Failed to sign JSON-LD document: {e}")


def verify_jsonld_document(
    signed_document: Dict[str, Any],
    public_key: Ed25519PublicKey
) -> bool:
    """
    Verify a signed JSON-LD document.
    
    Args:
        signed_document: JSON-LD document with embedded proof
        public_key: Ed25519 public key for verification
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Extract proof
        if "proof" not in signed_document:
            return False
        
        proof = signed_document["proof"]
        
        # Check proof type
        if proof.get("type") != "Ed25519Signature2020":
            return False
        
        # Extract signature
        if "proofValue" not in proof:
            return False
        
        signature_b64 = proof["proofValue"]
        
        try:
            signature_bytes = base64.b64decode(signature_b64)
        except Exception:
            return False
        
        # Recreate document without proofValue
        doc_copy = json.loads(json.dumps(signed_document))
        proof_copy = doc_copy["proof"].copy()
        del proof_copy["proofValue"]
        doc_copy["proof"] = proof_copy
        
        # Canonicalize and hash
        canonical_bytes = canonicalize_jsonld(doc_copy)
        hash_digest = hashlib.sha256(canonical_bytes).digest()
        
        # Verify signature
        try:
            public_key.verify(signature_bytes, hash_digest)
            return True
        except InvalidSignature:
            return False
            
    except Exception:
        # Any error in verification process means invalid signature
        return False


def extract_proof_metadata(signed_document: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract proof metadata from a signed document.
    
    Args:
        signed_document: JSON-LD document with embedded proof
        
    Returns:
        Proof metadata or None if no valid proof found
    """
    if "proof" not in signed_document:
        return None
    
    proof = signed_document["proof"]
    
    # Return a copy without the signature value
    metadata = proof.copy()
    if "proofValue" in metadata:
        del metadata["proofValue"]
    
    return metadata


def remove_proof(signed_document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove proof from a signed document, returning the original data.
    
    Args:
        signed_document: JSON-LD document with embedded proof
        
    Returns:
        Document without proof
    """
    doc_copy = json.loads(json.dumps(signed_document))
    if "proof" in doc_copy:
        del doc_copy["proof"]
    return doc_copy