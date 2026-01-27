"""
DoruMake Email Sender
SMTP-based email notification service
"""

import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

from src.config import settings
from src.utils.logger import logger


class EmailSender:
    """
    Email sender service using SMTP
    """

    def __init__(self):
        self.smtp_host = settings.notification.smtp_host
        self.smtp_port = settings.notification.smtp_port
        self.smtp_user = settings.notification.smtp_user
        self.smtp_password = settings.notification.smtp_password
        self.enabled = settings.notification.enabled

    def _connect(self) -> Optional[smtplib.SMTP]:
        """Create SMTP connection"""
        if not self.enabled:
            logger.warning("Email notifications are disabled")
            return None

        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured")
            return None

        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            return None

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send an email

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body

        Returns:
            True if sent successfully
        """
        server = self._connect()
        if not server:
            logger.warning(f"Email not sent (SMTP not configured): {subject}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to

            # Plain text part
            part1 = MIMEText(body, "plain", "utf-8")
            msg.attach(part1)

            # HTML part (optional)
            if html_body:
                part2 = MIMEText(html_body, "html", "utf-8")
                msg.attach(part2)

            server.sendmail(self.smtp_user, to, msg.as_string())
            server.quit()

            logger.info(f"Email sent to {to}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_to_multiple(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> Dict[str, bool]:
        """Send email to multiple recipients"""
        results = {}
        for recipient in recipients:
            results[recipient] = self.send_email(recipient, subject, body)
        return results


def generate_random_password(length: int = 12) -> str:
    """Generate a random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_notification_email(
    template_name: str,
    to: str,
    params: Dict[str, Any]
) -> bool:
    """
    Send a notification email using a template

    Args:
        template_name: Template name (new_user, password_reset, etc.)
        to: Recipient email
        params: Template parameters

    Returns:
        True if sent successfully
    """
    # Import here to avoid circular imports
    from src.api.main import _templates_db

    # Find template
    template = None
    for t in _templates_db:
        if t["name"] == template_name:
            template = t
            break

    if not template:
        logger.error(f"Template not found: {template_name}")
        return False

    # Interpolate template
    subject = template["subject"]
    body = template["body"]

    for key, value in params.items():
        placeholder = "{" + key + "}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))

    # Send email
    sender = EmailSender()
    return sender.send_email(to, subject, body)
