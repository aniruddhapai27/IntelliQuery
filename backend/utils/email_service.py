"""
Email service for sending query results and visualizations to recipients.
Uses SMTP with TLS. Configure via environment variables.
"""
import os
import io
import csv
import json
import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SMTP config from environment
# ---------------------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "") or SMTP_USER
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")


def _validate_smtp_config() -> None:
    """Raise if SMTP is not configured."""
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP credentials are not configured. "
            "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, "
            "and optionally SMTP_FROM in your environment."
        )


def results_to_csv_bytes(
    results: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
) -> bytes:
    """
    Convert a list-of-dicts result set to CSV bytes (UTF-8 with BOM for Excel
    compatibility).
    """
    if not results:
        return b""

    fieldnames = columns or list(results[0].keys())

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in results:
        writer.writerow(row)

    # UTF-8 BOM so Excel opens it properly
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")


def _build_email(
    *,
    recipients: List[str],
    subject: str,
    body_html: str,
    csv_bytes: Optional[bytes] = None,
    chart_image_bytes: Optional[bytes] = None,
) -> MIMEMultipart:
    """Assemble a MIME message with optional CSV and chart image attachments."""
    msg = MIMEMultipart("mixed")
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # HTML body
    msg.attach(MIMEText(body_html, "html"))

    # CSV attachment
    if csv_bytes:
        part = MIMEBase("text", "csv")
        part.set_payload(csv_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", "attachment", filename="query_results.csv"
        )
        msg.attach(part)

    # Chart image attachment (PNG)
    if chart_image_bytes:
        part = MIMEBase("image", "png")
        part.set_payload(chart_image_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", "attachment", filename="chart.png"
        )
        msg.attach(part)

    return msg


def send_results_email(
    *,
    recipients: List[str],
    subject: str,
    body_html: str,
    csv_bytes: Optional[bytes] = None,
    chart_image_bytes: Optional[bytes] = None,
) -> None:
    """
    Send an email with optional CSV and/or chart image as attachments.

    Raises:
        RuntimeError: If SMTP is not configured.
        smtplib.SMTPException: On SMTP send failure.
    """
    _validate_smtp_config()

    msg = _build_email(
        recipients=recipients,
        subject=subject,
        body_html=body_html,
        csv_bytes=csv_bytes,
        chart_image_bytes=chart_image_bytes,
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, recipients, msg.as_string())

    logger.info("Email sent to %s", recipients)


def render_plotly_chart_to_png(chart_data: Dict[str, Any]) -> Optional[bytes]:
    """
    Render a Plotly figure dict to PNG bytes using kaleido.
    Returns None if rendering fails.
    """
    try:
        import plotly.io as pio
        import plotly.graph_objects as go

        fig = go.Figure(chart_data)
        return pio.to_image(fig, format="png", width=900, height=550, scale=2)
    except Exception as exc:
        logger.warning("Failed to render chart to PNG: %s", exc)
        return None
