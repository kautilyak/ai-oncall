# src/tools/datadog_integration.py

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.models import LogsSort, LogsListRequest, LogsQueryFilter
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Optional

# get all errors for a time range
def get_all_errors(start_time: datetime, end_time: datetime):
    """
    Get all errors for a given time range from Datadog.

    Args:
        start_time (datetime): The start time of the time range.
        end_time (datetime): The end time of the time range.

    Returns:
        list: A list of errors for the given time range.
    """ 
    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_instance = LogsApi(api_client)

        # Define the time range for the query
        now = datetime.utcnow() 

        # Create the filter for the query
        filter = LogsQueryFilter(
            query=f'@error',
            _from=start_time.isoformat() + "Z",
            to=now.isoformat() + "Z"
        )   

        # Create the request
        request = LogsListRequest(
            filter=filter,
            sort=LogsSort("timestamp")
        )

        try:
            # Execute the search
            response = api_instance.list_logs(body=request)
            return response.data
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []






def fetch_past_error_logs(self, hours: int = 24) -> list[LogData]:
        """
        Fetch past error logs from Datadog and store them in Pinecone.
        """
        with ApiClient(self.configuration) as api_client:
            api_instance = LogsApi(api_client)
            now = datetime.utcnow()
            start_time = now - timedelta(hours=hours)
            filter = LogsQueryFilter(query='@status:error', _from=start_time.isoformat() + "Z", to=now.isoformat() + "Z")
            request = LogsListRequest(filter=filter, sort=LogsSort("timestamp"))
            
            try:
                response = api_instance.list_logs(body=request)
                logs = response.data
                
                for log in logs:
                    log_data = LogData(
                        trace_id=log.attributes.get("trace_id", "unknown"),
                        message=log.attributes.get("message", ""),
                        timestamp=log.attributes.get("timestamp", ""),
                        service=log.attributes.get("service", "unknown"),
                        error_code=log.attributes.get("error.code", "unknown"),
                        error_type=log.attributes.get("error.type", "unknown")
                    )
                    store_vector(log_data.dict())
                
                return logs
            except Exception as e:
                print(f"Error fetching logs: {e}")
                return []

def fetch_logs_by_trace_id(trace_id: str, hours: int = 1):
    """
    Fetch logs associated with a specific trace ID from Datadog.

    Args:
        trace_id (str): The trace ID to search for.
        hours (int): The time range in hours to look back from the current time.

    Returns:
        list: A list of logs associated with the trace ID.
    """
    configuration = Configuration()
    with ApiClient(configuration) as api_client:
        api_instance = LogsApi(api_client)

        # Define the time range for the query
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours)

        # Create the filter for the query
        filter = LogsQueryFilter(
            query=f'@trace_id:{trace_id}',
            _from=start_time.isoformat() + "Z",
            to=now.isoformat() + "Z"
        )

        # Create the request
        request = LogsListRequest(
            filter=filter,
            sort=LogsSort("timestamp")
        )

        try:
            # Execute the search
            response = api_instance.list_logs(body=request)
            return response.data
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
