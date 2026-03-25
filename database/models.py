"""SQLAlchemy ORM models for persistent storage."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Booking(Base):
    __tablename__ = "bookings"

    id              = Column(Integer, primary_key=True, index=True)
    reference       = Column(String(20), unique=True, index=True, nullable=False)
    patient_name    = Column(String(100), nullable=False)
    age             = Column(Integer, nullable=True)
    gender          = Column(String(10), nullable=True)
    phone           = Column(String(15), nullable=False)
    email           = Column(String(100), nullable=True)
    symptoms        = Column(Text, nullable=True)
    tests           = Column(Text, nullable=False)   # JSON list: [{"code":"CBC","name":...,"price":...}]
    total_cost      = Column(Float, nullable=False)
    appointment_slot = Column(String(30), nullable=True)  # e.g. "07:00 AM"
    appointment_date = Column(String(30), nullable=True)  # e.g. "2026-03-25"
    notes           = Column(Text, nullable=True)
    # Status lifecycle: pending → confirmed → completed | cancelled
    status          = Column(String(20), default="pending", nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(String(50), unique=True, index=True, nullable=False)
    history     = Column(Text, default="[]")   # JSON list of {role, content}
    language    = Column(String(10), default="en")
    created_at  = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(100), nullable=False)
    phone      = Column(String(15), nullable=True)
    subject    = Column(String(200), nullable=False)
    message    = Column(Text, nullable=False)
    status     = Column(String(20), default="new")   # new | read | replied
    created_at = Column(DateTime, default=datetime.utcnow)
