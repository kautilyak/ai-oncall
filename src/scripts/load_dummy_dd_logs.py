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
    Load dummy logs into Datadog using the LogData model and store them in the vector database
    for error analysis.
    """
    dummy_logs = [
        LogData(
            trace_id="test-trace-12345",
            message="Database connection failed due to invalid credentials",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:34:56")),
            service="database-service", 
            error_code="500",
            error_type="DatabaseError",
            stack_trace="Error: DatabaseError: Invalid credentials\n    at Database.connect (/src/database.js:123)\n    at processRequest (/src/api/middleware.js:45)",
            host="test-host-1",
            environment="test",
            additional_context={
                "database": "users_db",
                "connection_type": "primary"
            }
        ),
        LogData(
            trace_id="test-trace-67890",
            message="Connection timeout while connecting to database",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:35:10")),
            service="database-service",
            error_code="504",
            error_type="TimeoutError",
            stack_trace="Error: TimeoutError: Connection timed out after 30s\n    at Pool.connect (/src/db/pool.js:89)\n    at ApiHandler.query (/src/handlers/api.js:211)",
            host="test-host-2",
            environment="test",
            additional_context={
                "timeout_ms": "30000",
                "retry_count": "3"
            }
        ),
        LogData(
            trace_id="test-trace-24680",
            message="API rate limit exceeded",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:36:15")),
            service="api-gateway",
            error_code="429",
            error_type="RateLimitError",
            stack_trace="Error: RateLimitError: Too many requests\n    at RateLimiter.check (/src/middleware/rate-limit.js:78)\n    at processRequest (/src/api/gateway.js:156)",
            host="test-host-3",
            environment="test",
            additional_context={
                "limit": "100",
                "window_seconds": "60"
            }
        ),
        LogData(
            trace_id="test-trace-13579", 
            message="Invalid JWT token in authorization header",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:37:20")),
            service="auth-service",
            error_code="401",
            error_type="AuthenticationError",
            stack_trace="Error: AuthenticationError: Invalid token\n    at JwtVerifier.verify (/src/auth/jwt.js:45)\n    at AuthMiddleware.authenticate (/src/middleware/auth.js:23)",
            host="test-host-4",
            environment="test",
            additional_context={
                "token_type": "access",
                "auth_source": "bearer"
            }
        ),
        LogData(
            trace_id="test-trace-97531",
            message="Failed to process payment: Invalid card number",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:38:25")),
            service="payment-service",
            error_code="400",
            error_type="PaymentValidationError", 
            stack_trace="Error: PaymentValidationError: Invalid card number\n    at PaymentProcessor.validate (/src/payments/processor.js:167)\n    at PaymentHandler.process (/src/handlers/payment.js:89)",
            host="test-host-5",
            environment="test",
            additional_context={
                "payment_provider": "stripe",
                "currency": "USD"
            }
        ),
        LogData(
            trace_id="test-trace-35791",
            message="Memory allocation failed during image processing",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:39:30")),
            service="image-service",
            error_code="507",
            error_type="OutOfMemoryError",
            stack_trace="Error: OutOfMemoryError: Failed to allocate 2GB\n    at ImageProcessor.resize (/src/services/image.js:234)\n    at BatchProcessor.process (/src/batch/processor.js:78)",
            host="test-host-6",
            environment="test",
            additional_context={
                "requested_memory": "2GB",
                "available_memory": "512MB"
            }
        ),
        LogData(
            trace_id="test-trace-46802",
            message="Failed to connect to Redis cache server",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:40:35")),
            service="cache-service",
            error_code="503",
            error_type="ConnectionError",
            stack_trace="Error: ConnectionError: Redis server unreachable\n    at RedisClient.connect (/src/cache/redis.js:156)\n    at CacheManager.initialize (/src/managers/cache.js:45)",
            host="test-host-7",
            environment="test",
            additional_context={
                "redis_host": "cache-1.example.com",
                "port": "6379"
            }
        ),
        LogData(
            trace_id="test-trace-58913",
            message="Invalid GraphQL query syntax",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:41:40")),
            service="graphql-api",
            error_code="400",
            error_type="GraphQLSyntaxError",
            stack_trace="Error: GraphQLSyntaxError: Expected Name, found <EOF>\n    at Parser.parse (/src/graphql/parser.js:89)\n    at QueryValidator.validate (/src/validators/query.js:123)",
            host="test-host-8",
            environment="test",
            additional_context={
                "query_id": "abc123",
                "operation_name": "GetUserProfile"
            }
        ),
        LogData(
            trace_id="test-trace-69024",
            message="Kafka consumer group rebalancing failed",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:42:45")),
            service="streaming-service",
            error_code="500",
            error_type="KafkaError",
            stack_trace="Error: KafkaError: Consumer group rebalance timeout\n    at ConsumerGroup.join (/src/kafka/consumer.js:278)\n    at MessageProcessor.start (/src/processors/message.js:67)",
            host="test-host-9",
            environment="test",
            additional_context={
                "consumer_group": "order-processors",
                "partition_count": "12"
            }
        ),
        LogData(
            trace_id="test-trace-70135",
            message="S3 bucket permission denied during file upload",
            timestamp=str(datetime.fromisoformat("2024-02-15T12:43:50")),
            service="storage-service",
            error_code="403",
            error_type="AccessDeniedError",
            stack_trace="Error: AccessDeniedError: Access Denied to bucket 'user-uploads'\n    at S3Client.putObject (/src/aws/s3.js:145)\n    at FileUploader.upload (/src/services/uploader.js:89)",
            host="test-host-10",
            environment="test",
            additional_context={
                "bucket_name": "user-uploads",
                "file_size": "15MB"
            }
        )
    ]

    # First submit logs to Datadog
    with ApiClient(datadog_config) as api_client:
        api_instance = LogsApi(api_client)
        try:
            for log in dummy_logs:
                # Convert to Datadog log format
                log_entry = HTTPLogItem(
                    ddtags=f"service:{log.service},trace_id:{log.trace_id},env:{log.environment}",
                    hostname=log.host,
                    message=log.message,
                    service=log.service,
                    status="error",
                    timestamp=int(datetime.now().timestamp() * 1000),  # Unix time in milliseconds
                    attributes={
                        "error": {
                            "code": log.error_code,
                            "type": log.error_type,
                            "stack": log.stack_trace
                        },
                        "trace_id": log.trace_id,
                        "env": log.environment,
                        **log.additional_context
                    }
                )            
                response = api_instance.submit_log(body=[log_entry])
                print(f"Log submitted successfully to Datadog: {log.trace_id}")

            # Store logs in vector database for analysis
            from src.tools.vector_store import vector_store
            vector_store.store_vectors(dummy_logs)
            print("Logs stored in vector database for analysis")
                
        except Exception as e:
            print(f"Error submitting/storing logs: {e}")

if __name__ == "__main__":
    load_dummy_logs()
