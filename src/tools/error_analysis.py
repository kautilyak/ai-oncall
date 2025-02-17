# src/tools/error_analysis.py

from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

from src.models.error_analysis_state import ErrorAnalysisOutput, ErrorAnalysisInput
from src.tools.vector_store import vector_store
from src.tools.datadog_integration import DatadogLogFetcher

# Initialize the Ollama LLM and DatadogLogFetcher
llm = ChatOllama(model="llama3.2", temperature=0.2)
datadog_fetcher = DatadogLogFetcher()

# Create the output parser using our Pydantic model
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
        "Your response should be a JSON object with the following structure:\n"
        "{{\n"
        '    "analysis": "A detailed analysis of the error",\n'
        '    "possible_causes": ["cause1", "cause2", "cause3"],\n'
        '    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]\n'
        "}}\n\n"
        "Example response:\n"
        "{{\n"
        '    "analysis": "The connection timeout error occurred in the payment service, indicating potential network or service availability issues.",\n'
        '    "possible_causes": ["Database connection pool exhaustion", "Network latency issues", "Service under high load"],\n'
        '    "recommendations": ["Increase connection timeout settings", "Monitor connection pool metrics", "Check network latency between services"]\n'
        "}}\n"
    ),
    input_variables=["error_message", "stack_trace", "service_info", "historical_data", "related_logs"]
)

# Create the analysis chain using LCEL
chain = prompt_template | llm

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
    try:
        # Prepare service information
        service_info = f"Service: {error_analysis_input.service}"
        
        # Search for similar historical errors using hybrid search
        historical_results = vector_store.hybrid_search(
            query=f"{error_analysis_input.error_message}",
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
                f"[{log.timestamp}] {log.service}: {log.message}"
                for log in error_analysis_input.related_logs
            ])
        
        # Run the analysis chain
        result = chain.invoke({
            "error_message": error_analysis_input.error_message,
            "stack_trace": error_analysis_input.stack_trace or "No stack trace available",
            "service_info": service_info,
            "historical_data": historical_data,
            "related_logs": related_logs_text or "No related logs found"
        })  # This will return an AIMessage type
        
        # Get the content from AIMessage
        content = result.content if hasattr(result, 'content') else str(result)
        
        try:
            # Try to parse as JSON
            parsed_json = json.loads(content)
            return ErrorAnalysisOutput(**parsed_json)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to parse JSON: {str(e)}")
            # If JSON parsing fails, try to extract information from the text
            return ErrorAnalysisOutput(
                analysis=content,
                possible_causes=["Unable to parse structured output"],
                recommendations=["Please check the raw analysis above"]
            )
            
    except Exception as e:
        print(f"Error in analyze_error: {str(e)}")
        return ErrorAnalysisOutput(
            analysis=f"Error analyzing the issue: {str(e)}",
            possible_causes=["Error during analysis"],
            recommendations=["Please try again or contact support"]
        )
