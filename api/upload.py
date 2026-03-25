"""Document upload API — accepts PDFs for RAG indexing."""

import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from core.config import settings

router = APIRouter()

DOCS_DIR = Path(settings.RAG_DOCUMENTS_DIR)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB    = 20


def _rebuild_index():
    """Rebuild RAG index in the background after upload."""
    try:
        from rag.indexer import build_index
        from rag.retriever import invalidate_cache
        build_index(force=True)
        invalidate_cache()
        print("[Upload] RAG index rebuilt.")
    except Exception as e:
        print(f"[Upload] Index rebuild failed: {e}")


@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE_MB} MB.")

    dest = DOCS_DIR / file.filename
    dest.write_bytes(content)

    background_tasks.add_task(_rebuild_index)

    return {
        "success": True,
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "message": f"Document uploaded. RAG index is being rebuilt in the background.",
    }


@router.get("/documents")
def list_documents():
    files = [
        {"name": f.name, "size_mb": round(f.stat().st_size / (1024 * 1024), 2)}
        for f in DOCS_DIR.glob("*.pdf")
    ]
    return {"documents": files}
