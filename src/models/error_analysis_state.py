from typing import List, Optional
from pydantic import BaseModel, Field   

class AnalysisState(BaseModel): 
    selected_tools: List[str] = Field(default_factory=list)
    error_message: str = ""
    stack_trace: str = ""
    trace_id: Optional[str] = None
    recent_logs: str = ""
    api_docs: str = ""
    analysis: Optional[str] = None
    analysis_output: Optional[ErrorAnalysisOutput] = None

class ErrorAnalysisInput(BaseModel):
    error_message: str = Field(..., description="The error message to analyze")
    stack_trace: str = Field(..., description="The associated stack trace")
    trace_id: Optional[str] = Field(None, description="Optional trace ID for fetching related logs")

class ErrorAnalysisData(BaseModel):
    error_message: str
    stack_trace: str
    historical_data: str
    recent_logs: str 
    api_docs: str

class ErrorAnalysisOutput(BaseModel):
    analysis: str = Field(description="Detailed analysis of the error")
    possible_causes: list[str] = Field(description="List of potential causes of the error")
    recommendations: list[str] = Field(description="List of recommended solutions")