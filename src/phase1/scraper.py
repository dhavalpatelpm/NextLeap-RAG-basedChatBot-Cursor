"""
Playwright-based scraper for nextleap.app course pages.
Renders SPA, extracts full page text, then runs structured extraction.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from .config import get_course_url, COURSE_URLS, Paths
from .extract import extract_all
from .schema import CourseData, CourseFee, CohortInfo, Instructor, SalaryOutcomes, LiveScheduleSlot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wait for content to appear (SPA)
PAGE_LOAD_TIMEOUT_MS = 45_000
CONTENT_WAIT_TIMEOUT_MS = 20_000


def get_page_text(page) -> str:
    """Get visible text from the full page (body) so we capture all sections including instructors, schedule, timeline."""
    try:
        return page.locator("body").inner_text(timeout=10000)
    except Exception:
        pass
    selectors = ["main", "[role=main]", "article", "body"]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                return loc.inner_text(timeout=5000)
        except Exception:
            continue
    return ""


def scrape_course_page(url: str, page) -> dict:
    """Scrape a single course URL; return extracted payload (no schema yet)."""
    logger.info("Scraping %s", url)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)
        page.wait_for_load_state("networkidle", timeout=CONTENT_WAIT_TIMEOUT_MS)
    except PlaywrightTimeout:
        logger.warning("Timeout loading %s, continuing with current DOM", url)
    except Exception as e:
        logger.error("Error loading %s: %s", url, e)
        return {"error": str(e), "url": url}

    # Wait for dynamic content and scroll to trigger lazy-loaded sections (instructors, timeline, FAQ)
    page.wait_for_timeout(4000)
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
    except Exception:
        pass

    text = get_page_text(page)
    if len(text) < 200:
        logger.warning("Very little text from %s (%d chars)", url, len(text))

    return extract_all(text)


def scraped_payload_to_course_data(
    slug_key: str,
    scraped: dict,
    course_name: str,
    cohort_id: str,
    slug: str,
) -> CourseData:
    """Convert scraped payload + known identifiers into CourseData (for scraped-only)."""
    fee = None
    if scraped.get("current_price"):
        fee = CourseFee(
            current_price=scraped["current_price"],
            original_price=scraped.get("original_price"),
            emi_from=scraped.get("emi_from"),
            price_increase_info=scraped.get("price_increase_info"),
        )
    cohort_info = None
    if scraped.get("cohort_info"):
        cohort_info = CohortInfo(**scraped["cohort_info"])
    salary = None
    if scraped.get("average_salary") or scraped.get("highest_salary"):
        salary = SalaryOutcomes(
            average_ctc=scraped.get("average_salary"),
            highest_salary=scraped.get("highest_salary"),
        )
    instructors = []
    for i in scraped.get("instructors") or []:
        if isinstance(i, dict):
            instructors.append(Instructor(name=i.get("name", ""), role=i.get("role")))
        else:
            instructors.append(Instructor(name=str(i), role=None))
    schedule_slots = []
    for s in scraped.get("live_class_schedule") or []:
        if isinstance(s, dict):
            schedule_slots.append(
                LiveScheduleSlot(
                    day=s.get("day", ""),
                    time=s.get("time", ""),
                    description=s.get("description"),
                )
            )
    return CourseData(
        cohort_id=cohort_id,
        course_name=course_name,
        slug=slug,
        duration=scraped.get("duration"),
        duration_weeks=scraped.get("duration_weeks"),
        total_live_hours=scraped.get("total_live_hours"),
        fellowship_timeline=scraped.get("fellowship_timeline"),
        mentorship=scraped.get("mentorship"),
        placement_support=scraped.get("placement_support") or ("1 year" if scraped.get("has_placement_1_year") else None),
        placement_support_years="1 year" if scraped.get("has_placement_1_year") else None,
        placement_support_detail=scraped.get("placement_support_detail"),
        fee=fee,
        cohort_info=cohort_info,
        live_class_schedule=schedule_slots,
        instructors=instructors,
        average_salary=scraped.get("average_salary"),
        highest_salary=scraped.get("highest_salary"),
        salary_outcomes=salary,
        curriculum_by_week=scraped.get("curriculum_by_week") or [],
        tools_learned=scraped.get("tools_learned") or [],
        alumni_support=scraped.get("alumni_support") or [],
        projects_count=scraped.get("projects_count"),
        weekly_commitment=scraped.get("weekly_commitment"),
        reviews_summary=scraped.get("reviews_summary") or {},
        source="scraped",
        scraped_raw={k: v for k, v in scraped.items() if k not in {"raw_text_preview", "raw_text_length"}},
    )


def run_scraper(slug_keys: list[str] | None = None, output_dir: Path | None = None) -> list[Path]:
    """Scrape all (or selected) course pages and write JSON to output_dir."""
    from .config import COHORT_IDS, COHORT_NAMES

    paths = Paths.from_repo_root()
    out_dir = output_dir or paths.scraped
    out_dir.mkdir(parents=True, exist_ok=True)
    keys = slug_keys or list(COURSE_URLS.keys())
    written: list[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(PAGE_LOAD_TIMEOUT_MS)
        for key in keys:
            url = get_course_url(key)
            scraped = scrape_course_page(url, page)
            if scraped.get("error"):
                # Still save error payload for debugging
                out_file = out_dir / f"{key}.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump({"url": url, "error": scraped["error"], "partial": scraped}, f, indent=2)
                written.append(out_file)
                continue
            course_name = COHORT_NAMES.get(key, key.replace("_", " ").title())
            cohort_id = COHORT_IDS.get(key, key)
            slug = key.replace("_", "-")
            try:
                course_data = scraped_payload_to_course_data(
                    key, scraped, course_name, cohort_id, slug
                )
                out_file = out_dir / f"{key}.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(course_data.to_canonical_dict(), f, indent=2, ensure_ascii=False)
                written.append(out_file)
            except Exception as e:
                logger.exception("Failed to build CourseData for %s: %s", key, e)
                out_file = out_dir / f"{key}.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump({"url": url, "error": str(e), "scraped": scraped}, f, indent=2)
                written.append(out_file)
        browser.close()

    return written
