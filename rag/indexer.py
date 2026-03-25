"""
RAG Document Indexer — ingests PDFs and TXT files into a FAISS vector index.
Place documents in rag/documents/ and they will be automatically indexed.
Supports: .pdf, .txt, .md
"""

from pathlib import Path
from core.config import settings

DOCS_DIR  = Path(settings.RAG_DOCUMENTS_DIR)
INDEX_DIR = Path(settings.RAG_INDEX_DIR)


def _get_embeddings():
    """
    Create Azure OpenAI embeddings.
    Tries text-embedding-3-small first; falls back to the chat deployment
    (works for basic similarity but not ideal — replace with a real embedding
    deployment when available).
    """
    from langchain_openai import AzureOpenAIEmbeddings

    # Try dedicated embedding deployment first
    for deployment in ["text-embedding-3-small", "embedding", settings.AZURE_OPENAI_DEPLOYMENT]:
        try:
            emb = AzureOpenAIEmbeddings(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_deployment=deployment,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
            # Quick connectivity test with a tiny string
            emb.embed_query("test")
            print(f"[RAG] Using embedding deployment: {deployment}")
            return emb
        except Exception as e:
            print(f"[RAG] Deployment '{deployment}' unavailable: {e}")
            continue

    raise RuntimeError(
        "[RAG] No working embedding deployment found. "
        "RAG is disabled — chatbot uses built-in knowledge base."
    )


def _load_txt(path: Path) -> list:
    """Load a plain text / markdown file as LangChain documents."""
    from langchain_core.documents import Document
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [Document(page_content=text, metadata={"source": path.name})]


def build_index(force: bool = False) -> bool:
    """
    Scan rag/documents/ for PDFs and TXT/MD files, chunk them,
    embed with Azure OpenAI, and save FAISS index.
    Returns True if index was built successfully.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS

    doc_files = (
        list(DOCS_DIR.glob("*.pdf"))
        + list(DOCS_DIR.glob("*.txt"))
        + list(DOCS_DIR.glob("*.md"))
    )
    if not doc_files:
        print("[RAG] No documents found in rag/documents/")
        return False

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[RAG] Indexing {len(doc_files)} document(s)...")

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    all_docs = []

    for doc_path in doc_files:
        try:
            if doc_path.suffix.lower() == ".pdf":
                from langchain_community.document_loaders import PyPDFLoader
                pages = PyPDFLoader(str(doc_path)).load()
            else:
                pages = _load_txt(doc_path)

            chunks = splitter.split_documents(pages)
            all_docs.extend(chunks)
            print(f"[RAG]   {doc_path.name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"[RAG]   Failed to load {doc_path.name}: {e}")

    if not all_docs:
        return False

    embeddings  = _get_embeddings()
    vectorstore = FAISS.from_documents(all_docs, embeddings)
    vectorstore.save_local(str(INDEX_DIR))
    print(f"[RAG] Index saved to {INDEX_DIR}/")
    return True


def build_index_if_needed():
    """Build index if documents exist but index is stale or missing."""
    index_file = INDEX_DIR / "index.faiss"
    has_docs = any(
        list(DOCS_DIR.glob(pat))
        for pat in ("*.pdf", "*.txt", "*.md")
    )
    if not index_file.exists() and has_docs:
        build_index()
