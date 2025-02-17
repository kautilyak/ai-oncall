from typing import Optional, List

from langgraph.graph import StateGraph, START, END
from pydantic import Field, BaseModel


from datetime import datetime, timedelta
from src.tools.datadog_integration import DatadogLogFetcher
from src.models.error_analysis_state import ErrorAnalysisInput, ErrorAnalysisOutput
from src.tools.error_analysis import analyze_error

from src.tools.tool_selection import select_tools


class AnalysisState(BaseModel):
    """State model for error analysis workflow."""
    selected_tools: List[str] = Field(default_factory=list, description="List of selected tools")
    error_code: str = Field(description="Error code")
    error_message: str = Field(description="Error message")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace")
    service: Optional[str] = Field(default=None, description="Service name")
    trace_id: Optional[str] = Field(default=None, description="Trace ID")
    related_logs: List[dict] = Field(default_factory=list, description="Related logs")
    service_docs: Optional[dict] = Field(default=None, description="Service documentation")
    analysis_output: Optional[ErrorAnalysisOutput] = Field(default=None)


TASK_DESCRIPTION = """
Analyze error incidents using Datadog logs and service documentation.
"""

# Initialize clients
datadog_client = DatadogLogFetcher()


# Declare all nodes
def tool_selection(state: AnalysisState) -> AnalysisState:
    """Select appropriate tools based on the query"""
    state.selected_tools = select_tools(TASK_DESCRIPTION)
    return state


def gather_datadog_logs(state: AnalysisState) -> AnalysisState:
    """Gather logs from Datadog if selected"""
    if "datadog" in state.selected_tools:
        try:
            # Fetch logs by trace ID if available
            if state.trace_id:
                logs = datadog_client.fetch_logs_by_trace_id(
                    trace_id=state.trace_id,
                    hours=1
                )
                if logs:
                    state.related_logs = [log.dict() for log in logs]
            
            # If no trace ID or no logs found, fetch recent error logs
            if not state.related_logs:
                logs = datadog_client.fetch_past_error_logs_and_store(hours=24)
                if logs:
                    state.related_logs = [log.dict() for log in logs]
                    
            # Extract service name if not provided
            if not state.service and state.related_logs:
                state.service = state.related_logs[0].get('service')
                
        except Exception as e:
            print(f"Error gathering Datadog logs: {e}")
    
    return state


def gather_service_docs(state: AnalysisState) -> AnalysisState:
    """Gather service documentation if selected"""
    pass


def perform_analysis(state: AnalysisState) -> AnalysisState:
    """Perform error analysis"""
    try:
        error_analysis_input = ErrorAnalysisInput(
            error_message=state.error_message,
            stack_trace=state.stack_trace,
            trace_id=state.trace_id,
            service=state.service,
            related_logs=state.related_logs,
            service_docs=state.service_docs
        )
        state.analysis_output = analyze_error(error_analysis_input)
    except Exception as e:
        print(f"Error performing analysis: {e}")
        
    return state


# Define the workflow graph
dd_error_monitoring_workflow = StateGraph(AnalysisState)

# Add nodes to the graph
dd_error_monitoring_workflow.add_node("tool_selection", tool_selection)
dd_error_monitoring_workflow.add_node("gather_datadog", gather_datadog_logs)
dd_error_monitoring_workflow.add_node("gather_service_docs", gather_service_docs)
dd_error_monitoring_workflow.add_node("analysis", perform_analysis)


# Define the edges
dd_error_monitoring_workflow.add_edge(START, "tool_selection")
dd_error_monitoring_workflow.add_edge("tool_selection", "gather_datadog")
dd_error_monitoring_workflow.add_edge("gather_datadog", "gather_service_docs")
dd_error_monitoring_workflow.add_edge("gather_service_docs", "analysis")
dd_error_monitoring_workflow.add_edge("analysis", END)

# Compile the graph
dd_error_workflow = dd_error_monitoring_workflow.compile()
