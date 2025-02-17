# src/tools/error_analysis.py

from langchain_ollama import ChatOllama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser

from src.models.error_analysis_state import ErrorAnalysisOutput, ErrorAnalysisInput
from src.tools.vector_store import vector_store
from src.tools.datadog_integration import DatadogLogFetcher

# Initialize the Ollama LLM and DatadogLogFetcher
llm = ChatOllama(model="llama3.2", temperature=0.2)
datadog_fetcher = DatadogLogFetcher()

# Create the output parser
output_parser = PydanticOutputParser(pydantic_object=ErrorAnalysisOutput)

# Define the prompt template for error analysis
prompt_template = PromptTemplate(
    template=(
        "You are an AI assistant specialized in system error analysis.\n\n"
        "Error Message:\n{error_message}\n\n"
        "Stack Trace:\n{stack_trace}\n\n"
        "Service Information:\n{service_info}\n\n"
        "Historical Similar Errors:\n{historical_data}\n\n"
        "Related Trace Logs:\n{related_logs}\n\n"
        "Based on the above information, provide a detailed analysis of the error.\n"
        "Consider patterns in historical errors and the current service context.\n\n"
        "{format_instructions}\n"
    ),
    input_variables=["error_message", "stack_trace", "service_info", "historical_data", "related_logs"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

# Create the analysis chain using LCEL
error_analysis_chain = prompt_template | llm | output_parser

def format_historical_data(historical_results: List[Dict]) -> str:
    """Format historical error data for the prompt."""
    formatted_data = []
    for result in historical_results:
        status = f"[{result.get('resolution_status', 'pending').upper()}]"
        resolution = f"Resolution: {result.get('resolution_notes', 'No resolution notes yet')}"
        error_info = f"Error: {result.get('error_type')} in {result.get('service')}"
        timestamp = f"Occurred: {result.get('timestamp')}"
        
        formatted_data.append(f"{status}\n{error_info}\n{timestamp}\n{resolution}\n")
    
    return "\n".join(formatted_data) if formatted_data else "No historical data available."

def analyze_error(error_analysis_input: ErrorAnalysisInput) -> ErrorAnalysisOutput:
    """
    Analyze an error using the LLM and provide insights and resolution suggestions.
    
    This function:
    1. Retrieves similar historical errors using hybrid search
    2. Fetches related logs from the same trace
    3. Combines all information for LLM analysis
    4. Returns structured analysis output
    
    Args:
        error_analysis_input (ErrorAnalysisInput): Details about the error to analyze
        
    Returns:
        ErrorAnalysisOutput: Structured analysis including root cause and resolution steps
    """
    # Prepare service information
    service_info = f"Service: {error_analysis_input.service}\nEnvironment: {error_analysis_input.environment}"
    
    # Search for similar historical errors using hybrid search
    historical_results = vector_store.hybrid_search(
        query=f"{error_analysis_input.error_type} {error_analysis_input.error_message}",
        metadata_filter={
            "service": error_analysis_input.service
        } if error_analysis_input.service else None,
        k=5
    )
    
    # Format historical data
    historical_data = format_historical_data(historical_results)
    
    # Format related logs
    related_logs_text = ""
    if error_analysis_input.related_logs:
        related_logs_text = "\n".join([
            f"[{log.get('timestamp', 'unknown')}] {log.get('service', 'unknown')}: {log.get('message', '')}"
            for log in error_analysis_input.related_logs
        ])
    
    # Run the error analysis chain
    result = error_analysis_chain.invoke({
        "error_message": error_analysis_input.error_message,
        "stack_trace": error_analysis_input.stack_trace or "No stack trace available",
        "service_info": service_info,
        "historical_data": historical_data,
        "related_logs": related_logs_text or "No related logs found"
    })
    
    return result
