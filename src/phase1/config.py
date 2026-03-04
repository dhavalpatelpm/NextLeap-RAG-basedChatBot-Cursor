"""
Phase 1 config: course page URLs and cohort slugs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BASE_URL = "https://nextleap.app"
COURSE_PATH_PREFIX = "/course/"

# Course page path suffixes (URL = BASE_URL + COURSE_PATH_PREFIX + path_suffix)
COURSE_URLS = {
    "product_management": "product-management-course",
    "ux_design": "ui-ux-design-course",
    "data_analytics": "data-analyst-course",
    "business_analytics": "business-analyst-course",
    "genai_bootcamp": "generative-ai-course",
}

# Slug to cohort_id for canonical output
COHORT_IDS = {
    "product_management": "product_manager_fellowship",
    "ux_design": "ui_ux_designer_fellowship",
    "data_analytics": "data_analyst_fellowship",
    "business_analytics": "business_analyst_fellowship",
    "genai_bootcamp": "genai_bootcamp",
}

# Human-readable names
COHORT_NAMES = {
    "product_management": "Product Manager Fellowship",
    "ux_design": "UI/UX Designer Fellowship",
    "data_analytics": "Data Analyst Fellowship",
    "business_analytics": "Business Analyst Fellowship",
    "genai_bootcamp": "Applied Generative AI Bootcamp",
}


@dataclass
class Paths:
    root: Path
    data: Path
    reference: Path
    scraped: Path
    canonical: Path
    course_details: Path

    @classmethod
    def from_repo_root(cls, repo_root: Optional[Path] = None) -> "Paths":
        root = repo_root or Path(__file__).resolve().parent.parent.parent
        data = root / "data"
        return cls(
            root=root,
            data=data,
            reference=data / "reference",
            scraped=data / "scraped",
            canonical=data / "canonical",
            course_details=data / "course_details",
        )


def get_course_url(slug_key: str) -> str:
    path = COURSE_URLS.get(slug_key)
    if not path:
        raise ValueError(f"Unknown cohort key: {slug_key}")
    return f"{BASE_URL}{COURSE_PATH_PREFIX}{path}"
