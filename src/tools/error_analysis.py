# src/tools/error_analysis.py

from langchain_ollama import ChatOllama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from typing import List, Dict, Optional
from src.tools.vector_store import search_logs
from src.tools.datadog_integration import fetch_logs_by_trace_id, get_all_errors
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from src.models.error_analysis_state import ErrorAnalysisOutput, ErrorAnalysisInput, ErrorAnalysisData


# Initialize the OpenAI LLM
llm = ChatOllama(model_name="llama3.2", temperature=0.2)

# Create the output parser
output_parser = PydanticOutputParser(pydantic_object=ErrorAnalysisOutput)

# Define the prompt template for error analysis
prompt_template = PromptTemplate(
    template=(
        "You are an AI assistant specialized in system error analysis.\n\n"
        "Error Message:\n{error_message}\n\n"
        "Stack Trace:\n{stack_trace}\n\n"
        "Historical Data:\n{historical_data}\n\n"
        "Recent Logs:\n{recent_logs}\n\n"
        "API Documentation:\n{api_docs}\n\n"
        "Based on the above information, provide a detailed analysis of the error.\n\n"
        "{format_instructions}\n"
    ),
    input_variables=["error_message", "stack_trace", "historical_data", "recent_logs", "api_docs"],
    partial_variables={"format_instructions": output_parser.get_format_instructions()}
)

# Create the LLMChain with the output parser
error_analysis_chain = LLMChain(
    llm=llm,
    prompt=prompt_template,
    output_parser=output_parser
)

def analyze_error(error_analysis_input: ErrorAnalysisInput) -> ErrorAnalysisOutput:
    """
    Analyze an error using the LLM and provide insights and resolution suggestions.

    Args:
        error_message (str): The error message to analyze.
        stack_trace (str): The associated stack trace.
        trace_id (str, optional): The trace ID for fetching related logs. Defaults to None.

    Returns:
        str: The analysis and suggested resolution.
    """

    # Retrieve historical data from the vector store
    historical_data_docs = search_logs(query=error_analysis_input.error_message, k=5)
    historical_data = "\n\n".join([doc.page_content for doc in historical_data_docs])

    # Fetch recent logs from Datadog
    if error_analysis_input.trace_id:
        trace_data = fetch_logs_by_trace_id(error_analysis_input.trace_id)
        recent_logs = trace_data.get('logs', '')
    else:
        # Define a time range for recent logs (e.g., last 24 hours)
        to_time = int(datetime.now().timestamp())
        from_time = int((datetime.now() - timedelta(days=1)).timestamp())
        logs_data = get_all_errors(from_time, to_time)
        recent_logs = logs_data.get('logs', '')

    # Placeholder for API documentation retrieval
    api_docs = "Relevant API documentation content."

    # Validate analysis data using Pydantic model
    analysis_data = ErrorAnalysisData(
        error_message=error_analysis_input.error_message,
        stack_trace=error_analysis_input.stack_trace,
        historical_data=historical_data,
        recent_logs=recent_logs if recent_logs else logs_data,
        api_docs=api_docs
    )

    # Run the error analysis chain
    analysis = error_analysis_chain.invoke(
        error_message=analysis_data.error_message,
        stack_trace=analysis_data.stack_trace,
        historical_data=analysis_data.historical_data,
        recent_logs=analysis_data.recent_logs,
        api_docs=analysis_data.api_docs
    )

    return analysis
