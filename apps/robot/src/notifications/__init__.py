"""
KolayRobot Notifications Module
Email and notification services
"""

from .email_sender import EmailSender, send_notification_email

__all__ = ["EmailSender", "send_notification_email"]
