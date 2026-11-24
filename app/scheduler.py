"""In-process APScheduler for 5-minute metric polling."""

from __future__ import annotations

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler(app) -> None:
    """Start once per process. Avoid double-start under Flask reloader."""
    global _scheduler

    if app.config.get("TESTING"):
        return

    # Reloader parent process should not start the scheduler
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    if _scheduler is not None and _scheduler.running:
        return

    interval = int(app.config.get("METRICS_POLL_INTERVAL_SECONDS", 300))
    scheduler = BackgroundScheduler(daemon=True)

    def job():
        with app.app_context():
            from app.metrics_service import collect_all_servers

            collect_all_servers()

    scheduler.add_job(
        job,
        "interval",
        seconds=interval,
        id="collect_metrics",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Metrics scheduler started (every %s seconds)", interval)


def get_poll_interval_seconds(app) -> int:
    return int(app.config.get("METRICS_POLL_INTERVAL_SECONDS", 300))
