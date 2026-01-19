"""
DoruMake Scheduler
APScheduler-based job scheduling for background tasks
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config import settings
from src.utils.logger import logger


class Scheduler:
    """
    Background job scheduler

    Manages scheduled tasks like:
    - Health checks
    - Log cleanup
    - Daily reports
    - Screenshot cleanup
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs: List[str] = []

    def start(self):
        """Start the scheduler"""
        logger.info("Starting scheduler...")
        self.scheduler.start()
        self._setup_default_jobs()
        logger.info(f"Scheduler started with {len(self._jobs)} jobs")

    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")

    def _setup_default_jobs(self):
        """Setup default scheduled jobs"""

        # Health check every 5 minutes
        self.add_interval_job(
            self._health_check,
            minutes=5,
            job_id="health_check"
        )

        # Cleanup old screenshots daily at 3 AM
        self.add_cron_job(
            self._cleanup_screenshots,
            hour=3,
            minute=0,
            job_id="cleanup_screenshots"
        )

        # Cleanup old logs weekly on Sunday at 4 AM
        self.add_cron_job(
            self._cleanup_logs,
            day_of_week='sun',
            hour=4,
            minute=0,
            job_id="cleanup_logs"
        )

        # Daily summary report at 6 PM
        self.add_cron_job(
            self._send_daily_report,
            hour=18,
            minute=0,
            job_id="daily_report"
        )

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        seconds: int = None,
        minutes: int = None,
        hours: int = None,
        **kwargs
    ):
        """
        Add job that runs at fixed intervals

        Args:
            func: Function to run
            job_id: Unique job ID
            seconds/minutes/hours: Interval
            **kwargs: Additional args for the function
        """
        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours
        )

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs
        )

        self._jobs.append(job_id)
        logger.debug(f"Added interval job: {job_id}")

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        year: int = None,
        month: int = None,
        day: int = None,
        week: int = None,
        day_of_week: str = None,
        hour: int = None,
        minute: int = None,
        second: int = None,
        **kwargs
    ):
        """
        Add job that runs on a cron schedule

        Args:
            func: Function to run
            job_id: Unique job ID
            Cron fields: year, month, day, week, day_of_week, hour, minute, second
            **kwargs: Additional args for the function
        """
        trigger = CronTrigger(
            year=year,
            month=month,
            day=day,
            week=week,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            second=second
        )

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs
        )

        self._jobs.append(job_id)
        logger.debug(f"Added cron job: {job_id}")

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self._jobs:
                self._jobs.remove(job_id)
            logger.debug(f"Removed job: {job_id}")
        except Exception as e:
            logger.warning(f"Error removing job {job_id}: {e}")

    def get_jobs(self) -> List[dict]:
        """Get list of scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs

    # ============================================
    # DEFAULT JOB HANDLERS
    # ============================================

    async def _health_check(self):
        """Periodic health check"""
        logger.debug("Running health check...")

        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }

        # Check database connection
        try:
            # TODO: Implement actual DB check
            checks["checks"]["database"] = "ok"
        except Exception as e:
            checks["checks"]["database"] = f"error: {e}"
            checks["status"] = "unhealthy"

        # Check email server
        try:
            from src.email.fetcher import EmailFetcher
            fetcher = EmailFetcher()
            await fetcher.connect()
            await fetcher.disconnect()
            checks["checks"]["email"] = "ok"
        except Exception as e:
            checks["checks"]["email"] = f"error: {e}"
            # Email failure is warning, not critical
            if checks["status"] == "healthy":
                checks["status"] = "degraded"

        if checks["status"] != "healthy":
            logger.warning(f"Health check result: {checks}")
        else:
            logger.debug(f"Health check passed: {checks}")

        return checks

    async def _cleanup_screenshots(self):
        """Cleanup old screenshot files"""
        logger.info("Running screenshot cleanup...")
        from pathlib import Path
        import shutil

        screenshot_dir = Path(settings.playwright.screenshot_path)
        if not screenshot_dir.exists():
            return

        cutoff = datetime.now() - timedelta(days=7)  # Keep 7 days
        deleted_count = 0

        for date_dir in screenshot_dir.iterdir():
            if not date_dir.is_dir():
                continue

            try:
                # Parse date from directory name
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff:
                    shutil.rmtree(date_dir)
                    deleted_count += 1
                    logger.debug(f"Deleted screenshot directory: {date_dir}")
            except ValueError:
                continue  # Not a date directory

        logger.info(f"Screenshot cleanup complete. Deleted {deleted_count} directories.")

    async def _cleanup_logs(self):
        """Cleanup old log files (handled by logrotate, but as backup)"""
        logger.info("Running log cleanup...")
        # This is mostly handled by logrotate
        # This is just a backup cleanup
        pass

    async def _send_daily_report(self):
        """Send daily summary report"""
        logger.info("Generating daily report...")

        # TODO: Implement actual report generation
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "orders_processed": 0,
            "orders_successful": 0,
            "orders_failed": 0,
            "emails_processed": 0,
        }

        logger.info(f"Daily report: {report}")

        # TODO: Send notification email
        # from src.notifications.email_notifier import send_daily_report
        # await send_daily_report(report)
