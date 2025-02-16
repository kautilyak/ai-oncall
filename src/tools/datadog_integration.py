# src/tools/datadog_integration.py

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.models import LogsSort, LogsListRequest, LogsQueryFilter
from datetime import datetime, timedelta

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
