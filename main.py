"""
Avishka Pathology — Unified FastAPI Application
Serves the premium website + all AI APIs on port 8000
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from database.db import create_tables
from api import chat, booking, voice, contact, upload, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and RAG index on startup."""
    create_tables()
    # Attempt to load existing RAG index if documents exist
    try:
        from rag.indexer import build_index_if_needed
        build_index_if_needed()
    except Exception as e:
        print(f"[RAG] Startup index skipped: {e}")
    yield


app = FastAPI(
    title="Avishka Pathology API",
    description="Unified backend for Avishka Pathology — Azamgarh, U.P.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ─────────────────────────────────────────────────────────────
app.include_router(chat.router,    prefix="/api/chat",    tags=["Chat"])
app.include_router(booking.router, prefix="/api/booking", tags=["Booking"])
app.include_router(voice.router,   prefix="/api/voice",   tags=["Voice"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])
app.include_router(upload.router,  prefix="/api/upload",  tags=["Upload"])
app.include_router(admin.router,   prefix="/admin",        tags=["Admin"])

# ── Static Files ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Catch-all: serve the SPA for every non-API route."""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import signal
    import sys

    def _shutdown(sig, frame):
        print("\n[Server] Shutting down cleanly...")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,        # False = single process, Ctrl+C kills it instantly
        log_level="info",
        access_log=True,
    )
