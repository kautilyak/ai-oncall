from typing import Optional, List

from langgraph.graph import StateGraph, START, END
from pydantic import Field, BaseModel

from src.tools.error_analysis import analyze_error
from src.tools.tool_selection import select_tools
from datetime import datetime, timedelta
from src.tools.datadog_integration import get_all_errors, fetch_past_error_logs, fetch_logs_by_trace_id
from src.models.error_analysis_state import ErrorAnalysisInput, ErrorAnalysisOutput


class AnalysisState(BaseModel):
    selected_tools: List[str] = Field(description="List of selected tools")
    error_code: str = Field(description="Error code")
    error_message: str = Field(description="Error message")
    stack_trace: str = Field(description="Stack trace")
    trace_id: Optional[str] = Field(description="Trace ID")
    related_logs: str = Field(description="Related logs", default=None)
    api_docs: str = Field(description="Business Error Relevant Info / API docs", default=None)
    analysis_output: Optional[ErrorAnalysisOutput] = None


TASK_DESCRIPTION = """
Fetching Datadog Logs and API Docs to resolve the error incident.
"""


# Declare all nodes
def tool_selection(state: AnalysisState) -> AnalysisState:
    """Select appropriate tools based on the query"""
    state.selected_tools = select_tools(TASK_DESCRIPTION)
    return state


def gather_datadog_logs(state: AnalysisState) -> AnalysisState:
    """Gather logs from Datadog if selected"""
    if "datadog" in state.selected_tools:
        to_time = int(datetime.now().timestamp())
        from_time = int((datetime.now() - timedelta(days=1)).timestamp())
        related_logs = fetch_logs_by_trace_id(trace_id=state.trace_id)
        state.recent_logs = related_logs.get('logs', '')
    return state


# todo
def gather_api_docs(state: AnalysisState) -> AnalysisState:
    """Gather API documentation if selected"""
    if "api_docs" in state.selected_tools:
        state.api_docs = "Relevant API documentation content."
    return state


def perform_analysis(state: AnalysisState) -> AnalysisState:
    """Perform error analysis"""
    error_analysis_input = ErrorAnalysisInput(
        error_message=state.error_message,
        stack_trace=state.stack_trace,
        trace_id=state.trace_id,
        related_logs=state.related_logs,
        api_docs=state.api_docs
    )
    state.analysis_output = analyze_error(error_analysis_input)
    return state


# Define the workflow graph
dd_error_monitoring_workflow = StateGraph(AnalysisState)

# Add nodes to the graph
dd_error_monitoring_workflow.add_node("start", START)
dd_error_monitoring_workflow.add_node("tool_selection", tool_selection)
dd_error_monitoring_workflow.add_node("gather_datadog", gather_datadog_logs)
dd_error_monitoring_workflow.add_node("gather_api_docs", gather_api_docs)
dd_error_monitoring_workflow.add_node("analysis", perform_analysis)
dd_error_monitoring_workflow.add_node("end", END)

# Define the edges
dd_error_monitoring_workflow.add_edge(START, "tool_selection")
dd_error_monitoring_workflow.add_edge("tool_selection", "gather_datadog")
dd_error_monitoring_workflow.add_edge("gather_datadog", "gather_api_docs")
dd_error_monitoring_workflow.add_edge("gather_api_docs", "analysis")
dd_error_monitoring_workflow.add_edge("analysis", END)

# Compile the graph
dd_error_workflow = dd_error_monitoring_workflow.compile()
