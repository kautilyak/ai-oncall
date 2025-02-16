import requests
import json

from datadog_api_client.v2.model.http_log import HTTPLog
from datadog_api_client.v2.model.http_log_item import HTTPLogItem
from dotenv import load_dotenv
import ddtrace
load_dotenv()

from datadog_api_client import ApiClient
from datadog_api_client.v2.api.logs_api import LogsApi
from src.config import datadog_config
from src.models.error_analysis_state import LogData
from datetime import datetime
import logging

ddtrace.patch(logging=True)
def load_dummy_logs():
    """
    Load dummy logs into Datadog using the LogData model
    """
    dummy_logs = [
        LogData(
            trace_id="test-trace-12345",
            message="Database connection failed due to invalid credentials",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:34:56")),
            service="database-service",
            error_code="500",
            error_type="DatabaseError",
            resolution="Check and update database credentials in environment variables"
        ),
        LogData(
            trace_id="test-trace-67890",
            message="Connection timeout while connecting to database",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:35:10")),
            service="database-service",
            error_code="504",
            error_type="TimeoutError",
            resolution="Verify database connection settings and network stability"
        ),
        LogData(
            trace_id="test-trace-24680",
            message="API rate limit exceeded",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:36:15")),
            service="api-gateway",
            error_code="429",
            error_type="RateLimitError",
            resolution="Implement rate limiting or request throttling"
        ),
        LogData(
            trace_id="test-trace-13579",
            message="Invalid JWT token in authorization header",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:37:20")),
            service="auth-service",
            error_code="401",
            error_type="AuthenticationError",
            resolution="Verify token generation and expiration settings"
        ),
        LogData(
            trace_id="test-trace-97531",
            message="Failed to process payment: Invalid card number",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:38:25")),
            service="payment-service",
            error_code="400",
            error_type="PaymentValidationError",
            resolution="Validate card number format before processing"
        ),
        LogData(
            trace_id="test-trace-86420",
            message="Memory limit exceeded in container",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:39:30")),
            service="processing-service",
            error_code="507",
            error_type="ResourceExhaustedError",
            resolution="Increase container memory limits or optimize resource usage"
        ),
        LogData(
            trace_id="test-trace-11111",
            message="Failed to connect to Redis cache",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:40:35")),
            service="cache-service",
            error_code="503",
            error_type="CacheConnectionError",
            resolution="Check Redis connection settings and service health"
        ),
        LogData(
            trace_id="test-trace-22222",
            message="Malformed JSON in request body",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:41:40")),
            service="api-gateway",
            error_code="400",
            error_type="ValidationError",
            resolution="Validate JSON format before processing request"
        ),
        LogData(
            trace_id="test-trace-33333",
            message="Database deadlock detected",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:42:45")),
            service="database-service",
            error_code="500",
            error_type="DeadlockError",
            resolution="Implement retry logic with exponential backoff"
        ),
        LogData(
            trace_id="test-trace-44444",
            message="Failed to send email notification",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:43:50")),
            service="notification-service",
            error_code="502",
            error_type="EmailDeliveryError",
            resolution="Verify SMTP settings and email service availability"
        )
    ]

    with ApiClient(datadog_config) as api_client:
        api_instance = LogsApi(api_client)
        logging.error("err")
        try:
            for log in dummy_logs:
                # Convert to Datadog log format
                log_entry = HTTPLogItem(
                    ddtags=f"service:{log.service},trace_id:{log.trace_id}",
                    hostname="test-host",
                    message=log.message,
                    service=log.service,
                    status="error",
                    timestamp=int(datetime.now().timestamp() * 1000),  # Unix time in milliseconds
                    attributes={
                        "error": {
                            "code": log.error_code,
                            "type": log.error_type
                        },
                        "resolution": log.resolution,
                        "trace_id": log.trace_id
                    }
                
                )            
                response = api_instance.submit_log(body=[log_entry])
                print(f"Log submitted successfully: {log.trace_id}")
                
        except Exception as e:
            print(f"Error submitting logs: {e}")

if __name__ == "__main__":
    load_dummy_logs()
