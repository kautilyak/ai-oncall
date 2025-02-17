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
                        trace_id=str(log.attributes.get("trace_id")) if hasattr(log, 'attributes') else "unknown",
                        message=str(log.attributes.get("message")) if hasattr(log, 'attributes') else "",
                        timestamp=str(log.attributes.get("timestamp")) if hasattr(log, 'attributes') else "",
                        service=str(log.attributes.get("service", "unknown")) if hasattr(log, 'attributes') else "unknown",
                        error_code=str(log.attributes.get("error.code")) if hasattr(log, 'attributes') else "unknown",
                        error_type=str(log.attributes.get("error.type")) if hasattr(log, 'attributes') else "unknown",
                        stack_trace=str(log.attributes.get("error.stack")) if hasattr(log, 'attributes') else "",
                        host=str(log.attributes.get("hostname")) if hasattr(log, 'attributes') else "unknown",
                        environment=str(log.attributes.get("env")) if hasattr(log, 'attributes') else "unknown",
                        # additional_context=self._extract_additional_context(log.attributes) if hasattr(log, 'attributes') else {}
                    )
                    for log in (response.data if hasattr(response, 'data') else [])
                ]
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []

    def _extract_additional_context(self, attributes) -> Dict:
        """Extract additional context from log attributes that might be useful for error analysis."""
        context = {}
        
        if not attributes:
            return context
            
        # Extract any custom tags
        try:
            # Handle attributes as a LogAttributes object
            for key in dir(attributes):
                if key.startswith("custom_") or key.startswith("usr_"):
                    value = getattr(attributes, key)
                    context[key] = value
            
            # Extract request context if available
            http_fields = ["http_url", "http_method", "http_status_code"] 
            for field in http_fields:
                if hasattr(attributes, field):
                    context[field] = getattr(attributes, field)
                    
        except Exception as e:
            print(f"Error extracting additional context: {e}")
            
        return context

    