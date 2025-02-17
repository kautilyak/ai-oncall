# src/main.py
import argparse
from src.graph.datadog_error_monitoring import dd_error_workflow, AnalysisState
from pydantic import BaseModel, Field
from typing import List, Optional
from src.models.error_analysis_state import ErrorAnalysisOutput
import questionary


class ErrorQuery(BaseModel):
    code: str = Field(..., description="Incoming Error Code")
    message: str = Field(..., description="Incoming Error Message")
    stack_trace: Optional[str] = Field(..., description="Incoming Stack Trace")
    service: Optional[str] = Field(..., description="Incoming Service Name")
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
                                  trace_id=error_query.trace_id if error_query.trace_id is not None else None,
                                  service=error_query.service if error_query.service is not None else None)

    # Run the workflow
    final_state = dd_error_workflow.invoke(initial_state)

    # Output the analysis
    print("Error Analysis and Suggested Resolutions:")
    print(final_state.get("analysis_output"))


if __name__ == "__main__":
    

    # error_code = questionary.text("Please enter the error code:").ask()
    # error_message = questionary.text("Please enter the error message:").ask()
    # stack_trace = questionary.text("Please enter the stack trace (optional):", default="").ask()
    # service = questionary.text("Please enter the service name (optional):", default="").ask()
    # trace_id = questionary.text("Please enter the trace ID for Datadog logs (optional):", default="").ask()
    error_code = "ETIMEDOUT"
    error_message = "Connection timed out"
    stack_trace = "Traceback (most recent call last):\n  File \"network.py\", line 15, in <module>\n    connect_to_service()\n  File \"network.py\", line 8, in connect_to_service\n    raise TimeoutError('Connection timed out')"
    service = "api_service"
    trace_id = "xyz789"

    error_query = ErrorQuery(
        code=error_code,
        message=error_message,
        stack_trace=stack_trace or None,
        service=service or None,
        trace_id=trace_id or None
    )

    process_error(error_query)
