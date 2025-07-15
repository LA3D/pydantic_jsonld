"""
Cryptographic utilities for Ed25519 key generation and management.
"""

import base64
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def generate_ed25519_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """
    Generate a new Ed25519 private/public key pair.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def private_key_to_bytes(private_key: Ed25519PrivateKey) -> bytes:
    """
    Convert Ed25519 private key to raw bytes.
    
    Args:
        private_key: Ed25519PrivateKey instance
        
    Returns:
        Raw private key bytes (32 bytes)
    """
    return private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )


def public_key_to_bytes(public_key: Ed25519PublicKey) -> bytes:
    """
    Convert Ed25519 public key to raw bytes.
    
    Args:
        public_key: Ed25519PublicKey instance
        
    Returns:
        Raw public key bytes (32 bytes)
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )


def private_key_from_bytes(key_bytes: bytes) -> Ed25519PrivateKey:
    """
    Create Ed25519 private key from raw bytes.
    
    Args:
        key_bytes: Raw private key bytes (32 bytes)
        
    Returns:
        Ed25519PrivateKey instance
        
    Raises:
        ValueError: If key_bytes is not exactly 32 bytes
    """
    if len(key_bytes) != 32:
        raise ValueError(f"Ed25519 private key must be exactly 32 bytes, got {len(key_bytes)}")
    
    return Ed25519PrivateKey.from_private_bytes(key_bytes)


def public_key_from_bytes(key_bytes: bytes) -> Ed25519PublicKey:
    """
    Create Ed25519 public key from raw bytes.
    
    Args:
        key_bytes: Raw public key bytes (32 bytes)
        
    Returns:
        Ed25519PublicKey instance
        
    Raises:
        ValueError: If key_bytes is not exactly 32 bytes
    """
    if len(key_bytes) != 32:
        raise ValueError(f"Ed25519 public key must be exactly 32 bytes, got {len(key_bytes)}")
    
    return Ed25519PublicKey.from_public_bytes(key_bytes)


def private_key_to_base64(private_key: Ed25519PrivateKey) -> str:
    """
    Convert Ed25519 private key to base64 string.
    
    Args:
        private_key: Ed25519PrivateKey instance
        
    Returns:
        Base64-encoded private key string
    """
    key_bytes = private_key_to_bytes(private_key)
    return base64.b64encode(key_bytes).decode('ascii')


def public_key_to_base64(public_key: Ed25519PublicKey) -> str:
    """
    Convert Ed25519 public key to base64 string.
    
    Args:
        public_key: Ed25519PublicKey instance
        
    Returns:
        Base64-encoded public key string
    """
    key_bytes = public_key_to_bytes(public_key)
    return base64.b64encode(key_bytes).decode('ascii')


def private_key_from_base64(key_b64: str) -> Ed25519PrivateKey:
    """
    Create Ed25519 private key from base64 string.
    
    Args:
        key_b64: Base64-encoded private key string
        
    Returns:
        Ed25519PrivateKey instance
        
    Raises:
        ValueError: If base64 string is invalid or wrong length
    """
    try:
        key_bytes = base64.b64decode(key_b64)
        return private_key_from_bytes(key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid base64 private key: {e}")


def public_key_from_base64(key_b64: str) -> Ed25519PublicKey:
    """
    Create Ed25519 public key from base64 string.
    
    Args:
        key_b64: Base64-encoded public key string
        
    Returns:
        Ed25519PublicKey instance
        
    Raises:
        ValueError: If base64 string is invalid or wrong length
    """
    try:
        key_bytes = base64.b64decode(key_b64)
        return public_key_from_bytes(key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid base64 public key: {e}")


def generate_key_id(public_key: Ed25519PublicKey) -> str:
    """
    Generate a simple key identifier from public key.
    
    Args:
        public_key: Ed25519PublicKey instance
        
    Returns:
        Key identifier string (first 8 chars of base64 public key)
    """
    key_b64 = public_key_to_base64(public_key)
    return f"key-{key_b64[:8]}"