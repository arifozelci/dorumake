"""
KolayRobot Email Fetcher
IMAP-based email fetching service for order emails
"""

import asyncio
import email
from email.header import decode_header
from email.message import Message
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import uuid

from imapclient import IMAPClient
import ssl

from src.config import settings
from src.utils.logger import logger, email_logger


class EmailFetcher:
    """
    IMAP email fetcher for order processing

    Connects to IMAP server and fetches unread emails with attachments.
    """

    def __init__(self):
        self.client: Optional[IMAPClient] = None
        self.download_path = Path(settings.playwright.download_path) / "emails"
        self.download_path.mkdir(parents=True, exist_ok=True)

    async def connect(self) -> None:
        """Connect to IMAP server"""
        email_logger.info(f"Connecting to IMAP server: {settings.email.host}:{settings.email.port}")

        try:
            # Create SSL context
            ssl_context = ssl.create_default_context()

            # Connect to IMAP server
            self.client = IMAPClient(
                host=settings.email.host,
                port=settings.email.port,
                ssl=settings.email.use_ssl,
                ssl_context=ssl_context
            )

            # Login
            self.client.login(settings.email.user, settings.email.password)

            email_logger.info(f"Connected to IMAP server as {settings.email.user}")

        except Exception as e:
            email_logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from IMAP server"""
        if self.client:
            try:
                self.client.logout()
                email_logger.info("Disconnected from IMAP server")
            except Exception as e:
                email_logger.warning(f"Error during disconnect: {e}")
            finally:
                self.client = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    def _decode_header_value(self, value: str) -> str:
        """Decode email header value (handles encoded strings)"""
        if value is None:
            return ""

        decoded_parts = decode_header(value)
        result = []

        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                charset = charset or 'utf-8'
                try:
                    result.append(part.decode(charset))
                except (UnicodeDecodeError, LookupError):
                    result.append(part.decode('utf-8', errors='replace'))
            else:
                result.append(part)

        return ''.join(result)

    def _parse_email_address(self, address: str) -> str:
        """Extract email address from header"""
        if not address:
            return ""

        # Handle "Name <email@domain.com>" format
        if '<' in address and '>' in address:
            start = address.index('<') + 1
            end = address.index('>')
            return address[start:end]

        return address.strip()

    def _get_email_body(self, msg: Message) -> Tuple[str, str]:
        """
        Extract email body (text and HTML)

        Returns:
            Tuple of (text_body, html_body)
        """
        text_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded = payload.decode(charset, errors='replace')

                        if content_type == "text/plain":
                            text_body = decoded
                        elif content_type == "text/html":
                            html_body = decoded
                except Exception as e:
                    email_logger.warning(f"Error decoding email part: {e}")
        else:
            # Single part message
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    text_body = payload.decode(charset, errors='replace')
            except Exception as e:
                email_logger.warning(f"Error decoding email body: {e}")

        return text_body, html_body

    def _extract_attachments(self, msg: Message, email_id: str) -> List[Dict[str, Any]]:
        """
        Extract attachments from email

        Args:
            msg: Email message
            email_id: Unique email ID for file naming

        Returns:
            List of attachment info dicts
        """
        attachments = []

        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" not in content_disposition:
                continue

            filename = part.get_filename()
            if not filename:
                continue

            # Decode filename if needed
            filename = self._decode_header_value(filename)

            # Skip non-Excel files (we only care about order files)
            if not filename.lower().endswith(('.xlsx', '.xls', '.csv')):
                email_logger.debug(f"Skipping non-Excel attachment: {filename}")
                continue

            try:
                # Get attachment data
                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                # Generate safe filename
                safe_filename = f"{email_id}_{filename}"
                file_path = self.download_path / safe_filename

                # Save attachment
                with open(file_path, 'wb') as f:
                    f.write(payload)

                attachment_info = {
                    "id": str(uuid.uuid4()),
                    "filename": filename,
                    "safe_filename": safe_filename,
                    "file_path": str(file_path),
                    "mime_type": part.get_content_type(),
                    "size": len(payload)
                }

                attachments.append(attachment_info)
                email_logger.info(f"Saved attachment: {filename} ({len(payload)} bytes)")

            except Exception as e:
                email_logger.error(f"Error saving attachment {filename}: {e}")

        return attachments

    async def fetch_unread_emails(
        self,
        folder: str = "INBOX",
        mark_as_read: bool = False,
        limit: int = 50,
        known_message_ids: set = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent emails from specified folder

        Uses SINCE date search instead of UNSEEN to handle Gmail
        marking emails as read when the account is open in a browser.
        Deduplication is done via known_message_ids from the database.

        Args:
            folder: IMAP folder name (default: INBOX)
            mark_as_read: Whether to mark fetched emails as read
            limit: Maximum number of emails to fetch
            known_message_ids: Set of message_ids already processed (for dedup)

        Returns:
            List of email data dicts
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")

        emails = []
        if known_message_ids is None:
            known_message_ids = set()

        try:
            # Select folder
            self.client.select_folder(folder)

            # Search for recent emails (today) instead of UNSEEN
            # This handles Gmail marking emails as read when opened in browser
            today = datetime.now().strftime('%d-%b-%Y')
            messages = self.client.search(['SINCE', today])

            if not messages:
                email_logger.debug("No recent emails found")
                return emails

            # First pass: fetch envelopes to check message_ids (lightweight)
            envelopes = self.client.fetch(messages, ['ENVELOPE'])
            new_messages = []
            for msg_id in messages:
                if msg_id in envelopes:
                    envelope = envelopes[msg_id].get(b'ENVELOPE')
                    if envelope and envelope.message_id:
                        mid = envelope.message_id.decode('utf-8', errors='replace')
                        if mid in known_message_ids:
                            continue  # Already processed, skip
                new_messages.append(msg_id)

            if not new_messages:
                email_logger.debug("No new emails (all already processed)")
                return emails

            email_logger.info(f"Found {len(new_messages)} new emails (of {len(messages)} recent)")

            # Limit number of messages
            new_messages = new_messages[:limit]

            # Fetch full messages
            for msg_id in new_messages:
                try:
                    # Fetch email data
                    response = self.client.fetch([msg_id], ['RFC822', 'INTERNALDATE'])

                    if msg_id not in response:
                        continue

                    raw_email = response[msg_id][b'RFC822']
                    internal_date = response[msg_id][b'INTERNALDATE']

                    # Parse email
                    msg = email.message_from_bytes(raw_email)

                    # Generate unique ID
                    email_id = str(uuid.uuid4())[:8]

                    # Extract headers
                    subject = self._decode_header_value(msg.get('Subject', ''))
                    from_addr = self._parse_email_address(
                        self._decode_header_value(msg.get('From', ''))
                    )
                    to_addr = self._parse_email_address(
                        self._decode_header_value(msg.get('To', ''))
                    )
                    message_id = msg.get('Message-ID', f'<{email_id}@local>')

                    # Extract body
                    text_body, html_body = self._get_email_body(msg)

                    # Extract attachments
                    attachments = self._extract_attachments(msg, email_id)

                    # Check if this is an order email (has Excel attachment)
                    is_order_email = len(attachments) > 0

                    email_data = {
                        "id": str(uuid.uuid4()),
                        "message_id": message_id,
                        "imap_uid": msg_id,
                        "subject": subject,
                        "from_address": from_addr,
                        "to_address": to_addr,
                        "received_at": internal_date,
                        "body_text": text_body,
                        "body_html": html_body,
                        "has_attachments": len(attachments) > 0,
                        "attachments": attachments,
                        "is_order_email": is_order_email
                    }

                    emails.append(email_data)

                    email_logger.info(
                        f"Fetched email: {subject[:50]}... "
                        f"from {from_addr} "
                        f"({len(attachments)} attachments)"
                    )

                    # Mark as read if requested
                    if mark_as_read:
                        self.client.add_flags([msg_id], ['\\Seen'])

                except Exception as e:
                    email_logger.error(f"Error processing email {msg_id}: {e}")
                    continue

        except Exception as e:
            email_logger.error(f"Error fetching emails: {e}")
            raise

        return emails

    async def fetch_email_by_uid(self, uid: int, folder: str = "INBOX") -> Optional[Dict[str, Any]]:
        """
        Fetch a specific email by UID

        Args:
            uid: IMAP UID
            folder: IMAP folder name

        Returns:
            Email data dict or None
        """
        if not self.client:
            raise RuntimeError("Not connected to IMAP server")

        try:
            self.client.select_folder(folder)
            response = self.client.fetch([uid], ['RFC822', 'INTERNALDATE'])

            if uid not in response:
                return None

            raw_email = response[uid][b'RFC822']
            internal_date = response[uid][b'INTERNALDATE']

            msg = email.message_from_bytes(raw_email)
            email_id = str(uuid.uuid4())[:8]

            subject = self._decode_header_value(msg.get('Subject', ''))
            from_addr = self._parse_email_address(
                self._decode_header_value(msg.get('From', ''))
            )
            to_addr = self._parse_email_address(
                self._decode_header_value(msg.get('To', ''))
            )
            message_id = msg.get('Message-ID', f'<{email_id}@local>')

            text_body, html_body = self._get_email_body(msg)
            attachments = self._extract_attachments(msg, email_id)

            return {
                "id": str(uuid.uuid4()),
                "message_id": message_id,
                "imap_uid": uid,
                "subject": subject,
                "from_address": from_addr,
                "to_address": to_addr,
                "received_at": internal_date,
                "body_text": text_body,
                "body_html": html_body,
                "has_attachments": len(attachments) > 0,
                "attachments": attachments,
                "is_order_email": len(attachments) > 0
            }

        except Exception as e:
            email_logger.error(f"Error fetching email {uid}: {e}")
            return None

    async def mark_as_read(self, uid: int, folder: str = "INBOX") -> bool:
        """Mark email as read"""
        if not self.client:
            return False

        try:
            self.client.select_folder(folder)
            self.client.add_flags([uid], ['\\Seen'])
            return True
        except Exception as e:
            email_logger.error(f"Error marking email {uid} as read: {e}")
            return False

    async def check_connection(self) -> bool:
        """Check if connection is alive"""
        if not self.client:
            return False

        try:
            self.client.noop()
            return True
        except:
            return False
