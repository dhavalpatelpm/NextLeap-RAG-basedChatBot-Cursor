#!/usr/bin/env python3
"""
Run Phase 5 scheduler: refresh (Phase 1 → Phase 2) on an interval (e.g. every 24h).
For 10 AM daily, use GitHub Actions: .github/workflows/scheduled-refresh.yml

Usage:
  python scripts/run_phase5_scheduler.py
  python scripts/run_phase5_scheduler.py --interval 12   # hours
  python scripts/run_phase5_scheduler.py --run-now       # run immediately on start
  REFRESH_INTERVAL_HOURS=24 python scripts/run_phase5_scheduler.py
"""
import logging
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    import argparse
    p = argparse.ArgumentParser(description="Phase 5: Scheduled data refresh (local/server)")
    p.add_argument("--interval", type=int, default=None, help="Refresh interval in hours (default: 24)")
    p.add_argument("--no-scrape", action="store_true", help="On each run, skip scrape (merge only + Phase 2)")
    p.add_argument("--run-now", action="store_true", help="Run refresh immediately on start, then schedule")
    args = p.parse_args()
    interval = args.interval or int(os.environ.get("REFRESH_INTERVAL_HOURS", "24"))
    if interval < 1:
        logger.error("Interval must be >= 1 hour")
        sys.exit(1)

    from apscheduler.schedulers.blocking import BlockingScheduler
    from src.phase5 import run_refresh

    def job():
        try:
            ok = run_refresh(scrape=not args.no_scrape)
            if not ok:
                logger.warning("Refresh failed; will retry at next scheduled run.")
        except Exception as e:
            logger.exception("Refresh error: %s; will retry at next scheduled run.", e)

    if args.run_now:
        logger.info("Running refresh immediately...")
        job()

    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=interval, id="refresh")
    logger.info("Phase 5 scheduler: refresh every %d hour(s). Press Ctrl+C to stop.", interval)
    scheduler.start()


if __name__ == "__main__":
    main()
