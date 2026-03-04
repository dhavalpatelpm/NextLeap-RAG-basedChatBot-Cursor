#!/usr/bin/env python3
"""
Run Phase 5 scheduler: refresh (Phase 1 → Phase 2) on an interval (e.g. every 24h).
Usage:
  python scripts/run_phase5_scheduler.py
  python scripts/run_phase5_scheduler.py --interval 12   # hours
  REFRESH_INTERVAL_HOURS=24 python scripts/run_phase5_scheduler.py
"""
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))


def main():
    import argparse
    p = argparse.ArgumentParser(description="Phase 5: Scheduled data refresh")
    p.add_argument("--interval", type=int, default=None, help="Refresh interval in hours (default: 24)")
    p.add_argument("--no-scrape", action="store_true", help="On each run, skip scrape (merge only + Phase 2)")
    args = p.parse_args()
    interval = args.interval or int(os.environ.get("REFRESH_INTERVAL_HOURS", "24"))

    from apscheduler.schedulers.blocking import BlockingScheduler
    from src.phase5 import run_refresh

    def job():
        run_refresh(scrape=not args.no_scrape)

    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=interval, id="refresh")
    print(f"Phase 5 scheduler: refresh every {interval} hour(s). Press Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
