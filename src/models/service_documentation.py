from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class APIEndpoint(BaseModel):
    endpoint: str
    method: str
    description: str
    auth: str
    input_type: str
    output_type: str

class OutboundAPI(BaseModel):
    called_service: str
    endpoint: str
    purpose: str
    request_type: str
    response_type: str

class DatabaseTable(BaseModel):
    table_name: str
    purpose: str
    columns: List[str]
    db_engine: str
    frequency: str

class KafkaTopic(BaseModel):
    topic_name: str
    payload_example: str
    purpose: str

class ErrorCode(BaseModel):
    code: str
    message: str
    description: str
    resolution: str

class ServiceDependency(BaseModel):
    dependency: str
    purpose: str
    type: str

class ServiceDocumentation(BaseModel):
    """Model representing comprehensive service documentation."""
    # Service Overview
    service_name: str
    primary_function: str
    technology_stack: List[str]
    owner_team: str
    contact: str
    
    # API Information
    inbound_apis: List[APIEndpoint]
    outbound_apis: List[OutboundAPI]
    
    # Database Connectivity
    read_tables: List[DatabaseTable]
    write_tables: List[DatabaseTable]
    
    # Kafka Connectivity
    produced_topics: List[KafkaTopic]
    consumed_topics: List[KafkaTopic]
    
    # Error Information
    error_codes: List[ErrorCode]
    
    # Dependencies
    dependencies: List[ServiceDependency]
    
    # Additional Information
    additional_notes: List[str]
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0" 