# create a script that will pull datadog logs from datadog using the client in python 
# use these logs to ingest LogData type data into pinecone vector db 

from tools.datadog_integration import get_all_errors, fetch_logs_by_trace_id, fetch_past_error_logs_and_store
from pinecone import Pinecone
from pinecone.grpc import GrpcIndex


