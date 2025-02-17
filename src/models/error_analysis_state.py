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
    stack_trace: str = Field(default="unknown")
    host: str = Field(default="unknown")
    environment: str = Field(default="unknown")
    additional_context: dict = Field(default_factory=dict)
    resolution: Optional[str] = Field(default="unknown")


# Input Model for the Error Analysis Graph
class ErrorAnalysisInput(BaseModel):
    error_code: str = Field(description="The error code for the incident")
    error_message: str = Field(..., description="The error message to analyze")
    stack_trace: Optional[str] = Field(None, description="The associated stack trace")
    trace_id: Optional[str] = Field(None, description="Optional trace ID for fetching related logs")
    service: Optional[str] = Field(None, description="Service name")
    related_logs: Optional[List[LogData]] = Field(None, description="List of recent logs")
    service_docs: Optional[dict] = Field(None, description="Service documentation")


# Output Model for the Error Analysis Graph
class ErrorAnalysisOutput(BaseModel):
    """Model for structured error analysis output."""
    analysis: str = Field(
        default="",
        description="Detailed analysis of the error, including context and impact"
    )
    possible_causes: List[str] = Field(
        default_factory=list,
        description="List of potential root causes for the error"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommended actions to resolve the error"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "analysis": "The connection timeout error occurred in the payment service, indicating potential network or service availability issues.",
                    "possible_causes": [
                        "Database connection pool exhaustion",
                        "Network latency issues",
                        "Service under high load"
                    ],
                    "recommendations": [
                        "Increase connection timeout settings",
                        "Monitor connection pool metrics",
                        "Check network latency between services"
                    ]
                }
            ]
        }
    }


