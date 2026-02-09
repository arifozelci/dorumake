"""
KolayRobot Logging Configuration
Centralized logging with Loguru
"""

import sys
from pathlib import Path
from loguru import logger as loguru_logger

from src.config import settings


def setup_logging() -> None:
    """Configure application logging"""

    # Remove default handler
    loguru_logger.remove()

    # Console handler
    loguru_logger.add(
        sys.stdout,
        format=settings.log.format,
        level=settings.log.level,
        colorize=True,
        backtrace=True,
        diagnose=settings.debug
    )

    # Create log directory
    log_path = Path(settings.log.path)
    log_path.mkdir(parents=True, exist_ok=True)

    # Main log file (all logs)
    loguru_logger.add(
        log_path / "robot.log",
        format=settings.log.format,
        level="DEBUG",
        rotation=settings.log.rotation,
        retention=settings.log.retention,
        compression=settings.log.compression,
        backtrace=True,
        diagnose=True
    )

    # Error log file (errors only)
    loguru_logger.add(
        log_path / "error.log",
        format=settings.log.format,
        level="ERROR",
        rotation=settings.log.rotation,
        retention="90 days",
        compression=settings.log.compression,
        backtrace=True,
        diagnose=True
    )

    # Orders log file
    loguru_logger.add(
        log_path / "orders.log",
        format=settings.log.format,
        level="INFO",
        rotation=settings.log.rotation,
        retention=settings.log.retention,
        compression=settings.log.compression,
        filter=lambda record: "order" in record["extra"].get("category", "")
    )

    # Email log file
    loguru_logger.add(
        log_path / "email.log",
        format=settings.log.format,
        level="INFO",
        rotation=settings.log.rotation,
        retention=settings.log.retention,
        compression=settings.log.compression,
        filter=lambda record: "email" in record["extra"].get("category", "")
    )

    loguru_logger.info(f"Logging configured. Log path: {log_path}")


# Create category-specific loggers
def get_logger(category: str = ""):
    """Get a logger with specific category"""
    return loguru_logger.bind(category=category)


# Export the main logger
logger = loguru_logger


# Convenience loggers
order_logger = get_logger("order")
email_logger = get_logger("email")
robot_logger = get_logger("robot")
