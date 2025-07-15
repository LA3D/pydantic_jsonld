"""
Extended examples for pydantic-jsonld package.

This file demonstrates advanced usage patterns, edge cases, and real-world
scenarios for using pydantic-jsonld to create models that work for both
LLM function calling and semantic web applications.
"""

from typing import List, Optional, Union, Literal
from datetime import datetime
from enum import Enum
from pydantic import Field, field_validator
from pydantic_jsonld import JsonLDModel, Term


# =============================================================================
# Example 1: Scientific Research Paper Model
# =============================================================================

class ResearchPaper(JsonLDModel):
    """A comprehensive research paper model using multiple vocabularies."""
    
    # Basic identifiers
    doi: str = Term("schema:doi", alias="@id", type_="@id")
    title: str = Term("schema:name")
    abstract: str = Term("schema:abstract")
    
    # Publication details
    publication_date: str = Term("schema:datePublished", type_="xsd:date")
    journal: Optional[str] = Term("schema:publisher")
    volume: Optional[int] = Term("bibo:volume", type_="xsd:integer")
    issue: Optional[int] = Term("bibo:issue", type_="xsd:integer")
    pages: Optional[str] = Term("bibo:pages")
    
    # Authors and affiliations
    authors: List[str] = Term("schema:author", container="@list")
    corresponding_author: Optional[str] = Term("schema:editor", type_="@id")
    
    # Classification
    keywords: List[str] = Term("schema:keywords", container="@set")
    subject_areas: List[str] = Term("schema:about", container="@set")
    research_field: Optional[str] = Term("dcat:theme")
    
    # Content structure
    sections: List[str] = Term("schema:hasPart", container="@list")
    figures: List[str] = Term("schema:image", container="@list")
    tables: List[str] = Term("ex:hasTable", container="@list")
    
    # Citations and references
    cites: List[str] = Term("cito:cites", container="@set", type_="@id")
    cited_by_count: Optional[int] = Term("ex:citationCount", type_="xsd:integer")
    
    # Open access and licensing
    license: Optional[str] = Term("schema:license", type_="@id")
    is_open_access: bool = Term("ex:isOpenAccess", type_="xsd:boolean")
    
    # Quality metrics
    peer_reviewed: bool = Term("ex:isPeerReviewed", type_="xsd:boolean", default=True)
    impact_factor: Optional[float] = Term("ex:impactFactor", type_="xsd:decimal")


# Configure with multiple vocabularies
ResearchPaper.configure_jsonld(
    base="https://doi.org/",
    vocab="https://schema.org/",
    remote_contexts=[
        "https://schema.org/",
        "https://sparontologies.github.io/cito/current/cito.json"
    ],
    prefixes={
        "schema": "https://schema.org/",
        "bibo": "http://purl.org/ontology/bibo/",
        "cito": "http://purl.org/spar/cito/",
        "dcat": "http://www.w3.org/ns/dcat#",
        "ex": "https://example.org/research/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 2: E-commerce Product with Variants
# =============================================================================

class ProductVariant(JsonLDModel):
    """Product variant with specific attributes."""
    
    sku: str = Term("schema:sku", alias="@id", type_="@id")
    color: Optional[str] = Term("schema:color")
    size: Optional[str] = Term("schema:size")
    material: Optional[str] = Term("schema:material")
    price: float = Term("schema:price", type_="xsd:decimal")
    currency: str = Term("schema:priceCurrency", default="USD")
    availability: Literal["InStock", "OutOfStock", "PreOrder"] = Term(
        "schema:availability", 
        default="InStock"
    )
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v


class Product(JsonLDModel):
    """E-commerce product with rich metadata."""
    
    # Core product info
    gtin: str = Term("schema:gtin", alias="@id", type_="@id")
    name: str = Term("schema:name")
    description: str = Term("schema:description")
    brand: str = Term("schema:brand")
    model: Optional[str] = Term("schema:model")
    
    # Categorization
    category: str = Term("schema:category")
    product_type: str = Term("ex:productType")
    tags: List[str] = Term("schema:keywords", container="@set")
    
    # Media
    images: List[str] = Term("schema:image", container="@list", type_="@id")
    videos: List[str] = Term("schema:video", container="@list", type_="@id")
    
    # Variants and pricing
    variants: List[str] = Term("ex:hasVariant", container="@set", type_="@id")
    base_price: float = Term("schema:price", type_="xsd:decimal")
    currency: str = Term("schema:priceCurrency", default="USD")
    
    # Specifications
    dimensions: Optional[str] = Term("ex:dimensions")
    weight: Optional[float] = Term("schema:weight", type_="xsd:decimal")
    weight_unit: str = Term("ex:weightUnit", default="kg")
    
    # Reviews and ratings
    average_rating: Optional[float] = Term("schema:aggregateRating", type_="xsd:decimal")
    review_count: Optional[int] = Term("ex:reviewCount", type_="xsd:integer")
    
    # Compliance and certifications
    certifications: List[str] = Term("ex:certification", container="@set")
    safety_warnings: List[str] = Term("ex:safetyWarning", container="@set")
    
    # Sustainability
    eco_friendly: bool = Term("ex:isEcoFriendly", type_="xsd:boolean", default=False)
    recycling_info: Optional[str] = Term("ex:recyclingInfo")


Product.configure_jsonld(
    base="https://products.example.com/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://example.com/ecommerce/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)

ProductVariant.configure_jsonld(
    base="https://products.example.com/variants/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://example.com/ecommerce/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 3: Healthcare Patient Record
# =============================================================================

class PatientRecord(JsonLDModel):
    """Healthcare patient record with privacy considerations."""
    
    # Patient identifiers (anonymized)
    patient_id: str = Term("ex:patientId", alias="@id", type_="@id")
    medical_record_number: str = Term("ex:medicalRecordNumber")
    
    # Demographics (anonymized/generalized)
    age_range: str = Term("ex:ageRange")  # e.g., "30-40"
    gender: Optional[str] = Term("schema:gender")
    zip_code_prefix: Optional[str] = Term("ex:zipPrefix")  # First 3 digits only
    
    # Medical history
    conditions: List[str] = Term("ex:hasCondition", container="@set")
    allergies: List[str] = Term("ex:hasAllergy", container="@set")
    medications: List[str] = Term("ex:takingMedication", container="@set")
    
    # Visit information
    visit_date: str = Term("ex:visitDate", type_="xsd:date")
    visit_type: str = Term("ex:visitType")
    chief_complaint: str = Term("ex:chiefComplaint")
    
    # Vital signs
    blood_pressure_systolic: Optional[int] = Term("ex:bpSystolic", type_="xsd:integer")
    blood_pressure_diastolic: Optional[int] = Term("ex:bpDiastolic", type_="xsd:integer")
    heart_rate: Optional[int] = Term("ex:heartRate", type_="xsd:integer")
    temperature: Optional[float] = Term("ex:temperature", type_="xsd:decimal")
    temperature_unit: str = Term("ex:temperatureUnit", default="celsius")
    
    # Assessments
    diagnosis: List[str] = Term("ex:diagnosis", container="@set")
    treatment_plan: List[str] = Term("ex:treatmentPlan", container="@list")
    
    # Follow-up
    next_appointment: Optional[str] = Term("ex:nextAppointment", type_="xsd:date")
    referrals: List[str] = Term("ex:referralTo", container="@set")
    
    # Data governance
    consent_given: bool = Term("ex:consentGiven", type_="xsd:boolean")
    data_retention_until: str = Term("ex:retentionDate", type_="xsd:date")


PatientRecord.configure_jsonld(
    base="https://hospital.example.org/patients/",
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://hospital.example.org/ontology/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 4: Financial Transaction
# =============================================================================

class FinancialTransaction(JsonLDModel):
    """Financial transaction with compliance and audit trail."""
    
    # Transaction identifiers
    transaction_id: str = Term("ex:transactionId", alias="@id", type_="@id")
    reference_number: Optional[str] = Term("ex:referenceNumber")
    
    # Transaction details
    transaction_type: Literal["transfer", "payment", "deposit", "withdrawal"] = Term("ex:transactionType")
    amount: float = Term("schema:amount", type_="xsd:decimal")
    currency: str = Term("schema:currency")
    
    # Parties involved
    from_account: str = Term("ex:fromAccount", type_="@id")
    to_account: str = Term("ex:toAccount", type_="@id")
    
    # Timing
    initiated_at: str = Term("ex:initiatedAt", type_="xsd:dateTime")
    completed_at: Optional[str] = Term("ex:completedAt", type_="xsd:dateTime")
    
    # Status and processing
    status: Literal["pending", "completed", "failed", "cancelled"] = Term("ex:status")
    processing_fees: Optional[float] = Term("ex:processingFee", type_="xsd:decimal")
    
    # Compliance and risk
    risk_score: Optional[float] = Term("ex:riskScore", type_="xsd:decimal")
    compliance_flags: List[str] = Term("ex:complianceFlag", container="@set")
    requires_approval: bool = Term("ex:requiresApproval", type_="xsd:boolean", default=False)
    
    # Audit trail
    created_by: str = Term("ex:createdBy", type_="@id")
    approved_by: Optional[str] = Term("ex:approvedBy", type_="@id")
    ip_address: Optional[str] = Term("ex:sourceIpAddress")
    user_agent: Optional[str] = Term("ex:userAgent")
    
    # Description and metadata
    description: Optional[str] = Term("schema:description")
    merchant_category: Optional[str] = Term("ex:merchantCategory")
    tags: List[str] = Term("schema:keywords", container="@set")


FinancialTransaction.configure_jsonld(
    base="https://bank.example.com/transactions/",
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://bank.example.com/ontology/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 5: IoT Sensor Data
# =============================================================================

class SensorReading(JsonLDModel):
    """IoT sensor reading with temporal and spatial context."""
    
    # Reading identifier
    reading_id: str = Term("ex:readingId", alias="@id", type_="@id")
    
    # Sensor information
    sensor_id: str = Term("sosa:madeBySensor", type_="@id")
    sensor_type: str = Term("ex:sensorType")
    
    # Temporal context
    timestamp: str = Term("sosa:resultTime", type_="xsd:dateTime")
    
    # Spatial context
    location_lat: Optional[float] = Term("schema:latitude", type_="xsd:decimal")
    location_lon: Optional[float] = Term("schema:longitude", type_="xsd:decimal")
    location_alt: Optional[float] = Term("schema:elevation", type_="xsd:decimal")
    location_name: Optional[str] = Term("schema:locationCreated")
    
    # Measurements
    property_measured: str = Term("sosa:observedProperty")
    value: float = Term("sosa:hasSimpleResult", type_="xsd:decimal")
    unit: str = Term("ex:unit")
    
    # Quality and confidence
    accuracy: Optional[float] = Term("ex:accuracy", type_="xsd:decimal")
    confidence: Optional[float] = Term("ex:confidence", type_="xsd:decimal")
    quality_flag: Optional[str] = Term("ex:qualityFlag")
    
    # Environmental context
    temperature: Optional[float] = Term("ex:ambientTemperature", type_="xsd:decimal")
    humidity: Optional[float] = Term("ex:ambientHumidity", type_="xsd:decimal")
    
    # Device status
    battery_level: Optional[float] = Term("ex:batteryLevel", type_="xsd:decimal")
    signal_strength: Optional[float] = Term("ex:signalStrength", type_="xsd:decimal")
    
    # Data lineage
    processing_pipeline: Optional[str] = Term("ex:processingPipeline")
    calibration_date: Optional[str] = Term("ex:lastCalibration", type_="xsd:date")


SensorReading.configure_jsonld(
    base="https://iot.example.org/readings/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "sosa": "http://www.w3.org/ns/sosa/",
        "ex": "https://iot.example.org/ontology/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 6: Educational Course with Complex Relationships
# =============================================================================

class Course(JsonLDModel):
    """Educational course with prerequisites, outcomes, and assessments."""
    
    # Course identifiers
    course_code: str = Term("ex:courseCode", alias="@id", type_="@id")
    title: str = Term("schema:name")
    description: str = Term("schema:description")
    
    # Academic details
    credits: int = Term("ex:creditHours", type_="xsd:integer")
    level: Literal["undergraduate", "graduate", "doctoral"] = Term("ex:academicLevel")
    discipline: str = Term("schema:educationalAlignment")
    
    # Prerequisites and corequisites
    prerequisites: List[str] = Term("ex:hasPrerequisite", container="@set", type_="@id")
    corequisites: List[str] = Term("ex:hasCorequisite", container="@set", type_="@id")
    
    # Learning objectives and outcomes
    learning_objectives: List[str] = Term("ex:learningObjective", container="@list")
    learning_outcomes: List[str] = Term("ex:learningOutcome", container="@list")
    skills_developed: List[str] = Term("ex:skillDeveloped", container="@set")
    
    # Content structure
    modules: List[str] = Term("schema:hasPart", container="@list", type_="@id")
    required_readings: List[str] = Term("ex:requiredReading", container="@list")
    optional_readings: List[str] = Term("ex:optionalReading", container="@list")
    
    # Assessment methods
    assessment_types: List[str] = Term("ex:assessmentType", container="@set")
    grading_scheme: str = Term("ex:gradingScheme")
    
    # Delivery mode
    delivery_mode: Literal["in-person", "online", "hybrid"] = Term("ex:deliveryMode")
    language: str = Term("schema:inLanguage", default="en")
    
    # Scheduling
    duration_weeks: int = Term("ex:durationWeeks", type_="xsd:integer")
    contact_hours: float = Term("ex:contactHours", type_="xsd:decimal")
    
    # Resources and requirements
    required_software: List[str] = Term("ex:requiredSoftware", container="@set")
    required_hardware: List[str] = Term("ex:requiredHardware", container="@set")
    
    # Accreditation and standards
    accredited_by: List[str] = Term("ex:accreditedBy", container="@set")
    meets_standards: List[str] = Term("ex:meetsStandard", container="@set")


Course.configure_jsonld(
    base="https://university.example.edu/courses/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://university.example.edu/ontology/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Example 7: Supply Chain Item with Provenance
# =============================================================================

class SupplyChainItem(JsonLDModel):
    """Supply chain item with full provenance tracking."""
    
    # Item identification
    item_id: str = Term("ex:itemId", alias="@id", type_="@id")
    batch_number: str = Term("ex:batchNumber")
    serial_number: Optional[str] = Term("ex:serialNumber")
    
    # Product information
    product_name: str = Term("schema:name")
    product_category: str = Term("schema:category")
    manufacturer: str = Term("schema:manufacturer", type_="@id")
    
    # Origin and sourcing
    country_of_origin: str = Term("ex:countryOfOrigin")
    region_of_origin: Optional[str] = Term("ex:regionOfOrigin")
    raw_materials: List[str] = Term("ex:containsMaterial", container="@set")
    supplier: str = Term("ex:suppliedBy", type_="@id")
    
    # Manufacturing details
    manufactured_date: str = Term("ex:manufacturedDate", type_="xsd:date")
    expiry_date: Optional[str] = Term("schema:expires", type_="xsd:date")
    production_facility: str = Term("ex:producedAt", type_="@id")
    quality_grade: Optional[str] = Term("ex:qualityGrade")
    
    # Certifications and compliance
    organic_certified: bool = Term("ex:isOrganicCertified", type_="xsd:boolean", default=False)
    fair_trade_certified: bool = Term("ex:isFairTradeCertified", type_="xsd:boolean", default=False)
    certifications: List[str] = Term("ex:hasCertification", container="@set")
    
    # Supply chain tracking
    previous_owner: Optional[str] = Term("ex:previousOwner", type_="@id")
    current_owner: str = Term("ex:currentOwner", type_="@id")
    custody_chain: List[str] = Term("ex:custodyChain", container="@list", type_="@id")
    
    # Transportation and logistics
    transport_method: Optional[str] = Term("ex:transportMethod")
    transport_conditions: List[str] = Term("ex:transportCondition", container="@set")
    carbon_footprint: Optional[float] = Term("ex:carbonFootprint", type_="xsd:decimal")
    
    # Current status and location
    current_status: Literal["in-transit", "in-warehouse", "delivered", "returned"] = Term("ex:currentStatus")
    current_location: Optional[str] = Term("schema:location")
    temperature_controlled: bool = Term("ex:requiresTemperatureControl", type_="xsd:boolean", default=False)
    
    # Sustainability metrics
    recyclable: bool = Term("ex:isRecyclable", type_="xsd:boolean", default=False)
    biodegradable: bool = Term("ex:isBiodegradable", type_="xsd:boolean", default=False)
    sustainability_score: Optional[float] = Term("ex:sustainabilityScore", type_="xsd:decimal")


SupplyChainItem.configure_jsonld(
    base="https://supply-chain.example.com/items/",
    remote_contexts=["https://schema.org/"],
    prefixes={
        "schema": "https://schema.org/",
        "ex": "https://supply-chain.example.com/ontology/",
        "xsd": "http://www.w3.org/2001/XMLSchema#"
    }
)


# =============================================================================
# Demonstration Functions
# =============================================================================

def demonstrate_research_paper():
    """Demonstrate research paper model."""
    print("=" * 60)
    print("RESEARCH PAPER EXAMPLE")
    print("=" * 60)
    
    paper = ResearchPaper(
        doi="10.1000/182",
        title="Advanced Machine Learning Techniques for Climate Prediction",
        abstract="This paper presents novel ML approaches for improved climate modeling...",
        publication_date="2024-03-15",
        journal="Nature Climate Change",
        volume=14,
        issue=3,
        pages="123-135",
        authors=["Dr. Jane Smith", "Dr. Bob Wilson", "Dr. Alice Chen"],
        corresponding_author="https://orcid.org/0000-0000-0000-0001",
        keywords=["machine learning", "climate modeling", "prediction"],
        subject_areas=["Computer Science", "Climate Science"],
        research_field="Artificial Intelligence",
        sections=["Introduction", "Methods", "Results", "Discussion"],
        figures=["fig1.png", "fig2.png"],
        tables=["table1.csv"],
        cites=["10.1000/100", "10.1000/101"],
        cited_by_count=42,
        license="https://creativecommons.org/licenses/by/4.0/",
        is_open_access=True,
        peer_reviewed=True,
        impact_factor=21.5
    )
    
    print("Research Paper JSON (clean for LLM):")
    print(paper.model_dump_json(indent=2)[:500] + "...")
    
    print("\nResearch Paper Context:")
    context = paper.export_context()
    print(str(context)[:500] + "...")
    
    print("\nResearch Paper SHACL Shape:")
    shacl = paper.export_shacl()
    print(str(shacl)[:500] + "...")


def demonstrate_ecommerce_product():
    """Demonstrate e-commerce product model."""
    print("\n" + "=" * 60)
    print("E-COMMERCE PRODUCT EXAMPLE")
    print("=" * 60)
    
    product = Product(
        gtin="123456789012",
        name="Organic Cotton T-Shirt",
        description="Comfortable, sustainable organic cotton t-shirt",
        brand="EcoWear",
        model="ECO-TSHIRT-2024",
        category="Clothing",
        product_type="T-Shirt",
        tags=["organic", "cotton", "sustainable", "comfortable"],
        images=["img1.jpg", "img2.jpg"],
        videos=["video1.mp4"],
        variants=["var1", "var2", "var3"],
        base_price=29.99,
        currency="USD",
        dimensions="L: 70cm, W: 50cm",
        weight=0.2,
        weight_unit="kg",
        average_rating=4.7,
        review_count=156,
        certifications=["GOTS", "Fair Trade"],
        safety_warnings=[],
        eco_friendly=True,
        recycling_info="100% recyclable cotton"
    )
    
    variant = ProductVariant(
        sku="ECO-TSHIRT-2024-M-BLUE",
        color="Blue",
        size="M",
        material="Organic Cotton",
        price=29.99,
        currency="USD",
        availability="InStock"
    )
    
    print("Product JSON (clean for LLM):")
    print(product.model_dump_json(indent=2)[:400] + "...")
    
    print("\nProduct Variant JSON:")
    print(variant.model_dump_json(indent=2))
    
    print("\nProduct Context:")
    print(str(product.export_context())[:400] + "...")


def demonstrate_iot_sensor():
    """Demonstrate IoT sensor reading model."""
    print("\n" + "=" * 60)
    print("IOT SENSOR READING EXAMPLE")
    print("=" * 60)
    
    reading = SensorReading(
        reading_id="reading-12345",
        sensor_id="sensor-temp-001",
        sensor_type="temperature",
        timestamp="2024-07-15T14:30:00Z",
        location_lat=37.7749,
        location_lon=-122.4194,
        location_alt=50.0,
        location_name="San Francisco Office",
        property_measured="air_temperature",
        value=22.5,
        unit="celsius",
        accuracy=0.1,
        confidence=0.95,
        quality_flag="good",
        temperature=22.5,
        humidity=45.0,
        battery_level=0.87,
        signal_strength=-65.0,
        processing_pipeline="standard-v1.2",
        calibration_date="2024-07-01"
    )
    
    print("IoT Sensor Reading JSON (clean for LLM):")
    print(reading.model_dump_json(indent=2))
    
    print("\nIoT Sensor Reading Context:")
    print(str(reading.export_context())[:400] + "...")


def main():
    """Run all demonstrations."""
    print("Pydantic JSON-LD Extended Examples")
    print("==================================")
    print("Demonstrating advanced usage patterns and real-world scenarios")
    
    demonstrate_research_paper()
    demonstrate_ecommerce_product()
    demonstrate_iot_sensor()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ All examples demonstrate:")
    print("  • Clean JSON output for LLM function calling")
    print("  • Rich semantic context export for linked data")
    print("  • SHACL shape generation for validation")
    print("  • Domain-specific vocabularies and patterns")
    print("  • Complex field types and validation")
    print("  • Real-world data modeling scenarios")
    print("\n✅ Package supports diverse domains:")
    print("  • Scientific research and publications")
    print("  • E-commerce and product catalogs")
    print("  • Healthcare and patient records")
    print("  • Financial transactions and compliance")
    print("  • IoT sensor data and monitoring")
    print("  • Education and course management")
    print("  • Supply chain and provenance tracking")


if __name__ == "__main__":
    main()