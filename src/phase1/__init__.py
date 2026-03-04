"""Phase 1: Data ingestion from nextleap.app (scrape + merge → canonical)."""
from .config import Paths, get_course_url, COURSE_URLS, COHORT_IDS, COHORT_NAMES
from .schema import CourseData, CourseFee, Instructor, SalaryOutcomes
from .scraper import run_scraper
from .merge import run_merge, run_phase1

__all__ = [
    "Paths",
    "get_course_url",
    "COURSE_URLS",
    "COHORT_IDS",
    "COHORT_NAMES",
    "CourseData",
    "CourseFee",
    "Instructor",
    "SalaryOutcomes",
    "run_scraper",
    "run_merge",
    "run_phase1",
]
