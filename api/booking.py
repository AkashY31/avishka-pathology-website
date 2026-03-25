"""
Booking API — submit appointment requests (Option B: we'll call to confirm).
Stores in SQLite, generates reference ID, returns slot confirmation pending.
"""

import json
import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Booking
from core.test_catalog import TEST_CATALOG, all_tests_list
from core.email_notify import send_booking_email

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────

def generate_reference() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"AVP-{suffix}"


def get_available_slots() -> list[dict]:
    """Generate 6 available slots across the next 6 days."""
    slots = []
    slot_times = ["07:00 AM", "08:30 AM", "10:00 AM", "11:30 AM", "05:00 PM", "06:30 PM"]
    today = datetime.now()

    for i in range(1, 7):
        date = today + timedelta(days=i)
        if date.weekday() == 6:  # Skip Sunday evening slots
            available_times = slot_times[:2]
        else:
            available_times = slot_times

        # Pick 1 slot per day randomly
        chosen = random.choice(available_times)
        slots.append({
            "date":      date.strftime("%Y-%m-%d"),
            "day":       date.strftime("%A"),
            "date_display": date.strftime("%d %b %Y"),
            "time":      chosen,
            "label":     f"{date.strftime('%a, %d %b')} at {chosen}",
        })

    return slots


# ── Schemas ───────────────────────────────────────────────────────────────────

class BookingRequest(BaseModel):
    patient_name: str
    age: int | None = None
    gender: str | None = None
    phone: str
    email: str | None = None
    symptoms: str | None = None
    test_codes: list[str]       # e.g. ["CBC", "THYROID"]
    appointment_date: str       # e.g. "2026-03-25"
    appointment_slot: str       # e.g. "07:00 AM"
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v):
        digits = "".join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Phone must have at least 10 digits.")
        return v

    @field_validator("test_codes")
    @classmethod
    def codes_must_exist(cls, v):
        invalid = [c for c in v if c.upper() not in TEST_CATALOG]
        if invalid:
            raise ValueError(f"Unknown test code(s): {invalid}")
        return [c.upper() for c in v]


class BookingResponse(BaseModel):
    reference: str
    patient_name: str
    tests: list[dict]
    total_cost: float
    appointment_date: str
    appointment_slot: str
    status: str
    message: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/tests")
def list_tests():
    """Return the full test catalog."""
    return {"tests": all_tests_list()}


@router.get("/slots")
def list_slots():
    """Return available appointment slots for the next 6 days."""
    return {"slots": get_available_slots()}


@router.post("/submit", response_model=BookingResponse)
def submit_booking(req: BookingRequest, db: Session = Depends(get_db)):
    # Resolve test details
    tests_detail = []
    total = 0.0
    for code in req.test_codes:
        test = TEST_CATALOG[code]
        tests_detail.append({"code": code, "name": test["name"], "price": test["price"]})
        total += test["price"]

    ref = generate_reference()

    booking = Booking(
        reference=ref,
        patient_name=req.patient_name.strip(),
        age=req.age,
        gender=req.gender,
        phone=req.phone.strip(),
        email=req.email,
        symptoms=req.symptoms,
        tests=json.dumps(tests_detail),
        total_cost=total,
        appointment_date=req.appointment_date,
        appointment_slot=req.appointment_slot,
        notes=req.notes,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Send email notification to lab (background, non-blocking)
    import threading
    threading.Thread(
        target=send_booking_email,
        args=({
            "reference":        ref,
            "patient_name":     req.patient_name,
            "phone":            req.phone,
            "email":            req.email,
            "age":              req.age,
            "gender":           req.gender,
            "symptoms":         req.symptoms,
            "notes":            req.notes,
            "tests":            tests_detail,
            "total_cost":       total,
            "appointment_date": req.appointment_date,
            "appointment_slot": req.appointment_slot,
        },),
        daemon=True,
    ).start()

    return BookingResponse(
        reference=ref,
        patient_name=req.patient_name,
        tests=tests_detail,
        total_cost=total,
        appointment_date=req.appointment_date,
        appointment_slot=req.appointment_slot,
        status="pending",
        message=(
            f"Your appointment request has been received! "
            f"Reference: {ref}. Our team will call you at {req.phone} "
            f"to confirm your slot on {req.appointment_date} at {req.appointment_slot}. "
            f"For urgent queries, call 7355230710."
        ),
    )


@router.get("/status/{reference}")
def booking_status(reference: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.reference == reference).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking reference not found.")
    return {
        "reference": booking.reference,
        "patient_name": booking.patient_name,
        "status": booking.status,
        "appointment_date": booking.appointment_date,
        "appointment_slot": booking.appointment_slot,
        "tests": json.loads(booking.tests),
        "total_cost": booking.total_cost,
        "created_at": booking.created_at.isoformat(),
    }
