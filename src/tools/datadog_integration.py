# src/tools/datadog_integration.py

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.models import LogsSort, LogsListRequest, LogsQueryFilter
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from src.config import datadog_config
from src.models.error_analysis_state import LogData
from src.tools.vector_store import vector_store


class DatadogLogFetcher:
    def __init__(self, config=datadog_config):
        self.config = config


    def fetch_logs_by_trace_id(self, trace_id: str, hours: int = 1) -> List[LogData]:
        """Fetch logs associated with a specific trace ID from Datadog."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return self._execute_query(f"@trace_id:{trace_id}", start_time)



    def fetch_past_error_logs_and_store(self, hours: int = 24) -> List[LogData]:
        """
        Fetch past error logs from Datadog and store them in Pinecone.
        
        This method:
        1. Fetches error logs from Datadog
        2. Enriches them with additional context
        3. Stores them in the vector database with proper chunking
        4. Each log entry is split into multiple chunks for better semantic search
        5. Maintains metadata for filtering and resolution tracking
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        logs: List[LogData] = self._execute_query("@status:error", start_time)
        
        if logs:
            # Store in vector database with proper chunking and metadata
            vector_store.store_vectors(logs)
        
        return logs
    


    def _execute_query(self, query: str, start_time: datetime, end_time: Optional[datetime] = None) -> List[LogData]:
        """Execute a logs query and return LogData objects."""
        end_time = end_time or datetime.utcnow()
        
        try:
            with ApiClient(self.config) as api_client:
                api_instance = LogsApi(api_client)
                filter = LogsQueryFilter(
                    query=query,
                    _from=start_time.isoformat() + "Z",
                    to=end_time.isoformat() + "Z"
                )
                response = api_instance.list_logs(
                    body=LogsListRequest(
                        filter=filter,
                        sort=LogsSort("timestamp")
                    )
                )
                return [
                    LogData(
                        trace_id=log.attributes.get("trace_id", "unknown"),
                        message=log.attributes.get("message", ""),
                        timestamp=log.attributes.get("timestamp", ""),
                        service=log.attributes.get("service", "unknown"),
                        error_code=log.attributes.get("error.code", "unknown"),
                        error_type=log.attributes.get("error.type", "unknown"),
                        stack_trace=log.attributes.get("error.stack", ""),
                        host=log.attributes.get("host", "unknown"),
                        environment=log.attributes.get("env", "unknown"),
                        additional_context=self._extract_additional_context(log.attributes)
                    ) 
                    for log in response.data
                ]
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []

    def _extract_additional_context(self, attributes: Dict) -> Dict:
        """Extract additional context from log attributes that might be useful for error analysis."""
        context = {}
        
        # Extract any custom tags
        for key, value in attributes.items():
            if key.startswith("custom.") or key.startswith("usr."):
                context[key] = value
        
        # Extract request context if available
        if "http.url" in attributes:
            context["http_url"] = attributes["http.url"]
        if "http.method" in attributes:
            context["http_method"] = attributes["http.method"]
        if "http.status_code" in attributes:
            context["http_status_code"] = attributes["http.status_code"]
            
        return context

    