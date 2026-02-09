#!/usr/bin/env python3
"""
KolayRobot Email Worker - Standalone Runner
Runs only the email polling worker (for PM2 process management)
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.utils.logger import setup_logging, logger, email_logger
from src.db.connection import init_db, close_db
from src.workers.email_worker import EmailWorker


# Graceful shutdown event
shutdown_event = asyncio.Event()

# Global worker instance
email_worker: EmailWorker = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()


async def main():
    """Main entry point for email worker"""
    global email_worker

    # Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info(f"  KolayRobot Email Worker v{settings.app_version}")
    logger.info(f"  Environment: {settings.environment}")
    logger.info(f"  Poll Interval: {settings.email.poll_interval}s")
    logger.info("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        logger.info("Database initialized")

        # Initialize email worker
        email_worker = EmailWorker()

        # Start worker as async task
        logger.info("Starting email worker...")
        worker_task = asyncio.create_task(email_worker.start())

        logger.info("=" * 60)
        logger.info("  Email worker started successfully!")
        logger.info("  Press Ctrl+C to stop")
        logger.info("=" * 60)

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

    finally:
        # Stop worker
        logger.info("Stopping email worker...")

        if email_worker:
            await email_worker.stop()

        # Cancel worker task if running
        if 'worker_task' in dir() and worker_task and not worker_task.done():
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

        # Close database
        await close_db()

        logger.info("=" * 60)
        logger.info("  Email worker shutdown complete")
        logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Email worker crashed: {e}")
        sys.exit(1)
