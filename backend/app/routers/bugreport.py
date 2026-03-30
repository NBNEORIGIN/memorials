"""Bug report endpoint — emails reports via IONOS SMTP."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/bugreport", tags=["Bug Reports"])


class BugReport(BaseModel):
    subject: str
    description: str
    page: str = ""
    job_id: int | None = None
    item_id: int | None = None
    steps_to_reproduce: str = ""
    reporter: str = ""


@router.post("/")
def submit_bug_report(report: BugReport):
    """Submit a bug report — sent via email to the team."""
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        raise HTTPException(status_code=503, detail="SMTP not configured")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    recipients = [e.strip() for e in settings.SMTP_TO.split(",") if e.strip()]
    if not recipients:
        raise HTTPException(status_code=503, detail="No SMTP recipients configured")

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <h2 style="color: #4338ca;">🐛 Memorials Bug Report</h2>
        <table style="width:100%; border-collapse:collapse; font-size:14px;">
            <tr><td style="padding:6px 10px; font-weight:bold; color:#555; width:140px;">Reporter</td>
                <td style="padding:6px 10px;">{report.reporter or 'Not specified'}</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:6px 10px; font-weight:bold; color:#555;">Time</td>
                <td style="padding:6px 10px;">{timestamp}</td></tr>
            <tr><td style="padding:6px 10px; font-weight:bold; color:#555;">Page / Area</td>
                <td style="padding:6px 10px;">{report.page or 'Not specified'}</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:6px 10px; font-weight:bold; color:#555;">Job ID</td>
                <td style="padding:6px 10px;">{report.job_id or '—'}</td></tr>
            <tr><td style="padding:6px 10px; font-weight:bold; color:#555;">Item ID</td>
                <td style="padding:6px 10px;">{report.item_id or '—'}</td></tr>
        </table>
        <h3 style="color:#333; margin-top:20px;">Description</h3>
        <div style="background:#f5f5f5; padding:12px; border-radius:6px; white-space:pre-wrap; font-size:14px;">{report.description}</div>
        <h3 style="color:#333; margin-top:16px;">Steps to Reproduce</h3>
        <div style="background:#f5f5f5; padding:12px; border-radius:6px; white-space:pre-wrap; font-size:14px;">{report.steps_to_reproduce or 'Not provided'}</div>
        <hr style="margin-top:24px; border:none; border-top:1px solid #ddd;">
        <p style="color:#999; font-size:12px;">Sent from NBNE Memorials app bug reporter</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Memorials Bug] {report.subject}"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_FROM, recipients, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    return {"status": "sent", "message": "Bug report emailed to the team"}
