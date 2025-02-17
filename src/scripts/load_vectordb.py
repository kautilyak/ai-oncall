# create a script that will pull datadog logs from datadog using the client in python
# use these logs to ingest LogData type data into pinecone vector database




from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import ddtrace
from ..tools.datadog_integration import DatadogLogFetcher

load_dotenv()
ddtrace.patch(logging=True)

def load_logs_to_vectordb():
    """
    Fetch error logs from Datadog and store them in the vector database.
    This function:
    1. Fetches error logs from the past 24 hours
    2. Converts them to LogData format
    3. Stores them in Pinecone vector database for analysis
    """
    try:
        datadog_fetcher = DatadogLogFetcher()
        # Fetch and store logs from the past 24 hours
        logs = datadog_fetcher.fetch_past_error_logs_and_store(hours=5)
        
        if logs:
            print(f"Successfully loaded {len(logs)} logs into vector database")
        else:
            print("No logs found in the specified time period")
            
    except Exception as e:
        print(f"Error loading logs into vector database: {e}")

if __name__ == "__main__":
    load_logs_to_vectordb()






