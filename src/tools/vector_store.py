import os
from typing import Dict, List, Optional, Union
import pinecone
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from datetime import datetime
import hashlib
import json

from src.config import pinecone_config
from src.models.error_analysis_state import LogData


class VectorStore:
    def __init__(self, index_name: str = "datadoglogs"):
        # Initialize Pinecone client
        # Initialize Pinecone client and create index if needed
        pinecone_client = pinecone.Pinecone(
            api_key=pinecone_config.api_key,
            # environment=pinecone_config.environment,
            host=pinecone_config.host,
        )

        self.pc_index = pinecone_client.Index(index_name, host=pinecone_config.host)
        
        # if index_name not in [index.name for index in pinecone_client.list_indexes()]:
        #     pinecone_client.create_index(
        #         name=index_name,
        #         dimension=4096,  # Ollama's llama embedding dimension
        #         metric="cosine"
        #     )
        
        # Initialize embeddings and vector store
        self.embeddings = PineconeEmbeddings(model="multilingual-e5-large")
        self.vectorstore = PineconeVectorStore(index=self.pc_index, embedding=self.embeddings)

    def _generate_vector_id(self, log: Dict) -> str:
        """Generate a unique, deterministic ID for a log entry."""
        # Create a unique identifier using relevant fields
        unique_fields = {
            'trace_id': log.get('trace_id'),
            'timestamp': log.get('timestamp'),
            'error_type': log.get('error_type'),
            'service': log.get('service')
        }
        return hashlib.sha256(json.dumps(unique_fields, sort_keys=True).encode()).hexdigest()

    def _prepare_chunks(self, log: Dict) -> List[Dict]:
        """Prepare chunks from a single log entry for vectorization.
        
        This method implements a strategic chunking approach for error logs:
        
        1. Error Description Chunk: Combines error type and message to enable searching 
           by error characteristics and natural language descriptions
        
        2. Service Context Chunk: Groups service and error code information to support
           queries about specific services or error patterns
           
        3. Stack Trace Chunk (Optional): Stores stack trace separately since it contains
           detailed technical information that should be searchable independently
           
        This chunking strategy enables:
        - More precise semantic search by separating different aspects of the error
        - Better relevance scoring since related information is grouped together
        - Flexible querying across different error aspects (e.g. find similar errors
          vs find errors in a specific service)

        Example queries this structure helps solve:
        - "Find all errors with 'ETIMEDOUT' or 'ConnectTimeoutError' across payment-service and auth-service"
        - "Show me errors with stack traces containing 'ReferenceError: user is not defined' in the last 24 hours"
        - "What are the most frequent SQL constraint violations in the user-management-service?"
        - "Find errors containing 'Could not connect to PostgreSQL database' or 'connection refused' in the error message"
        - "Show me all errors where stack trace contains 'users.email' or 'UserModel.findOne' from the database service"
        
        Args:
            log (Dict): Log entry containing error information
            
        Returns:
            List[Dict]: List of chunks, each with 'text' content and 'chunk_type'
        """
        chunks = []
        
        # Create different chunks for different aspects of the error
        chunks.extend([
            {
                'text': f"Error Type: {log['error_type']} - Message: {log['message']}",
                'chunk_type': 'error_description'
            },
            {
                'text': f"Service: {log['service']} - Error Code: {log['error_code']}",
                'chunk_type': 'service_context'
            }
        ])
        
        # Add stack trace chunk if available
        if 'stack_trace' in log:
            chunks.append({
                'text': f"Stack Trace: {log['stack_trace']}",
                'chunk_type': 'stack_trace'
            })
        
        return chunks

    def store_vectors(self, logs: List[LogData]) -> None:
        """Store log vectors in Pinecone with proper chunking and metadata."""
        texts = []
        metadatas = []
        ids = []
        
        for log in logs:
            vector_id_base = self._generate_vector_id(log.dict())
            chunks = self._prepare_chunks(log.dict())
            
            for i, chunk in enumerate(chunks):
                # Create a unique ID for each chunk
                chunk_id = f"{vector_id_base}_{i}"
                
                # Prepare metadata with searchable fields and resolution tracking
                metadata = {
                    'vector_id': vector_id_base,
                    'chunk_id': chunk_id,
                    'chunk_type': chunk['chunk_type'],
                    'trace_id': log.trace_id,
                    'service': log.service,
                    'error_type': log.error_type,
                    'error_code': log.error_code,
                    'timestamp': log.timestamp,
                    'resolution_status': 'pending',  # Can be: pending, in_progress, resolved
                    'resolution_notes': '',
                    'resolution_timestamp': '',
                    'stored_at': datetime.utcnow().isoformat()
                }
                
                texts.append(chunk['text'])
                metadatas.append(metadata)
                ids.append(chunk_id)
        
        # Add texts and metadata to Pinecone
        self.vectorstore.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )

    def hybrid_search(self, 
                     query: str, 
                     metadata_filter: Optional[Dict] = None,
                     k: int = 5) -> List[Dict]:
        """
        Perform hybrid search combining semantic similarity with metadata filtering.
        
        Args:
            query: The search query for semantic similarity
            metadata_filter: Dictionary of metadata fields to filter on
            k: Number of results to return
        """
        filter = {}
        if metadata_filter:
            filter = metadata_filter
            
        results = self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
        return [doc.metadata for doc in results]

    def update_resolution(self, 
                         vector_id: str, 
                         resolution_status: str,
                         resolution_notes: str) -> None:
        """Update the resolution status and notes for all chunks of a log entry."""
        filter = {"vector_id": vector_id}
        update = {
            "resolution_status": resolution_status,
            "resolution_notes": resolution_notes,
            "resolution_timestamp": datetime.utcnow().isoformat()
        }
        
        # Note: This is a simplified version. In production, you'd want to use
        # Pinecone's update operations to modify the metadata while preserving
        # the vectors and other metadata fields.
        self.vectorstore._index.update(
            filter=filter,
            metadata=update
        )

    def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors by their IDs."""
        self.vectorstore.delete(ids=ids)

# Create a singleton instance
vector_store = VectorStore()
