from datadog_api_client import Configuration
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Datadog Configuration
datadog_config = Configuration(
    api_key={
        'apiKeyAuth': os.getenv('DATADOG_API_KEY'),  # Datadog API key from env
        'appKeyAuth': os.getenv('DATADOG_APP_KEY')   # Datadog application key from env
    }
)

# Pinecone Configuration
class PineconeConfig(BaseModel):
    """Configuration for Pinecone vector database."""
    api_key: str
    environment: str
    index_name: str = "error-logs",
    host: str

pinecone_config = PineconeConfig(
    api_key=os.getenv('PINECONE_API_KEY'),
    environment=os.getenv('PINECONE_ENVIRONMENT'),
    index_name=os.getenv('PINECONE_INDEX_NAME', 'error-logs'),
    host=os.getenv('PINECONE_HOST')
)