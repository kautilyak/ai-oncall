# src/main.py

from src.graph.datadog_error_monitoring import dd_error_monitoring_workflow
from pydantic import BaseModel, Field
from typing import List, Optional
from src.models.error_analysis_state import ErrorAnalysisOutput 
from src.models.error_analysis_state import AnalysisState

class ErrorQuery(BaseModel):
    code: str = Field(..., description="Incoming Error Code")
    message: str = Field(..., description="Incoming Error Message")
    stack_trace: str = Field(..., description="Incoming Stack Trace")
    trace_id: str = Field(..., description="Incoming Trace ID for Datadog Logs")


def process_error(error_query: ErrorQuery):
    """
    Process the user's query to analyze errors and suggest resolutions.

    Args:
        user_query (str): The user's input query regarding an error or issue.
    """

    # Initialize state
    initial_state = AnalysisState(error_message=error_query.message, stack_trace=error_query.stack_trace, trace_id=error_query.trace_id)
    
    # Run the workflow
    final_state = dd_error_monitoring_workflow.invoke(initial_state)
    
    # Output the analysis
    print("Error Analysis and Suggested Resolutions:")
    print(final_state.analysis)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Powered Error Log Monitoring System")
    parser.add_argument("query", type=str, help="The error message or query to analyze")
    args = parser.parse_args()

    process_error(args.query)
