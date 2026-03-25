"""
RAG Retriever — loads FAISS index and retrieves relevant chunks for a query.
"""

from pathlib import Path
from core.config import settings

INDEX_DIR = Path(settings.RAG_INDEX_DIR)

vectorstore = None


def _load_store():
    global vectorstore
    if vectorstore is not None:
        return vectorstore

    index_file = INDEX_DIR / "index.faiss"
    if not index_file.exists():
        return None

    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import AzureOpenAIEmbeddings

        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment="text-embedding-3-small",
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        vectorstore = FAISS.load_local(
            str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True
        )
        print("[RAG] Vector store loaded.")
    except Exception as e:
        print(f"[RAG] Could not load vector store: {e}")
        vectorstore = None

    return vectorstore


def retrieve(query: str, k: int = 3) -> list[str]:
    """
    Retrieve the top-k most relevant text chunks for the given query.
    Returns a list of text strings (empty list if RAG is unavailable).
    """
    store = _load_store()
    if store is None:
        return []

    try:
        docs = store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        return []


def invalidate_cache():
    """Call this after re-indexing to reload the vector store."""
    global vectorstore
    vectorstore = None
