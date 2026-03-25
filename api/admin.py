"""
Admin Dashboard — view all bookings and contact submissions.
Protected by ADMIN_TOKEN in .env (default: avishka2024).
Access: http://localhost:8000/admin/bookings?token=YOUR_TOKEN
"""

import json
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Booking, Contact

router = APIRouter()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "avishka2024")


def verify_token(token: str = Query("")):
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized. Add ?token=YOUR_TOKEN to the URL.")


@router.get("/bookings", response_class=HTMLResponse)
def admin_bookings(db: Session = Depends(get_db), _=Depends(verify_token)):
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()

    rows = ""
    for b in bookings:
        tests = json.loads(b.tests or "[]")
        test_names = ", ".join(t["name"] for t in tests)
        status_color = {
            "pending":   "#FFA500",
            "confirmed": "#28A745",
            "completed": "#007BFF",
            "cancelled": "#DC3545",
        }.get(b.status, "#666")

        rows += f"""
        <tr>
          <td><strong style="color:#C0272D;">{b.reference}</strong></td>
          <td>{b.patient_name}<br><small style="color:#666;">{b.age or '–'} / {b.gender or '–'}</small></td>
          <td><a href="tel:{b.phone}" style="color:#0A1628;font-weight:600;">{b.phone}</a>
              {"<br><small>" + b.email + "</small>" if b.email else ""}</td>
          <td style="font-size:0.85rem;">{test_names}</td>
          <td style="font-weight:700;color:#C0272D;">₹{b.total_cost:.0f}</td>
          <td><strong>{b.appointment_date}</strong><br><small>{b.appointment_slot}</small></td>
          <td><span style="background:{status_color};color:#fff;padding:3px 10px;border-radius:50px;font-size:0.78rem;font-weight:600;">{b.status.upper()}</span></td>
          <td style="font-size:0.8rem;color:#666;">{b.created_at.strftime('%d %b %Y<br>%I:%M %p') if b.created_at else '–'}</td>
        </tr>"""

    total_revenue = sum(b.total_cost for b in bookings if b.status != "cancelled")
    pending_count = sum(1 for b in bookings if b.status == "pending")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin — Avishka Pathology Bookings</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f4f7fb; color: #333; }}
    .header {{ background: linear-gradient(135deg,#0A1628,#1A3460); color: #fff; padding: 24px 32px; }}
    .header h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
    .header p {{ color: rgba(255,255,255,0.6); font-size: 0.85rem; }}
    .stats {{ display: flex; gap: 16px; padding: 24px 32px; flex-wrap: wrap; }}
    .stat-box {{ background: #fff; border-radius: 10px; padding: 16px 24px; flex: 1; min-width: 140px;
                 box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-left: 4px solid #C0272D; }}
    .stat-num {{ font-size: 1.8rem; font-weight: 900; color: #C0272D; }}
    .stat-lbl {{ font-size: 0.8rem; color: #666; margin-top: 2px; }}
    .table-wrap {{ padding: 0 32px 32px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px;
             overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    th {{ background: #0A1628; color: #fff; padding: 12px 14px; text-align: left;
          font-size: 0.82rem; font-weight: 600; white-space: nowrap; }}
    td {{ padding: 12px 14px; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; vertical-align: top; }}
    tr:hover td {{ background: #fafbfc; }}
    .refresh {{ margin: 0 32px 16px; }}
    .refresh a {{ background: #C0272D; color: #fff; padding: 8px 18px; border-radius: 8px;
                  text-decoration: none; font-size: 0.85rem; font-weight: 600; }}
    .empty {{ text-align: center; padding: 60px; color: #999; font-size: 1.1rem; }}
    @media (max-width: 600px) {{
      .stats, .table-wrap, .refresh {{ padding-left: 16px; padding-right: 16px; }}
      .header {{ padding: 16px; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>🔬 Avishka Pathology — Admin Dashboard</h1>
  <p>Mahuja Modh, Martinganj, Azamgarh, U.P. &nbsp;|&nbsp; 7355230710</p>
</div>

<div class="stats">
  <div class="stat-box">
    <div class="stat-num">{len(bookings)}</div>
    <div class="stat-lbl">Total Bookings</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:#FFA500;">{pending_count}</div>
    <div class="stat-lbl">Pending Calls</div>
  </div>
  <div class="stat-box">
    <div class="stat-num">₹{total_revenue:.0f}</div>
    <div class="stat-lbl">Total Revenue</div>
  </div>
  <div class="stat-box">
    <div class="stat-num" style="color:#28A745;">{sum(1 for b in bookings if b.status=='completed')}</div>
    <div class="stat-lbl">Completed</div>
  </div>
</div>

<div class="refresh">
  <a href="?token={ADMIN_TOKEN}">🔄 Refresh</a>
  &nbsp;&nbsp;
  <a href="/admin/contacts?token={ADMIN_TOKEN}" style="background:#0A1628;">📨 View Contacts</a>
</div>

<div class="table-wrap">
  {"<table><thead><tr><th>Reference</th><th>Patient</th><th>Contact</th><th>Tests</th><th>Amount</th><th>Appointment</th><th>Status</th><th>Booked At</th></tr></thead><tbody>" + rows + "</tbody></table>" if bookings else '<div class="empty">No bookings yet. Bookings will appear here once patients submit appointments.</div>'}
</div>

</body>
</html>"""

    return HTMLResponse(content=html)


@router.get("/contacts", response_class=HTMLResponse)
def admin_contacts(db: Session = Depends(get_db), _=Depends(verify_token)):
    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()

    rows = ""
    for c in contacts:
        rows += f"""
        <tr>
          <td>{c.name}</td>
          <td>{c.phone or '–'}</td>
          <td>{c.email or '–'}</td>
          <td>{c.subject or '–'}</td>
          <td style="max-width:300px;">{c.message or '–'}</td>
          <td style="font-size:0.8rem;color:#666;">{c.created_at.strftime('%d %b %Y, %I:%M %p') if c.created_at else '–'}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Contacts — Avishka Pathology Admin</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f4f7fb; color: #333; }}
    .header {{ background: linear-gradient(135deg,#0A1628,#1A3460); color: #fff; padding: 24px 32px; }}
    .header h1 {{ font-size: 1.4rem; }}
    .table-wrap {{ padding: 24px 32px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px;
             overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    th {{ background: #0A1628; color: #fff; padding: 12px 14px; text-align: left; font-size: 0.82rem; }}
    td {{ padding: 12px 14px; border-bottom: 1px solid #f0f0f0; font-size: 0.88rem; vertical-align: top; }}
    .nav {{ padding: 16px 32px; }}
    .nav a {{ background: #C0272D; color: #fff; padding: 8px 18px; border-radius: 8px;
               text-decoration: none; font-size: 0.85rem; font-weight: 600; margin-right: 8px; }}
  </style>
</head>
<body>
<div class="header"><h1>📨 Contact Form Submissions</h1></div>
<div class="nav">
  <a href="/admin/bookings?token={ADMIN_TOKEN}">← Back to Bookings</a>
  <a href="?token={ADMIN_TOKEN}" style="background:#0A1628;">🔄 Refresh</a>
</div>
<div class="table-wrap">
  {"<table><thead><tr><th>Name</th><th>Phone</th><th>Email</th><th>Subject</th><th>Message</th><th>Date</th></tr></thead><tbody>" + rows + "</tbody></table>" if contacts else "<p style='padding:40px;color:#999;text-align:center;'>No contact submissions yet.</p>"}
</div>
</body>
</html>"""

    return HTMLResponse(content=html)
