"""
DoruMake Email Worker
Background worker for polling and processing order emails
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from src.config import settings
from src.utils.logger import logger, email_logger
from src.email.fetcher import EmailFetcher
from src.email.parser import EmailParser, SupplierType
from src.parser.excel_parser import ExcelParser
from src.db.models import Email, EmailAttachment, Order, OrderItem, OrderStatus, EmailStatus


class EmailWorker:
    """
    Email worker for polling and processing order emails

    Responsibilities:
    - Poll IMAP server for new emails
    - Parse emails to detect supplier and extract attachments
    - Parse Excel attachments for order data
    - Create order records in database
    - Queue orders for robot processing
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.fetcher = EmailFetcher()
        self.email_parser = EmailParser()
        self.excel_parser = ExcelParser()

        self.is_running = False
        self.poll_interval = settings.email.poll_interval
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start the email worker"""
        email_logger.info("Starting email worker...")
        self.is_running = True
        self._stop_event.clear()

        try:
            await self._run_loop()
        except asyncio.CancelledError:
            email_logger.info("Email worker cancelled")
        except Exception as e:
            email_logger.error(f"Email worker error: {e}")
            raise
        finally:
            self.is_running = False

    async def stop(self):
        """Stop the email worker"""
        email_logger.info("Stopping email worker...")
        self._stop_event.set()

    async def _run_loop(self):
        """Main polling loop"""
        email_logger.info(f"Email worker started. Poll interval: {self.poll_interval}s")

        while not self._stop_event.is_set():
            try:
                await self._poll_emails()
            except Exception as e:
                email_logger.error(f"Error in poll cycle: {e}")

            # Wait for next poll or stop signal
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.poll_interval
                )
            except asyncio.TimeoutError:
                pass  # Normal timeout, continue polling

    async def _poll_emails(self):
        """Single poll cycle"""
        email_logger.debug("Polling for new emails...")

        try:
            async with self.fetcher as fetcher:
                # Fetch unread emails
                emails = await fetcher.fetch_unread_emails(
                    mark_as_read=False,  # Mark as read after successful processing
                    limit=10
                )

                if not emails:
                    email_logger.debug("No new emails")
                    return

                email_logger.info(f"Found {len(emails)} new emails")

                # Process each email
                for email_data in emails:
                    try:
                        await self._process_email(email_data, fetcher)
                    except Exception as e:
                        email_logger.error(f"Error processing email: {e}")
                        continue

        except Exception as e:
            email_logger.error(f"Error connecting to IMAP: {e}")
            raise

    async def _process_email(self, email_data: Dict[str, Any], fetcher: EmailFetcher):
        """
        Process a single email

        Args:
            email_data: Raw email data from fetcher
            fetcher: EmailFetcher instance for marking as read
        """
        subject = email_data.get('subject', '')[:50]
        email_logger.info(f"Processing email: {subject}...")

        # Parse email content
        parsed = self.email_parser.parse_email(email_data)

        # Check if valid order email
        if not parsed['is_valid_order']:
            errors = ', '.join(parsed['validation_errors'])
            email_logger.warning(f"Invalid order email: {errors}")

            # TODO: Save to DB as ignored
            # Mark as read to avoid reprocessing
            await fetcher.mark_as_read(email_data['imap_uid'])
            return

        # Get supplier type
        supplier_type = parsed['supplier_type']
        email_logger.info(f"Detected supplier: {supplier_type}")

        # Parse Excel attachments
        orders_created = []

        for attachment in parsed['excel_attachments']:
            file_path = attachment['file_path']

            # Parse Excel
            order_data = self.excel_parser.parse_file(file_path)
            if not order_data:
                email_logger.warning(f"Failed to parse Excel: {attachment['filename']}")
                continue

            # Create order record
            order_info = await self._create_order_from_data(
                order_data,
                supplier_type,
                email_data,
                attachment
            )

            if order_info:
                orders_created.append(order_info)
                email_logger.info(
                    f"Created order: {order_info['order_code']} "
                    f"({order_info['item_count']} items)"
                )

        # Mark email as read if at least one order created
        if orders_created:
            await fetcher.mark_as_read(email_data['imap_uid'])
            email_logger.info(
                f"Email processed successfully. "
                f"Created {len(orders_created)} orders."
            )
        else:
            email_logger.warning("No orders created from email")

    async def _create_order_from_data(
        self,
        order_data,
        supplier_type: str,
        email_data: Dict[str, Any],
        attachment: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create order record from parsed data

        Args:
            order_data: Parsed OrderData from Excel
            supplier_type: Detected supplier type
            email_data: Original email data
            attachment: Attachment info

        Returns:
            Created order info dict or None
        """
        try:
            order_id = str(uuid.uuid4())
            email_id = str(uuid.uuid4())

            # Build order info (for database insert)
            order_info = {
                "id": order_id,
                "order_code": order_data.order_code,
                "supplier_type": supplier_type,
                "customer_code": order_data.customer_code,
                "customer_name": order_data.customer_name,
                "order_date": order_data.order_date,
                "status": OrderStatus.PENDING.value,
                "total_amount": float(order_data.total_amount) if order_data.total_amount else None,
                "currency": order_data.currency,
                "item_count": len(order_data.items),
                "total_quantity": sum(item.quantity for item in order_data.items),
                "items": [item.to_dict() for item in order_data.items],
                "email_id": email_id,
                "email_subject": email_data.get('subject'),
                "attachment_filename": attachment.get('filename'),
                "attachment_path": attachment.get('file_path'),
                "created_at": datetime.utcnow().isoformat(),
            }

            # TODO: Save to database when session is available
            # if self.db_session:
            #     await self._save_order_to_db(order_info)

            email_logger.info(
                f"Order prepared: {order_info['order_code']} - "
                f"{supplier_type} - "
                f"{order_info['item_count']} items"
            )

            return order_info

        except Exception as e:
            email_logger.error(f"Error creating order: {e}")
            return None

    async def process_single_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email (for manual triggering)

        Args:
            email_data: Email data dict

        Returns:
            Processing result
        """
        result = {
            "success": False,
            "orders": [],
            "errors": []
        }

        try:
            # Parse email
            parsed = self.email_parser.parse_email(email_data)

            if not parsed['is_valid_order']:
                result["errors"] = parsed['validation_errors']
                return result

            # Parse attachments and create orders
            for attachment in parsed['excel_attachments']:
                order_data = self.excel_parser.parse_file(attachment['file_path'])
                if order_data:
                    order_info = await self._create_order_from_data(
                        order_data,
                        parsed['supplier_type'],
                        email_data,
                        attachment
                    )
                    if order_info:
                        result["orders"].append(order_info)

            result["success"] = len(result["orders"]) > 0

        except Exception as e:
            result["errors"].append(str(e))

        return result
