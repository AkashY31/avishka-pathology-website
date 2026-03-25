"""Voice API — speech-to-text + AI response + text-to-speech."""

import json
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import ChatSession
from agents.chat_agent import process_message
from core.speech import speech_to_text, text_to_speech
from rag import retriever

router = APIRouter()


@router.post("/transcribe-and-reply")
async def transcribe_and_reply(
    audio: UploadFile = File(...),
    session_id: str   = Form(default=""),
    db: Session       = Depends(get_db),
):
    """
    Accepts an audio file, transcribes it, generates AI reply, returns TTS audio + text.
    Falls back gracefully if speech services are unavailable.
    """
    audio_bytes = await audio.read()
    fmt = audio.content_type.split("/")[-1] if audio.content_type else "webm"

    # 1. Speech-to-text
    transcribed = speech_to_text(audio_bytes, fmt)
    if not transcribed:
        raise HTTPException(
            status_code=422,
            detail="Could not transcribe audio. Please use text input instead.",
        )

    # 2. Retrieve / create session
    session = None
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(session_id=str(uuid.uuid4()), history="[]")
        db.add(session)
        db.commit()
        db.refresh(session)

    history = json.loads(session.history or "[]")

    # 3. Generate reply
    result = process_message(transcribed, history, rag_retriever=retriever)

    # 4. Persist
    history.append({"role": "user",      "content": transcribed})
    history.append({"role": "assistant", "content": result["reply"]})
    session.history    = json.dumps(history[-20:])
    session.language   = result["language"]
    session.last_active = datetime.utcnow()
    db.commit()

    # 5. Text-to-speech
    audio_b64 = text_to_speech(result["reply"], result["language"])

    return {
        "transcribed": transcribed,
        "reply":       result["reply"],
        "language":    result["language"],
        "session_id":  session.session_id,
        "audio_b64":   audio_b64,        # None if speech not configured
        "is_emergency": result["is_emergency"],
    }


@router.post("/tts")
def synthesize_speech(text: str, language: str = "en"):
    """Convert arbitrary text to speech (for UI use)."""
    audio_b64 = text_to_speech(text, language)
    if audio_b64 is None:
        raise HTTPException(status_code=503, detail="TTS service not configured.")
    return {"audio_b64": audio_b64, "language": language}
