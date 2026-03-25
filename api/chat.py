"""Chat API — unified text chatbot with session persistence."""

import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import ChatSession
from agents.chat_agent import process_message
from rag import retriever

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    language: str
    tests_recommended: list[dict]
    is_emergency: bool


def _get_or_create_session(db: Session, session_id: str | None) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        if session:
            return session

    new_id = session_id or str(uuid.uuid4())
    session = ChatSession(session_id=new_id, history="[]")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/message", response_model=ChatResponse)
def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session = _get_or_create_session(db, req.session_id)
    history = json.loads(session.history or "[]")

    # Process with agent
    result = process_message(
        user_message=req.message,
        history=history,
        rag_retriever=retriever,
    )

    # Persist conversation turn
    history.append({"role": "user",      "content": req.message})
    history.append({"role": "assistant", "content": result["reply"]})

    # Keep last 20 messages to avoid DB bloat
    session.history   = json.dumps(history[-20:])
    session.language  = result["language"]
    session.last_active = datetime.utcnow()
    db.commit()

    return ChatResponse(
        reply=result["reply"],
        session_id=session.session_id,
        language=result["language"],
        tests_recommended=result["tests_recommended"],
        is_emergency=result["is_emergency"],
    )


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, "history": json.loads(session.history)}


@router.post("/session/new")
def new_session(db: Session = Depends(get_db)):
    session = ChatSession(session_id=str(uuid.uuid4()), history="[]")
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "session_id": session.session_id,
        "greeting": (
            "Hello! I'm Dr. Avi, your AI health assistant at Avishka Pathology. 😊\n\n"
            "You can ask me about test prices, preparation instructions, symptoms, "
            "or how to book an appointment. How can I help you today?"
        ),
    }
