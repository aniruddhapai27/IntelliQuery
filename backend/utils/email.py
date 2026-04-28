"""
Email utility for sending query results and charts to recipients.
Uses SMTP credentials from environment variables.
"""

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from typing import List, Optional

logger = logging.getLogger(__name__)


def _get_smtp_config() -> dict:
    """Load and validate SMTP configuration from environment."""
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM") or user

    missing = []
    if not host:
        missing.append("SMTP_HOST")
    if not port:
        missing.append("SMTP_PORT")
    if not user:
        missing.append("SMTP_USER")
    if not password:
        missing.append("SMTP_PASSWORD")

    if missing:
        raise RuntimeError(
            f"Missing SMTP environment variables: {', '.join(missing)}. "
            "Email sending is not configured."
        )

    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "from_addr": from_addr,
    }


def send_results_email(
    recipients: List[str],
    subject: str,
    body_text: str,
    csv_bytes: Optional[bytes] = None,
    csv_filename: str = "query_results.csv",
    chart_image_bytes: Optional[bytes] = None,
    chart_filename: str = "chart.png",
) -> None:
    """
    Send an email with optional CSV and chart image attachments.

    Args:
        recipients: List of validated email addresses.
        subject: Email subject line.
        body_text: Plain-text email body.
        csv_bytes: Raw bytes of the CSV file to attach.
        csv_filename: Name for the CSV attachment.
        chart_image_bytes: PNG bytes of the chart to attach.
        chart_filename: Name for the chart attachment.

    Raises:
        RuntimeError: If SMTP is not configured.
        smtplib.SMTPException: On any SMTP-level failure.
        ValueError: If recipients list is empty.
    """
    if not recipients:
        raise ValueError("At least one recipient email is required.")

    config = _get_smtp_config()

    msg = MIMEMultipart("mixed")
    msg["From"] = config["from_addr"]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # Plain-text body
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    # CSV attachment
    if csv_bytes:
        csv_part = MIMEBase("text", "csv")
        csv_part.set_payload(csv_bytes)
        encoders.encode_base64(csv_part)
        csv_part.add_header(
            "Content-Disposition", "attachment", filename=csv_filename
        )
        msg.attach(csv_part)

    # Chart image attachment
    if chart_image_bytes:
        img_part = MIMEImage(chart_image_bytes, name=chart_filename)
        img_part.add_header(
            "Content-Disposition", "attachment", filename=chart_filename
        )
        msg.attach(img_part)

    # Send
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config["user"], config["password"])
            server.sendmail(config["from_addr"], recipients, msg.as_string())
        logger.info("Email sent successfully to %s", recipients)
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check SMTP_USER / SMTP_PASSWORD.")
        raise
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending email: %s", exc)
        raise
