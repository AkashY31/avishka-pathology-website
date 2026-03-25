"""
Email notification — sends booking details to the lab's email via SMTP.
Works with any Outlook / Gmail account. Set EMAIL_PASSWORD in .env to enable.
If not configured, silently skips (bookings are always saved to the DB).
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


LAB_EMAIL   = "avishka.pathology@outlook.com"
EMAIL_PASS  = os.getenv("EMAIL_PASSWORD", "")
SMTP_HOST   = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))


def send_booking_email(booking_data: dict) -> bool:
    """
    Send a booking notification email to the lab.
    Returns True on success, False if email not configured or fails.
    """
    if not EMAIL_PASS:
        print("[Email] EMAIL_PASSWORD not set — skipping email notification.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔬 New Booking: {booking_data['reference']} — {booking_data['patient_name']}"
        msg["From"]    = LAB_EMAIL
        msg["To"]      = LAB_EMAIL

        tests_rows = "".join(
            f"<tr><td style='padding:6px 12px;border-bottom:1px solid #eee;'>{t['name']}</td>"
            f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right;'>₹{t['price']}</td></tr>"
            for t in booking_data.get("tests", [])
        )

        html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#333;">

  <div style="background:linear-gradient(135deg,#0A1628,#1A3460);padding:32px 24px;border-radius:12px;text-align:center;margin-bottom:24px;">
    <h1 style="color:#fff;margin:0;font-size:1.5rem;">🔬 Avishka Pathology</h1>
    <p style="color:rgba(255,255,255,0.7);margin:8px 0 0;">New Appointment Booking</p>
  </div>

  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:16px;">
    <h2 style="color:#C0272D;margin-top:0;">Booking Reference: {booking_data['reference']}</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px 0;color:#666;width:140px;">Patient Name</td>
          <td style="padding:8px 0;font-weight:bold;">{booking_data['patient_name']}</td></tr>
      <tr><td style="padding:8px 0;color:#666;">Phone</td>
          <td style="padding:8px 0;font-weight:bold;color:#C0272D;">
            <a href="tel:{booking_data['phone']}" style="color:#C0272D;">{booking_data['phone']}</a></td></tr>
      {"<tr><td style='padding:8px 0;color:#666;'>Age / Gender</td><td style='padding:8px 0;'>" + str(booking_data.get('age','–')) + " / " + str(booking_data.get('gender','–')) + "</td></tr>" if booking_data.get('age') or booking_data.get('gender') else ""}
      {"<tr><td style='padding:8px 0;color:#666;'>Email</td><td style='padding:8px 0;'>" + booking_data['email'] + "</td></tr>" if booking_data.get('email') else ""}
      <tr><td style="padding:8px 0;color:#666;">Appointment</td>
          <td style="padding:8px 0;font-weight:bold;">📅 {booking_data['appointment_date']} at {booking_data['appointment_slot']}</td></tr>
      {"<tr><td style='padding:8px 0;color:#666;'>Symptoms</td><td style='padding:8px 0;'>" + booking_data['symptoms'] + "</td></tr>" if booking_data.get('symptoms') else ""}
      {"<tr><td style='padding:8px 0;color:#666;'>Notes</td><td style='padding:8px 0;'>" + booking_data['notes'] + "</td></tr>" if booking_data.get('notes') else ""}
    </table>
  </div>

  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:16px;">
    <h3 style="margin-top:0;color:#333;">Tests Booked</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="background:#f4f7fb;">
        <th style="padding:8px 12px;text-align:left;font-size:0.85rem;color:#666;">Test</th>
        <th style="padding:8px 12px;text-align:right;font-size:0.85rem;color:#666;">Price</th>
      </tr>
      {tests_rows}
      <tr style="background:#fff3cd;">
        <td style="padding:10px 12px;font-weight:bold;">TOTAL</td>
        <td style="padding:10px 12px;font-weight:bold;text-align:right;font-size:1.1rem;color:#C0272D;">₹{booking_data['total_cost']:.0f}</td>
      </tr>
    </table>
  </div>

  <div style="background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;padding:16px;margin-bottom:16px;">
    <p style="margin:0;color:#155724;">
      <strong>Action Required:</strong> Please call <strong>{booking_data['phone']}</strong> to confirm the appointment
      on <strong>{booking_data['appointment_date']}</strong> at <strong>{booking_data['appointment_slot']}</strong>.
    </p>
  </div>

  <p style="color:#999;font-size:0.8rem;text-align:center;">
    Received at {datetime.now().strftime('%d %b %Y, %I:%M %p')} |
    Avishka Pathology, Mahuja Modh, Martinganj, Azamgarh
  </p>

</body>
</html>"""

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(LAB_EMAIL, EMAIL_PASS)
            server.sendmail(LAB_EMAIL, LAB_EMAIL, msg.as_string())

        print(f"[Email] Booking notification sent for {booking_data['reference']}")
        return True

    except Exception as e:
        print(f"[Email] Failed to send notification: {e}")
        return False


def send_contact_email(contact_data: dict) -> bool:
    """Send a contact form notification email to the lab."""
    if not EMAIL_PASS:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📨 Contact Form: {contact_data['name']} — Avishka Pathology"
        msg["From"]    = LAB_EMAIL
        msg["To"]      = LAB_EMAIL

        html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <h2 style="color:#C0272D;">New Contact Form Submission</h2>
  <table style="width:100%;border-collapse:collapse;">
    <tr><td style="padding:8px;color:#666;">Name</td><td style="padding:8px;font-weight:bold;">{contact_data['name']}</td></tr>
    <tr><td style="padding:8px;color:#666;">Phone</td><td style="padding:8px;font-weight:bold;">{contact_data.get('phone','–')}</td></tr>
    <tr><td style="padding:8px;color:#666;">Email</td><td style="padding:8px;">{contact_data.get('email','–')}</td></tr>
    <tr><td style="padding:8px;color:#666;">Subject</td><td style="padding:8px;">{contact_data.get('subject','–')}</td></tr>
    <tr><td style="padding:8px;color:#666;vertical-align:top;">Message</td>
        <td style="padding:8px;">{contact_data.get('message','–')}</td></tr>
  </table>
  <p style="color:#999;font-size:0.8rem;">Received at {datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
</body>
</html>"""

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(LAB_EMAIL, EMAIL_PASS)
            server.sendmail(LAB_EMAIL, LAB_EMAIL, msg.as_string())

        return True
    except Exception as e:
        print(f"[Email] Contact notification failed: {e}")
        return False
