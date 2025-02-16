from langchain.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document
from typing import List

# Initialize the OpenAI embeddings
embeddings = OllamaEmbeddings()

# Initialize the Chroma vector store
vector_store = Chroma(collection_name="error_logs", embedding_function=embeddings)

def index_logs(logs: List[Document]):
    """
    Index a list of log documents for semantic search.

    Args:
        logs (List[Document]): The log documents to index.
    """
    vector_store.add_documents(logs)

def search_logs(query: str, k: int = 5) -> List[Document]:
    """
    Search for logs relevant to the query.

    Args:
        query (str): The search query.
        k (int): The number of top results to return.

    Returns:
        List[Document]: A list of relevant log documents.
    """
    return vector_store.similarity_search(query, k=k)
