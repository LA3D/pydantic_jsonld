"""
Signed Models Example for Pydantic JSON-LD

This example demonstrates how to create cryptographically signed Pydantic models
using Ed25519 signatures compliant with W3C Data Integrity specification.

Key use cases:
- LLM output verification
- Agentic workflow provenance  
- Semantic data integrity
- Enterprise compliance
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Add the src directory to the path so we can import pydantic_jsonld
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic_jsonld import (
    SignableJsonLDModel,
    Term,
    generate_ed25519_keypair,
    private_key_to_base64,
    public_key_to_base64,
)


# =============================================================================
# Example Models for Different Scenarios
# =============================================================================

class LLMResponse(SignableJsonLDModel):
    """Model for LLM-generated content that needs verification."""
    
    query: str = Term("ex:query")
    response: str = Term("ex:response")
    model: str = Term("ex:model")
    timestamp: str = Term("schema:dateCreated", type_="xsd:dateTime")
    confidence: float = Term("ex:confidence", type_="xsd:decimal")


class Person(SignableJsonLDModel):
    """Person model suitable for signed semantic data."""
    
    name: str = Term("schema:name")
    email: str = Term("schema:email", type_="xsd:string")
    role: str = Term("schema:jobTitle")
    department: Optional[str] = Term("schema:department")


class ResearchData(SignableJsonLDModel):
    """Research dataset with cryptographic integrity."""
    
    title: str = Term("schema:name")
    researchers: List[str] = Term("schema:author", container="@list")
    methodology: str = Term("ex:methodology")
    findings: str = Term("ex:findings")
    dataset_id: str = Term("schema:identifier", type_="@id")


# Configure models
LLMResponse.configure_jsonld(
    base="https://ai.example.org/responses/",
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://ai.example.org/vocab/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

Person.configure_jsonld(
    base="https://example.org/people/",
    prefixes={
        "schema": "https://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

ResearchData.configure_jsonld(
    base="https://research.example.org/datasets/",
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://research.example.org/vocab/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 1: Basic Signing and Verification
# =============================================================================

def demonstrate_basic_signing():
    """Demonstrate basic model signing and verification."""
    print("=" * 70)
    print("BASIC MODEL SIGNING AND VERIFICATION")
    print("=" * 70)
    
    # Generate keys
    private_key, public_key = generate_ed25519_keypair()
    print(f"Generated Ed25519 keypair")
    print(f"Public key (first 16 chars): {public_key_to_base64(public_key)[:16]}...")
    
    # Create model instance
    person = Person(
        name="Dr. Alice Johnson",
        email="alice@university.edu",
        role="Principal Investigator",
        department="Computer Science"
    )
    
    print(f"\\nCreated person: {person.name}")
    
    # Normal JSON output (clean for LLMs)
    normal_json = person.model_dump()
    print(f"\\nNormal JSON (for LLMs): {normal_json}")
    
    # Sign the model
    signed_doc = person.sign(
        private_key,
        verification_method="researcher-key-001",
        proof_purpose="assertionMethod"
    )
    
    print(f"\\nSigned document structure:")
    print(f"  - Has @context: {'@context' in signed_doc}")
    print(f"  - Has proof: {'proof' in signed_doc}")
    print(f"  - Proof type: {signed_doc['proof']['type']}")
    print(f"  - Verification method: {signed_doc['proof']['verificationMethod']}")
    print(f"  - Created: {signed_doc['proof']['created']}")
    
    # Verify signature
    is_valid = Person.verify(signed_doc, public_key)
    print(f"\\nSignature verification: {'✓ VALID' if is_valid else '✗ INVALID'}")
    
    # Extract original data
    extracted_data = Person.extract_data(signed_doc)
    recreated_person = Person(**extracted_data)
    print(f"\\nExtracted data matches: {recreated_person.name == person.name}")


# =============================================================================
# Example 2: LLM Output Signing (Agentic Workflow)
# =============================================================================

def demonstrate_llm_output_signing():
    """Demonstrate signing LLM outputs for agentic workflows."""
    print("\\n" + "=" * 70)
    print("LLM OUTPUT SIGNING FOR AGENTIC WORKFLOWS")
    print("=" * 70)
    
    # Simulate agent keys
    agent_private_key, agent_public_key = generate_ed25519_keypair()
    print(f"Generated agent keypair for signing LLM outputs")
    
    # Simulate LLM response
    llm_response = LLMResponse(
        query="What are the key challenges in AI safety?",
        response="The primary challenges include alignment, robustness, interpretability, and value learning. These require interdisciplinary approaches combining technical research with ethics and policy.",
        model="claude-3-5-sonnet-20241022",
        timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        confidence=0.92
    )
    
    print(f"\\nLLM Response:")
    print(f"  Query: {llm_response.query}")
    print(f"  Model: {llm_response.model}")
    print(f"  Confidence: {llm_response.confidence}")
    
    # Sign the response
    signed_response = llm_response.sign(
        agent_private_key,
        verification_method="agent-001",
        proof_purpose="assertionMethod"
    )
    
    print(f"\\nSigned LLM response:")
    print(json.dumps(signed_response, indent=2))
    
    # Verify in downstream system
    is_authentic = LLMResponse.verify(signed_response, agent_public_key)
    print(f"\\nDownstream verification: {'✓ AUTHENTIC' if is_authentic else '✗ TAMPERED'}")
    
    # Demonstrate tamper detection
    tampered_response = signed_response.copy()
    tampered_response["confidence"] = 0.99  # Modify confidence
    
    is_tampered = LLMResponse.verify(tampered_response, agent_public_key)
    print(f"Tampered response verification: {'✓ VALID' if is_tampered else '✗ INVALID (detected tampering)'}")


# =============================================================================
# Example 3: Research Data Integrity
# =============================================================================

def demonstrate_research_data_integrity():
    """Demonstrate signing research data for publication integrity."""
    print("\\n" + "=" * 70)
    print("RESEARCH DATA INTEGRITY WITH SIGNATURES")
    print("=" * 70)
    
    # Research institution keys
    institution_private_key, institution_public_key = generate_ed25519_keypair()
    print(f"Generated institutional signing key for research data")
    
    # Create research dataset
    dataset = ResearchData(
        title="Machine Learning Bias in Healthcare Applications",
        researchers=["Dr. Alice Johnson", "Dr. Bob Smith", "Dr. Carol Williams"],
        methodology="We analyzed 10,000 medical records using fairness metrics including demographic parity and equalized odds.",
        findings="Significant bias detected in diagnostic algorithms, with 15% higher false positive rates for underrepresented groups.",
        dataset_id="dataset-ml-bias-2025-001"
    )
    
    print(f"\\nResearch Dataset:")
    print(f"  Title: {dataset.title}")
    print(f"  Researchers: {len(dataset.researchers)} authors")
    print(f"  Dataset ID: {dataset.dataset_id}")
    
    # Sign with institutional key
    signed_dataset = dataset.sign(
        institution_private_key,
        verification_method="university-research-key",
        proof_purpose="assertionMethod"
    )
    
    # Extract proof metadata
    proof_metadata = ResearchData.get_proof_metadata(signed_dataset)
    print(f"\\nProof Metadata:")
    print(f"  Type: {proof_metadata['type']}")
    print(f"  Created: {proof_metadata['created']}")
    print(f"  Purpose: {proof_metadata['proofPurpose']}")
    print(f"  Verification Method: {proof_metadata['verificationMethod']}")
    
    # Verify for publication
    is_verified = ResearchData.verify(signed_dataset, institution_public_key)
    print(f"\\nPublication verification: {'✓ VERIFIED' if is_verified else '✗ UNVERIFIED'}")
    
    # Show JSON-LD context preservation
    context = signed_dataset["@context"]
    print(f"\\nSemantic context preserved: {bool(context)}")
    print(f"Context includes schema.org: {'schema' in str(context)}")


# =============================================================================
# Example 4: Key Management and Workflow
# =============================================================================

def demonstrate_key_management():
    """Demonstrate key management practices."""
    print("\\n" + "=" * 70)
    print("KEY MANAGEMENT FOR PRODUCTION WORKFLOWS")
    print("=" * 70)
    
    # Generate keys for different entities
    entities = ["llm-agent", "research-institution", "data-processor"]
    keys = {}
    
    for entity in entities:
        private_key, public_key = generate_ed25519_keypair()
        keys[entity] = {
            "private": private_key,
            "public": public_key,
            "private_b64": private_key_to_base64(private_key),
            "public_b64": public_key_to_base64(public_key)
        }
    
    print(f"Generated keys for {len(entities)} entities:")
    for entity in entities:
        public_b64 = keys[entity]["public_b64"]
        print(f"  {entity}: {public_b64[:16]}...")
    
    # Demonstrate multi-entity workflow
    print(f"\\nMulti-entity workflow example:")
    
    # 1. LLM agent processes data
    person = Person(
        name="Dr. Jane Researcher",
        email="jane@lab.edu", 
        role="Research Scientist",
        department="AI Ethics"
    )
    
    agent_signed = person.sign(
        keys["llm-agent"]["private"],
        verification_method="llm-agent-001"
    )
    print(f"  1. LLM agent signed person data")
    
    # 2. Research institution validates
    agent_valid = Person.verify(agent_signed, keys["llm-agent"]["public"])
    print(f"  2. Institution verified agent signature: {'✓' if agent_valid else '✗'}")
    
    # 3. Institution re-signs for publication
    if agent_valid:
        # Extract data and re-sign with institutional key
        person_data = Person.extract_data(agent_signed)
        person_recreated = Person(**person_data)
        
        institution_signed = person_recreated.sign(
            keys["research-institution"]["private"],
            verification_method="institution-research-key"
        )
        print(f"  3. Institution re-signed for publication")
        
        # 4. Data processor verifies institutional signature
        final_valid = Person.verify(institution_signed, keys["research-institution"]["public"])
        print(f"  4. Data processor verified institutional signature: {'✓' if final_valid else '✗'}")


# =============================================================================
# Example 5: Production Integration Patterns
# =============================================================================

def demonstrate_production_patterns():
    """Demonstrate production-ready integration patterns."""
    print("\\n" + "=" * 70)
    print("PRODUCTION INTEGRATION PATTERNS")
    print("=" * 70)
    
    # Simulate enterprise workflow
    workflow_private_key, workflow_public_key = generate_ed25519_keypair()
    
    print("Enterprise workflow simulation:")
    print("  1. API receives LLM-generated data")
    print("  2. System validates and signs data")
    print("  3. Data stored in graph database with signature")
    print("  4. Downstream systems verify on retrieval")
    
    # Step 1-2: Receive and sign
    llm_data = Person(
        name="Generated Person",
        email="generated@ai.example.com",
        role="AI Assistant Output",
        department="Virtual"
    )
    
    # Enterprise signing with metadata
    signed_data = llm_data.sign(
        workflow_private_key,
        verification_method="enterprise-workflow-v2.1",
        created=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        proof_purpose="assertionMethod"
    )
    
    print(f"\\n  Signed data size: {len(json.dumps(signed_data))} bytes")
    
    # Step 3: Store (simulated)
    storage_record = {
        "id": "record-12345",
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "data": signed_data,
        "signature_valid": True
    }
    print(f"  Stored record ID: {storage_record['id']}")
    
    # Step 4: Retrieve and verify
    retrieved_data = storage_record["data"]
    verification_result = Person.verify(retrieved_data, workflow_public_key)
    
    print(f"  Retrieved and verified: {'✓ SUCCESS' if verification_result else '✗ FAILED'}")
    
    # Performance note
    print(f"\\n  Performance characteristics:")
    print(f"    - Ed25519 signing: ~65,000 signatures/second")
    print(f"    - Ed25519 verification: ~18,000 verifications/second")
    print(f"    - Signature size: 64 bytes (base64: ~88 chars)")
    print(f"    - Public key size: 32 bytes (base64: ~44 chars)")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Run all signed model demonstrations."""
    print("Pydantic JSON-LD Signed Models Examples")
    print("=" * 70)
    print("Demonstrating cryptographic signatures for semantic models")
    
    # Run all demonstrations
    demonstrate_basic_signing()
    demonstrate_llm_output_signing()
    demonstrate_research_data_integrity()
    demonstrate_key_management()
    demonstrate_production_patterns()
    
    print("\\n" + "=" * 70)
    print("SUMMARY OF SIGNED MODEL CAPABILITIES")
    print("=" * 70)
    print("✅ Cryptographic signatures enable:")
    print("  • LLM output verification and provenance")
    print("  • Agentic workflow integrity chains")
    print("  • Research data publication integrity")
    print("  • Enterprise compliance and audit trails")
    print("  • Tamper detection for semantic data")
    print("  • Multi-party trust without central authority")
    print("\\n✅ Technical features:")
    print("  • W3C Data Integrity compliant signatures")
    print("  • Ed25519 cryptography (fast and secure)")
    print("  • JSON-LD context preservation")
    print("  • Clean separation: LLM JSON vs signed semantic data")
    print("  • Standards-based verification workflows")
    print("\\n✅ Production ready:")
    print("  • High-performance signing and verification")
    print("  • Comprehensive test coverage")
    print("  • Enterprise key management patterns")
    print("  • Graph database integration ready")
    print("\\n🚀 Ready for agentic AI workflows!")


if __name__ == "__main__":
    main()