#!/usr/bin/env python3
"""
Run Phase 1: scrape nextleap.app course pages and merge with reference data into canonical JSON.
Usage:
  python scripts/run_phase1.py              # scrape all + merge
  python scripts/run_phase1.py --no-scrape  # merge only (use existing scraped/)
  python scripts/run_phase1.py --scrape-only  # scrape only, do not merge
  python scripts/run_phase1.py --cohorts product_management ux_design  # limit cohorts
"""
import sys
from pathlib import Path

# Add repo root so "src" is importable
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.phase1 import run_phase1, run_scraper, run_merge


def main():
    import argparse
    p = argparse.ArgumentParser(description="Phase 1: Data ingestion (scrape + merge)")
    p.add_argument("--no-scrape", action="store_true", help="Skip scraping; only merge from existing data/scraped/")
    p.add_argument("--scrape-only", action="store_true", help="Only scrape; do not merge")
    p.add_argument("--cohorts", nargs="*", help="Cohort keys to run (default: all). e.g. product_management ux_design")
    args = p.parse_args()
    cohort_keys = args.cohorts if args.cohorts else None
    if args.scrape_only:
        run_scraper(slug_keys=cohort_keys)
        print("Scrape complete. Output in data/scraped/")
        return
    if args.no_scrape:
        paths = run_merge()
    else:
        paths = run_phase1(scrape_first=True, merge_after=True, slug_keys=cohort_keys)
    print("Phase 1 complete. Canonical output:", [str(p) for p in paths])


if __name__ == "__main__":
    main()
