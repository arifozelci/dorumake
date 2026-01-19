#!/usr/bin/env python3
"""
DoruMake Robot Service
Main entry point for the order automation system
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


# Graceful shutdown flag
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()

    logger.info("=" * 60)
    logger.info(f"  DoruMake Robot Service v{settings.app_version}")
    logger.info(f"  Environment: {settings.environment}")
    logger.info("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        logger.info("Database initialized")

        # Start services
        logger.info("Starting services...")

        # TODO: Start workers
        # - Email worker (IMAP polling)
        # - Order worker (process orders from queue)
        # - Scheduler (health checks, cleanup)

        # For now, just keep running
        logger.info("Services started. Waiting for shutdown signal...")

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise

    finally:
        # Cleanup
        logger.info("Shutting down...")
        await close_db()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        sys.exit(1)
