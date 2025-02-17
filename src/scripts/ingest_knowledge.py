from datetime import datetime
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import MarkdownTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
import pinecone

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_markdown_files(directory_path: str) -> List[str]:
    """
    Load markdown files from the specified directory.
    
    Args:
        directory_path: Path to directory containing markdown files
        
    Returns:
        List of loaded markdown documents
    """
    markdown_files = []
    try:
        path = Path(directory_path)
        for file_path in path.glob("**/*.md"):
            loader = UnstructuredMarkdownLoader(str(file_path))
            markdown_files.extend(loader.load())
        logger.info(f"Loaded {len(markdown_files)} markdown files from {directory_path}")
        return markdown_files
    except Exception as e:
        logger.error(f"Error loading markdown files: {e}")
        return []

def split_markdown_content(documents: List[str]) -> List[str]:
    """
    Split markdown content into chunks for vectorization.
    
    Args:
        documents: List of markdown documents
        
    Returns:
        List of split document chunks
    """
    try:
        splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(documents)
        logger.info(f"Split documents into {len(split_docs)} chunks")
        return split_docs
    except Exception as e:
        logger.error(f"Error splitting documents: {e}")
        return []

def update_vector_store(documents: List[str], index_name: str):
    """
    Update the vector store with new document embeddings.
    
    Args:
        documents: List of document chunks to embed
        index_name: Name of the Pinecone index to update
    """
    try:
        pinecone.init()
        embeddings = OpenAIEmbeddings()
        
        # Initialize or get existing index
        vector_store = Pinecone.from_existing_index(
            index_name=index_name,
            embedding=embeddings
        )
        
        # Add new documents to the index
        vector_store.add_documents(documents)
        logger.info(f"Successfully updated vector store with {len(documents)} documents")
    except Exception as e:
        logger.error(f"Error updating vector store: {e}")

def ingest_knowledge(knowledge_dir: str, index_name: str):
    """
    Main function to ingest knowledge base markdown files into vector store.
    
    Args:
        knowledge_dir: Directory containing markdown knowledge base files
        index_name: Name of the Pinecone index to update
    """
    # Load markdown files
    documents = load_markdown_files(knowledge_dir)
    if not documents:
        return
        
    # Split content
    split_docs = split_markdown_content(documents)
    if not split_docs:
        return
        
    # Update vector store
    update_vector_store(split_docs, index_name)

if __name__ == "__main__":
    KNOWLEDGE_DIR = "knowledge_base"
    INDEX_NAME = "error-analysis-kb"
    ingest_knowledge(KNOWLEDGE_DIR, INDEX_NAME)
