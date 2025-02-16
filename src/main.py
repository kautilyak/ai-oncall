# src/main.py
import argparse
from src.graph.datadog_error_monitoring import dd_error_monitoring_workflow, AnalysisState
from pydantic import BaseModel, Field
from typing import List, Optional
from src.models.error_analysis_state import ErrorAnalysisOutput


class ErrorQuery(BaseModel):
    code: str = Field(..., description="Incoming Error Code")
    message: str = Field(..., description="Incoming Error Message")
    stack_trace: Optional[str] = Field(..., description="Incoming Stack Trace")
    trace_id: Optional[str] = Field(..., description="Incoming Trace ID for Datadog Logs")


def process_error(error_query: ErrorQuery):
    """
    Process the user's query to analyze errors and suggest resolutions.

    Args:
        error_query (ErrorQuery): The input query regarding an error or issue.
    """

    # Initialize state
    initial_state = AnalysisState(error_code=error_query.code,
                                  error_message=error_query.message,
                                  stack_trace=error_query.stack_trace if error_query.stack_trace is not None else None,
                                  trace_id=error_query.trace_id if error_query.trace_id is not None else None)

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
