"""
Merge reference + scraped data into canonical course JSON.
Prefer scraped for: instructors, fees, cohort info, schedule, salary (live data).
Prefer reference for: curriculum, tools, learning_style, career_support, etc.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import Paths, COURSE_URLS, COHORT_IDS, COHORT_NAMES
from .schema import (
    CourseData,
    CourseFee,
    CohortInfo,
    Instructor,
    SalaryOutcomes,
    HiringNetwork,
    LiveScheduleSlot,
)


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _reference_key_to_file(reference_key: str) -> str:
    """reference/product_management.json etc."""
    return reference_key + ".json"


def _scraped_key_to_file(scraped_key: str) -> str:
    """scraped/product_management.json etc."""
    return scraped_key + ".json"


def merge_course(
    reference_key: str,
    reference_data: dict | None,
    scraped_data: dict | None,
) -> CourseData:
    """Build one CourseData from reference + scraped. Prefer scraped for live fields."""
    cohort_id = COHORT_IDS.get(reference_key, reference_key)
    course_name = COHORT_NAMES.get(reference_key, reference_key.replace("_", " ").title())
    slug = reference_key.replace("_", "-")

    # Start from reference if present
    base = dict(reference_data) if reference_data else {}
    # Overlay scraped (scraped takes precedence for overlapping keys we care about)
    scraped = dict(scraped_data) if scraped_data else {}

    # Build merged dict with explicit precedence
    merged: dict = {
        "cohort_id": cohort_id,
        "course_name": course_name,
        "slug": slug,
        "provider": base.get("provider", "NextLeap"),
        "category": base.get("category"),
        "type": base.get("type", "Online Fellowship Program"),
        "source": "merged",
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }

    # Duration & hours: prefer scraped
    merged["duration"] = scraped.get("duration") or base.get("duration")
    merged["duration_weeks"] = scraped.get("duration_weeks") or base.get("duration_weeks")
    merged["total_live_hours"] = scraped.get("total_live_hours") or base.get("total_live_hours")
    merged["weekly_hours_min"] = base.get("weekly_hours_min")
    merged["weekly_hours_max"] = base.get("weekly_hours_max")
    merged["format"] = scraped.get("format") or base.get("format")
    merged["fellowship_timeline"] = scraped.get("fellowship_timeline") or base.get("fellowship_timeline")
    merged["mentorship"] = scraped.get("mentorship") or base.get("mentorship")
    merged["class_type"] = base.get("class_type", [])

    # Placement: prefer scraped for detail/current text
    merged["placement_support"] = scraped.get("placement_support") or base.get("placement_support")
    merged["placement_support_years"] = scraped.get("placement_support_years") or base.get("placement_support_years")
    merged["placement_support_detail"] = scraped.get("placement_support_detail") or base.get("placement_support_detail")
    merged["interview_prep_classes"] = base.get("interview_prep_classes")
    merged["career_support"] = base.get("career_support", [])

    # Fee: prefer scraped (current price, EMI, price increase)
    if scraped.get("fee") and isinstance(scraped["fee"], dict):
        fee_dict = dict(scraped["fee"])
        if base.get("fee") and isinstance(base["fee"], dict) and base["fee"].get("discounts"):
            fee_dict.setdefault("discounts", base["fee"]["discounts"])
        merged["fee"] = fee_dict
    elif scraped.get("current_price"):
        merged["fee"] = {
            "current_price": scraped["current_price"],
            "original_price": scraped.get("original_price"),
            "emi_from": scraped.get("emi_from"),
            "price_increase_info": scraped.get("price_increase_info"),
            "discounts": base.get("fee", {}).get("discounts", []) if isinstance(base.get("fee"), dict) else [],
        }
    elif base.get("fee") and isinstance(base["fee"], dict):
        merged["fee"] = base["fee"]
    else:
        merged["course_fee"] = base.get("course_fee")
        merged["emi_options"] = base.get("emi_options")

    # Cohort info: prefer scraped
    merged["cohort_info"] = scraped.get("cohort_info") or base.get("cohort_info")

    # Schedule: prefer scraped live_class_schedule; else reference schedule
    merged["live_class_schedule"] = scraped.get("live_class_schedule") or []
    merged["schedule"] = base.get("schedule", {})

    # Instructors: prefer scraped
    merged["instructors"] = scraped.get("instructors") or base.get("instructors", [])
    merged["learn_from_instructors"] = scraped.get("learn_from_instructors") or base.get("learn_from_instructors", [])

    # Salary: prefer scraped
    merged["average_salary"] = scraped.get("average_salary") or base.get("average_salary")
    merged["highest_salary"] = scraped.get("highest_salary") or base.get("highest_salary")
    merged["salary_outcomes"] = scraped.get("salary_outcomes") or base.get("salary_outcomes")

    # Curriculum, tools, etc.: keep from reference
    merged["curriculum_topics"] = base.get("curriculum_topics", [])
    merged["learning_style"] = base.get("learning_style", [])
    merged["learning_activities"] = base.get("learning_activities", [])
    merged["technical_skills"] = base.get("technical_skills", [])
    merged["tools"] = base.get("tools", [])
    merged["ai_learning_modules"] = base.get("ai_learning_modules", [])
    merged["ai_learning_hours"] = base.get("ai_learning_hours")
    merged["projects"] = base.get("projects", [])
    merged["who_is_this_for"] = base.get("who_is_this_for", [])
    merged["target_roles"] = base.get("target_roles", [])
    merged["unique_features"] = base.get("unique_features", [])
    merged["hiring_network"] = base.get("hiring_network")
    merged["certification"] = base.get("certification")
    merged["graduation_requirement"] = base.get("graduation_requirement", [])
    merged["top_fellow_criteria"] = base.get("top_fellow_criteria")
    merged["community_learning"] = base.get("community_learning", [])
    merged["ai_learning_tools"] = base.get("ai_learning_tools", [])

    # Rich scraped/reference: curriculum by week, program timeline, tools list, reviews, alumni
    merged["curriculum_by_week"] = scraped.get("curriculum_by_week") or base.get("curriculum_by_week") or []
    merged["program_timeline"] = scraped.get("program_timeline") or base.get("program_timeline") or []
    merged["tools_learned"] = scraped.get("tools_learned") or base.get("tools_learned") or base.get("tools", [])
    merged["projects_count"] = scraped.get("projects_count") or base.get("projects_count")
    merged["weekly_commitment"] = scraped.get("weekly_commitment") or base.get("weekly_commitment")
    merged["reviews_summary"] = scraped.get("reviews_summary") or base.get("reviews_summary") or {}
    merged["alumni_support"] = scraped.get("alumni_support") or base.get("alumni_support") or []

    # Normalize certification to string (reference may have dict with type/usage)
    cert = merged.get("certification")
    if isinstance(cert, dict):
        merged["certification"] = cert.get("type") or str(cert)
    elif cert is not None and not isinstance(cert, str):
        merged["certification"] = str(cert)

    # Normalize career_support to list (reference may have dict with services etc.)
    cs = merged.get("career_support")
    if isinstance(cs, dict):
        merged["career_support"] = cs.get("services") if isinstance(cs.get("services"), list) else []

    # Normalize string fields that reference may give as list (e.g. mentorship)
    for key in ("mentorship", "placement_support", "format", "fellowship_timeline"):
        val = merged.get(key)
        if isinstance(val, list):
            merged[key] = ", ".join(str(x) for x in val) if val else None

    # Normalize nested types for Pydantic
    if merged.get("fee") and isinstance(merged["fee"], dict):
        merged["fee"] = CourseFee(**{k: v for k, v in merged["fee"].items() if v is not None})
    if merged.get("cohort_info") and isinstance(merged["cohort_info"], dict):
        merged["cohort_info"] = CohortInfo(**merged["cohort_info"])
    if merged.get("salary_outcomes") and isinstance(merged["salary_outcomes"], dict):
        merged["salary_outcomes"] = SalaryOutcomes(**merged["salary_outcomes"])
    if merged.get("hiring_network") and isinstance(merged["hiring_network"], dict):
        merged["hiring_network"] = HiringNetwork(**merged["hiring_network"])
    instructors = merged.get("instructors") or []
    merged["instructors"] = [Instructor(**(i if isinstance(i, dict) else {"name": str(i), "role": None})) for i in instructors]
    sched = merged.get("live_class_schedule") or []
    merged["live_class_schedule"] = [LiveScheduleSlot(**(s if isinstance(s, dict) else {"day": "", "time": str(s), "description": None})) for s in sched]

    return CourseData(**{k: v for k, v in merged.items() if v is not None or k in ("instructors", "live_class_schedule")})


def run_merge(output_dir: Path | None = None) -> list[Path]:
    """Load all reference + scraped, merge, write canonical JSON per cohort."""
    paths = Paths.from_repo_root()
    ref_dir = paths.reference
    scraped_dir = paths.scraped
    out_dir = output_dir or paths.canonical
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for key in COURSE_URLS.keys():
        ref_path = ref_dir / _reference_key_to_file(key)
        scraped_path = scraped_dir / _scraped_key_to_file(key)
        ref_data = _load_json(ref_path)
        scraped_data = _load_json(scraped_path)
        # If scraped has error key, treat as no scraped data
        if scraped_data and scraped_data.get("error"):
            scraped_data = None
        try:
            course = merge_course(key, ref_data, scraped_data)
            canonical_dict = course.to_canonical_dict()
            # Add any reference-only keys (learning_model, graduation_requirements, portfolio_work, etc.) for RAG
            for ref_key, ref_value in (ref_data or {}).items():
                if ref_key not in canonical_dict and ref_value is not None:
                    canonical_dict[ref_key] = ref_value
            out_path = out_dir / f"{key}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(canonical_dict, f, indent=2, ensure_ascii=False)
            written.append(out_path)
        except Exception as e:
            raise RuntimeError(f"Merge failed for {key}: {e}") from e
    return written


def run_phase1(scrape_first: bool = True, merge_after: bool = True, slug_keys: list[str] | None = None) -> list[Path]:
    """Run full Phase 1: optionally scrape, then merge to canonical."""
    paths = Paths.from_repo_root()
    paths.scraped.mkdir(parents=True, exist_ok=True)
    paths.canonical.mkdir(parents=True, exist_ok=True)
    if scrape_first:
        from .scraper import run_scraper
        run_scraper(slug_keys=slug_keys, output_dir=paths.scraped)
    if merge_after:
        return run_merge(output_dir=paths.canonical)
    return []
