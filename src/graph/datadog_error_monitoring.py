from src.models.error_analysis_state import AnalysisState   
from langgraph.graph import StateGraph, START, END
from src.tools.tool_selection import select_tools
from src.tools.datadog_integration import gather_datadog_logs, gather_api_docs
from src.tools.error_analysis import perform_analysis  
from datetime import datetime, timedelta

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
        logs_data = fetch_logs_from_datadog(
            query=state.error_message, 
            from_time=from_time, 
            to_time=to_time
        )
        state.recent_logs = logs_data.get('logs', '')
    return state

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
        trace_id=state.trace_id
    )
    state.analysis = analyze_error(error_analysis_input)
    return state


# Compile the graph
dd_error_workflow = dd_error_monitoring_workflow.compile()