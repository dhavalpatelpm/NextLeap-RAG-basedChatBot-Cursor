"""
Load course data from data/course_details/ (one folder per course).
Use this so answers can be fetched from the relevant course folder and source_url returned with every response.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Tuple

from .config import Paths, COURSE_URLS


def _load_index() -> dict[str, Any]:
    paths = Paths.from_repo_root()
    index_path = paths.course_details / "index.json"
    if not index_path.exists():
        return {"courses": {}}
    with open(index_path, encoding="utf-8") as f:
        return json.load(f)


def get_source_url(course_key: str) -> str:
    """Return the course page URL for a given course key. Include this in every answer."""
    index = _load_index()
    course_meta = index.get("courses", {}).get(course_key)
    if course_meta and course_meta.get("source_url"):
        return course_meta["source_url"]
    # Fallback from config
    from .config import get_course_url
    return get_course_url(course_key)


def get_course_data(course_key: str) -> Optional[dict]:
    """Load full course.json for one course from course_details/<key>/course.json."""
    paths = Paths.from_repo_root()
    course_path = paths.course_details / course_key / "course.json"
    if not course_path.exists():
        return None
    with open(course_path, encoding="utf-8") as f:
        return json.load(f)


def get_all_course_keys() -> list[str]:
    """Return list of course keys (product_management, ux_design, etc.)."""
    return list(COURSE_URLS.keys())


def get_course_data_with_source(course_key: str) -> Tuple[Optional[dict], str]:
    """Return (course_data, source_url) for the given course. Use source_url in the response."""
    data = get_course_data(course_key)
    url = get_source_url(course_key)
    return data, url
