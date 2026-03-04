#!/usr/bin/env python3
"""
Run Phase 5 data refresh: Phase 1 (scrape + merge) → sync to course_details → Phase 2 (rebuild RAG).
Use for cron or manual run. On success writes data/.last_refresh.
Usage:
  python scripts/run_phase5_refresh.py           # full refresh (scrape + merge + Phase 2)
  python scripts/run_phase5_refresh.py --no-scrape   # merge only (no scrape) + sync + Phase 2
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))


def main():
    import argparse
    p = argparse.ArgumentParser(description="Phase 5: Data refresh (Phase 1 → sync → Phase 2)")
    p.add_argument("--no-scrape", action="store_true", help="Skip scrape; merge only then Phase 2")
    args = p.parse_args()
    from src.phase5 import run_refresh
    ok = run_refresh(scrape=not args.no_scrape)
    if not ok:
        sys.exit(1)
    print("Phase 5 refresh complete. RAG index updated.")


if __name__ == "__main__":
    main()
