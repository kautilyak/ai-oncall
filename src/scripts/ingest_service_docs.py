import logging
from pathlib import Path
from typing import List, Dict, Optional
import yaml
import re
from datetime import datetime

from src.models.service_documentation import ServiceDocumentation
from src.tools.vector_store import vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownTextSplitter

def ingest_service_docs(docs_dir: str):
    """
    Ingest service documentation from markdown files into the vector store.
    
    Args:
        docs_dir: Directory containing service documentation markdown files
    """
    try:
        path = Path(docs_dir)
        for file_path in path.glob("**/*.md"):
            logger.info(f"Processing {file_path}")
            
            # Load markdown using Langchain
            loader = UnstructuredMarkdownLoader(str(file_path))
            docs = loader.load()
            
            # Split into chunks
            splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(docs)
            
            # Convert to LogData format
            # Convert chunks to ServiceDocumentation format
            service_docs = []
            for chunk in chunks:
                service_docs.append(ServiceDocumentation(
                    service_name=file_path.stem,
                    primary_function=chunk.page_content,
                    technology_stack=[],
                    owner_team="",
                    contact="",
                    inbound_apis=[],
                    outbound_apis=[],
                    read_tables=[],
                    write_tables=[],
                    produced_topics=[],
                    consumed_topics=[],
                    error_codes=[],
                    dependencies=[],
                    additional_notes=[],
                    last_updated=datetime.utcnow(),
                    version="1.0"
                ))
            
            # Store in vector database
            vector_store.store_vectors(service_docs)
            logger.info(f"Successfully ingested documentation for {file_path.stem}")
            
    except Exception as e:
        logger.error(f"Error ingesting service documentation: {e}")

if __name__ == "__main__":
    DOCS_DIR = "service_docs"
    ingest_service_docs(DOCS_DIR)