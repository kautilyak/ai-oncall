from langchain.vectorstores import Pinecone
from langchain_pinecone import PineconeEmbeddings
from langchain.schema import Document
from typing import List

# Initialize the Pinecone embeddings    
embeddings = PineconeEmbeddings()

# Initialize the Pinecone vector store
# Initialize Pinecone
pinecone = Pinecone(api_key="YOUR_PINECONE_API_KEY")
index = pinecone.Index("error-logs")


def index_logs(logs: List[Document], batch_size: int = 100):
    """
    Index a list of log documents for semantic search in Pinecone.
    Uses batching for optimal performance.

    Args:
        logs (List[Document]): The log documents to index.
        batch_size (int): Size of batches for indexing. Defaults to 100.
    """
    # Process documents in batches for better performance
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i + batch_size]
        index.upsert(batch, namespace="error-logs") 

def search_logs(query: str, k: int = 5, filter: dict = None) -> List[Document]:
    """
    Search for logs relevant to the query using Pinecone's similarity search.

    Args:
        query (str): The search query.
        k (int): The number of top results to return.
        filter (dict): Optional metadata filters for the search.

    Returns:
        List[Document]: A list of relevant log documents.
    """
    # Use Pinecone's optimized similarity search with optional filtering
    results = index.query(
        top_k=k,
        include_metadata=True,
        filter=filter
    )
    return [Document(page_content=result['text'], metadata=result['metadata']) for result in results['matches']]    
