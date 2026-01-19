#!/usr/bin/env python3
"""
DoruMake Robot Service
Main entry point for the order automation system

Starts:
- Email Worker: Polls IMAP for new order emails
- Order Worker: Processes orders with supplier robots (parallel)
- Scheduler: Runs background jobs (health checks, cleanup)
- API Server: FastAPI for admin panel communication
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.utils.logger import setup_logging, logger
from src.db.connection import init_db, close_db
from src.workers.email_worker import EmailWorker
from src.workers.order_worker import OrderWorker
from src.workers.scheduler import Scheduler


# Graceful shutdown event
shutdown_event = asyncio.Event()

# Global worker instances
email_worker: EmailWorker = None
order_worker: OrderWorker = None
scheduler: Scheduler = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()


async def start_api_server():
    """Start FastAPI server for admin panel communication"""
    import uvicorn
    from src.api.main import app

    config = uvicorn.Config(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info" if settings.debug else "warning"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main entry point"""
    global email_worker, order_worker, scheduler

    # Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info(f"  DoruMake Robot Service v{settings.app_version}")
    logger.info(f"  Environment: {settings.environment}")
    logger.info(f"  Debug: {settings.debug}")
    logger.info("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    tasks = []

    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        logger.info("Database initialized")

        # Initialize workers
        email_worker = EmailWorker()
        order_worker = OrderWorker()
        scheduler = Scheduler()

        # Start scheduler (non-async, starts in background)
        logger.info("Starting scheduler...")
        scheduler.start()

        # Start workers as async tasks
        logger.info("Starting email worker...")
        email_task = asyncio.create_task(email_worker.start())
        tasks.append(email_task)

        logger.info("Starting order worker...")
        order_task = asyncio.create_task(order_worker.start())
        tasks.append(order_task)

        # Start API server
        logger.info(f"Starting API server on {settings.api_host}:{settings.api_port}...")
        api_task = asyncio.create_task(start_api_server())
        tasks.append(api_task)

        logger.info("=" * 60)
        logger.info("  All services started successfully!")
        logger.info("  Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

    finally:
        # Stop workers
        logger.info("Stopping workers...")

        if email_worker:
            await email_worker.stop()

        if order_worker:
            await order_worker.stop()

        if scheduler:
            scheduler.stop()

        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close database
        await close_db()

        logger.info("=" * 60)
        logger.info("  Shutdown complete")
        logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        sys.exit(1)
