"""
DoruMake Order Worker
Background worker for processing orders with supplier robots
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from src.config import settings
from src.utils.logger import logger, order_logger
from src.robots.mutlu_aku import MutluAkuRobot
from src.robots.mann_hummel import MannHummelRobot
from src.robots.base import RobotResult
from src.db.models import Order, OrderItem, OrderStatus


class OrderWorker:
    """
    Order worker for processing orders with supplier robots

    Responsibilities:
    - Monitor pending orders in database
    - Select appropriate robot based on supplier
    - Run robot to process order
    - Update order status
    - Handle retries and failures
    - Support parallel processing (Mann & Mutlu can run simultaneously)
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.is_running = False
        self._stop_event = asyncio.Event()

        # Separate queues for each supplier (parallel processing)
        self._mutlu_queue: asyncio.Queue = asyncio.Queue()
        self._mann_queue: asyncio.Queue = asyncio.Queue()

        # Active tasks
        self._mutlu_task: Optional[asyncio.Task] = None
        self._mann_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the order worker"""
        order_logger.info("Starting order worker...")
        self.is_running = True
        self._stop_event.clear()

        try:
            # Start parallel processors for each supplier
            self._mutlu_task = asyncio.create_task(
                self._process_supplier_queue("MUTLU", self._mutlu_queue)
            )
            self._mann_task = asyncio.create_task(
                self._process_supplier_queue("MANN", self._mann_queue)
            )

            # Start queue monitor
            await self._monitor_pending_orders()

        except asyncio.CancelledError:
            order_logger.info("Order worker cancelled")
        except Exception as e:
            order_logger.error(f"Order worker error: {e}")
            raise
        finally:
            self.is_running = False
            await self._cleanup()

    async def stop(self):
        """Stop the order worker"""
        order_logger.info("Stopping order worker...")
        self._stop_event.set()

    async def _cleanup(self):
        """Cleanup tasks"""
        if self._mutlu_task:
            self._mutlu_task.cancel()
            try:
                await self._mutlu_task
            except asyncio.CancelledError:
                pass

        if self._mann_task:
            self._mann_task.cancel()
            try:
                await self._mann_task
            except asyncio.CancelledError:
                pass

    async def _monitor_pending_orders(self):
        """Monitor and queue pending orders"""
        order_logger.info("Order monitor started")

        while not self._stop_event.is_set():
            try:
                # TODO: Fetch pending orders from database
                # For now, just wait
                await asyncio.sleep(10)

            except Exception as e:
                order_logger.error(f"Error monitoring orders: {e}")
                await asyncio.sleep(5)

    async def _process_supplier_queue(self, supplier_code: str, queue: asyncio.Queue):
        """
        Process orders for a specific supplier

        Args:
            supplier_code: MUTLU or MANN
            queue: Queue for this supplier's orders
        """
        order_logger.info(f"[{supplier_code}] Supplier processor started")

        while not self._stop_event.is_set():
            try:
                # Wait for order with timeout
                try:
                    order_info = await asyncio.wait_for(queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    continue

                # Process order
                order_logger.info(f"[{supplier_code}] Processing order: {order_info.get('order_code')}")
                await self._process_order(order_info, supplier_code)
                queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                order_logger.error(f"[{supplier_code}] Processor error: {e}")

    async def _process_order(self, order_info: Dict[str, Any], supplier_code: str):
        """
        Process a single order with the appropriate robot

        Args:
            order_info: Order data dict
            supplier_code: MUTLU or MANN
        """
        order_code = order_info.get('order_code', 'UNKNOWN')
        order_logger.info(f"Processing order {order_code} with {supplier_code} robot")

        try:
            # Update status to PROCESSING
            await self._update_order_status(order_info['id'], OrderStatus.PROCESSING)

            # Create mock Order object for robot
            # In production, this would be loaded from database
            order = self._create_order_object(order_info)
            order_items = self._create_order_items(order_info.get('items', []))

            # Select and run robot
            result = await self._run_robot(supplier_code, order, order_items)

            # Update order based on result
            if result.success:
                await self._update_order_status(
                    order_info['id'],
                    OrderStatus.COMPLETED,
                    portal_order_no=result.portal_order_no
                )
                order_logger.info(
                    f"Order {order_code} completed. Portal order: {result.portal_order_no}"
                )
            else:
                await self._update_order_status(
                    order_info['id'],
                    OrderStatus.FAILED,
                    error_message=result.message
                )
                order_logger.error(f"Order {order_code} failed: {result.message}")

        except Exception as e:
            order_logger.error(f"Error processing order {order_code}: {e}")
            await self._update_order_status(
                order_info['id'],
                OrderStatus.FAILED,
                error_message=str(e)
            )

    async def _run_robot(
        self,
        supplier_code: str,
        order: Order,
        order_items: List[OrderItem]
    ) -> RobotResult:
        """
        Run the appropriate robot for the supplier

        Args:
            supplier_code: MUTLU or MANN
            order: Order object
            order_items: List of OrderItem objects

        Returns:
            RobotResult
        """
        if supplier_code == "MUTLU":
            robot = MutluAkuRobot(order, order_items)
        elif supplier_code == "MANN":
            robot = MannHummelRobot(order, order_items)
        else:
            raise ValueError(f"Unknown supplier: {supplier_code}")

        return await robot.run()

    def _create_order_object(self, order_info: Dict[str, Any]) -> Order:
        """Create Order object from dict"""
        order = Order(
            id=order_info.get('id', ''),
            order_code=order_info.get('order_code', ''),
            caspar_order_no=order_info.get('caspar_order_no'),
            status=OrderStatus.PENDING,
            supplier_id='',  # Would be set from DB
            customer_id='',  # Would be set from DB
        )
        # Pass customer info from Excel parsing (not from DB relationships)
        order._excel_customer_code = order_info.get('customer_code', '')
        order._excel_customer_name = order_info.get('customer_name', '')
        return order

    def _create_order_items(self, items_data: List[Dict]) -> List[OrderItem]:
        """Create OrderItem objects from list of dicts"""
        items = []
        for item_data in items_data:
            item = OrderItem(
                id=item_data.get('id', ''),
                order_id='',
                product_code=item_data.get('product_code', ''),
                product_name=item_data.get('product_name'),
                quantity=item_data.get('quantity', 0),
            )
            items.append(item)
        return items

    async def _update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        portal_order_no: str = None,
        error_message: str = None
    ):
        """
        Update order status in database

        Args:
            order_id: Order ID
            status: New status
            portal_order_no: Portal order number (on success)
            error_message: Error message (on failure)
        """
        # TODO: Implement database update
        order_logger.debug(f"Status update: {order_id} -> {status.value}")

    async def queue_order(self, order_info: Dict[str, Any]):
        """
        Add order to processing queue

        Args:
            order_info: Order data dict with supplier_type
        """
        supplier_type = order_info.get('supplier_type', '')

        if supplier_type == "MUTLU":
            await self._mutlu_queue.put(order_info)
            order_logger.info(f"Order queued for Mutlu Akü: {order_info.get('order_code')}")

        elif supplier_type == "MANN":
            await self._mann_queue.put(order_info)
            order_logger.info(f"Order queued for Mann & Hummel: {order_info.get('order_code')}")

        else:
            order_logger.warning(f"Unknown supplier type: {supplier_type}")

    async def process_order_manual(
        self,
        order_info: Dict[str, Any]
    ) -> RobotResult:
        """
        Process order manually (for testing or manual trigger)

        Args:
            order_info: Order data dict

        Returns:
            RobotResult
        """
        supplier_type = order_info.get('supplier_type', '')
        order = self._create_order_object(order_info)
        order_items = self._create_order_items(order_info.get('items', []))

        return await self._run_robot(supplier_type, order, order_items)

    def get_queue_status(self) -> Dict[str, int]:
        """Get current queue sizes"""
        return {
            "mutlu_queue": self._mutlu_queue.qsize(),
            "mann_queue": self._mann_queue.qsize(),
        }
