"""
DoruMake Email Worker
Background worker for polling and processing order emails
Automatically triggers robot processing after order creation
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
from src.db.sqlserver import db
from src.robots.mann_hummel import MannHummelRobot
from src.robots.mutlu_aku import MutluAkuRobot
from src.robots.base import RobotResult
from src.notifications.email_sender import EmailSender


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
        message_id = email_data.get('message_id', '')
        email_logger.info(f"Processing email: {subject}...")

        # Check if email was already processed (prevent duplicates)
        if message_id and db.email_processed(message_id):
            email_logger.info(f"Email already processed, skipping: {message_id[:30]}...")
            await fetcher.mark_as_read(email_data['imap_uid'])
            return

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

        # Save email to database
        db_email_id = None  # Will be set by auto-increment
        try:
            received_at = email_data.get('received_at')
            if isinstance(received_at, str):
                received_at = datetime.fromisoformat(received_at.replace('Z', '+00:00'))

            db_email_id = db.save_email(
                message_id=email_data.get('message_id', ''),
                subject=email_data.get('subject', ''),
                from_address=email_data.get('from_address', ''),
                to_address=email_data.get('to_address', ''),
                received_at=received_at or datetime.utcnow(),
                supplier_type=supplier_type,
                status='PROCESSING',
                has_attachment=len(parsed['excel_attachments']) > 0
            )
            email_logger.info(f"Email saved to database with ID: {db_email_id}")
        except Exception as e:
            email_logger.error(f"Failed to save email to database: {e}")
            # Continue processing anyway

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
                attachment,
                db_email_id
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
            # Update email status to processed
            if db_email_id:
                try:
                    db.update_email_status(db_email_id, 'PROCESSED')
                except Exception as e:
                    email_logger.error(f"Failed to update email status: {e}")
            email_logger.info(
                f"Email processed successfully. "
                f"Created {len(orders_created)} orders."
            )

            # Auto-process orders with robots
            for order_info in orders_created:
                try:
                    await self._auto_process_order(order_info)
                except Exception as e:
                    email_logger.error(f"Auto-process failed for {order_info['order_code']}: {e}")
        else:
            # Update email status to failed
            if db_email_id:
                try:
                    db.update_email_status(db_email_id, 'FAILED')
                except Exception as e:
                    email_logger.error(f"Failed to update email status: {e}")
            email_logger.warning("No orders created from email")

    async def _create_order_from_data(
        self,
        order_data,
        supplier_type: str,
        email_data: Dict[str, Any],
        attachment: Dict[str, Any],
        db_email_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create order record from parsed data

        Args:
            order_data: Parsed OrderData from Excel
            supplier_type: Detected supplier type
            email_data: Original email data
            attachment: Attachment info
            db_email_id: Database email ID (int) for linking order to email

        Returns:
            Created order info dict or None
        """
        try:
            # Check if order already exists (prevent duplicates)
            if db.order_exists(order_data.order_code):
                email_logger.info(f"Order already exists, skipping: {order_data.order_code}")
                return None
            order_id = str(uuid.uuid4())

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
                "email_id": db_email_id,
                "email_subject": email_data.get('subject'),
                "attachment_filename": attachment.get('filename'),
                "attachment_path": attachment.get('file_path'),
                "created_at": datetime.utcnow().isoformat(),
            }

            # Save order to database
            try:
                saved_order = db.create_order(
                    order_code=order_info['order_code'],
                    supplier_type=order_info['supplier_type'],
                    customer_name=order_info.get('customer_name', ''),
                    customer_code=order_info.get('customer_code', ''),
                    total_items=order_info['item_count'],
                    email_id=db_email_id,
                    attachment_filename=order_info.get('attachment_filename'),
                    attachment_path=order_info.get('attachment_path')
                )
                order_info['db_id'] = saved_order.get('id')
                email_logger.info(f"Order saved to database: {saved_order.get('id')}")
            except Exception as e:
                email_logger.error(f"Failed to save order to database: {e}")

            email_logger.info(
                f"Order prepared: {order_info['order_code']} - "
                f"{supplier_type} - "
                f"{order_info['item_count']} items"
            )

            return order_info

        except Exception as e:
            email_logger.error(f"Error creating order: {e}")
            return None

    def _notify_order_created(self, order_info: Dict[str, Any]):
        """Send notification email when a new order is created"""
        try:
            sender = EmailSender()
            order_code = order_info['order_code']
            supplier = order_info['supplier_type']
            customer = order_info.get('customer_name', 'Bilinmiyor')
            item_count = order_info.get('item_count', 0)

            supplier_name = "Mann & Hummel" if supplier == "MANN" else "Mutlu Akü" if supplier == "MUTLU" else supplier

            subject = f"Yeni Sipariş: {order_code} - {supplier_name}"
            body = (
                f"Yeni sipariş oluşturuldu:\n\n"
                f"Sipariş Kodu: {order_code}\n"
                f"Tedarikçi: {supplier_name}\n"
                f"Müşteri: {customer}\n"
                f"Ürün Sayısı: {item_count}\n"
                f"Durum: Robot ile işleniyor...\n\n"
                f"Admin Panel: https://93-94-251-138.sslip.io/orders\n"
            )

            for recipient in settings.notification.recipients:
                sender.send_email(recipient, subject, body)

            email_logger.info(f"Order notification sent for {order_code}")
        except Exception as e:
            email_logger.error(f"Failed to send order notification: {e}")

    def _notify_order_completed(self, order_info: Dict[str, Any], result: RobotResult):
        """Send notification email when order processing completes"""
        try:
            sender = EmailSender()
            order_code = order_info['order_code']
            supplier = order_info['supplier_type']
            supplier_name = "Mann & Hummel" if supplier == "MANN" else "Mutlu Akü" if supplier == "MUTLU" else supplier

            if result.success:
                subject = f"Sipariş Tamamlandı: {order_code} - {supplier_name}"
                body = (
                    f"Sipariş başarıyla işlendi:\n\n"
                    f"Sipariş Kodu: {order_code}\n"
                    f"Tedarikçi: {supplier_name}\n"
                    f"Portal Sipariş No: {result.portal_order_no}\n"
                    f"Süre: {result.duration_seconds:.0f} saniye\n\n"
                    f"Admin Panel: https://93-94-251-138.sslip.io/orders\n"
                )
            else:
                subject = f"Sipariş HATA: {order_code} - {supplier_name}"
                body = (
                    f"Sipariş işlenirken hata oluştu:\n\n"
                    f"Sipariş Kodu: {order_code}\n"
                    f"Tedarikçi: {supplier_name}\n"
                    f"Hata: {result.message}\n\n"
                    f"Admin Panel: https://93-94-251-138.sslip.io/orders\n"
                )

            for recipient in settings.notification.recipients:
                sender.send_email(recipient, subject, body)

            email_logger.info(f"Order completion notification sent for {order_code}")
        except Exception as e:
            email_logger.error(f"Failed to send completion notification: {e}")

    async def _auto_process_order(self, order_info: Dict[str, Any]):
        """
        Automatically process order with the appropriate robot

        Args:
            order_info: Order info dict from _create_order_from_data
        """
        order_code = order_info['order_code']
        supplier_type = order_info['supplier_type']
        db_id = order_info.get('db_id')

        email_logger.info(f"Auto-processing order {order_code} with {supplier_type} robot...")

        # Notify: order created and being processed
        self._notify_order_created(order_info)

        try:
            # Update status to processing
            if db_id:
                db.update_order_status(db_id, 'PROCESSING')

            # Parse items from Excel attachment
            items = order_info.get('items', [])
            if not items:
                attachment_path = order_info.get('attachment_path')
                if attachment_path:
                    parsed = self.excel_parser.parse_file(attachment_path)
                    if parsed and parsed.items:
                        items = [item.to_dict() for item in parsed.items]

            if not items:
                raise Exception("No order items found")

            # Create Order mock object
            order = Order(
                id=db_id or '',
                order_code=order_code,
                caspar_order_no=order_code,
                status=OrderStatus.PENDING,
                supplier_id='',
                customer_id='',
            )
            order._excel_customer_code = order_info.get('customer_code', '')
            order._excel_customer_name = order_info.get('customer_name', '')

            # Create OrderItem objects
            order_items = []
            for item_data in items:
                item = OrderItem(
                    id='',
                    order_id='',
                    product_code=item_data.get('product_code', ''),
                    product_name=item_data.get('product_name'),
                    quantity=item_data.get('quantity', 0),
                )
                order_items.append(item)

            # Select and run robot
            if supplier_type == "MANN":
                robot = MannHummelRobot(order, order_items)
            elif supplier_type == "MUTLU":
                robot = MutluAkuRobot(order, order_items)
            else:
                raise Exception(f"Unknown supplier: {supplier_type}")

            result = await robot.run()

            # Update order status and notify
            if result.success:
                if db_id:
                    db.update_order_status(
                        db_id, 'COMPLETED',
                        portal_order_number=result.portal_order_no
                    )
                email_logger.info(
                    f"Order {order_code} completed! Portal order: {result.portal_order_no}"
                )
            else:
                if db_id:
                    db.update_order_status(
                        db_id, 'FAILED',
                        error_message=result.message
                    )
                email_logger.error(f"Order {order_code} failed: {result.message}")

            # Notify: order completed or failed
            self._notify_order_completed(order_info, result)

        except Exception as e:
            email_logger.error(f"Auto-process error for {order_code}: {e}")
            if db_id:
                try:
                    db.update_order_status(db_id, 'FAILED', error_message=str(e))
                except Exception:
                    pass
            # Notify: error
            error_result = RobotResult(success=False, order_id=order_code)
            error_result.message = str(e)
            self._notify_order_completed(order_info, error_result)

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
