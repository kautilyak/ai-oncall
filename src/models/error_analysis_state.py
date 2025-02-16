from typing import List, Optional
from pydantic import BaseModel, Field   


# Incoming Log from DataDog
class LogData(BaseModel):
    trace_id: str = Field(default="unknown")
    message: str = Field(default="")
    timestamp: str = Field(default="")
    service: str = Field(default="unknown")
    error_code: str = Field(default="unknown")
    error_type: str = Field(default="unknown")
    resolution: Optional[str] = Field(default="unknown")


# Input Model for the Error Analysis Graph
class ErrorAnalysisInput(BaseModel):
    error_code: str = Field(description="The error code for the incident")
    error_message: str = Field(..., description="The error message to analyze")
    stack_trace: str = Field(..., description="The associated stack trace")
    trace_id: Optional[str] = Field(None, description="Optional trace ID for fetching related logs")
    related_logs: Optional[List[LogData]] = Field(None, description="List of recent logs")
    api_docs: Optional[str] = Field(None, description="API documentation")


# Output Model for the Error Analysis Graph
class ErrorAnalysisOutput(BaseModel):
    analysis: str = Field(description="Detailed analysis of the error")
    possible_causes: list[str] = Field(description="List of potential causes of the error")
    recommendations: list[str] = Field(description="List of recommended solutions")


