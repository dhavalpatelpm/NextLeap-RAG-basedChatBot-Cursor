"""
Load course documents from data/course_details/ (and optionally data/canonical/).
Produces a stream of (course_key, course_data, source_url) for chunking.
"""
from __future__ import annotations

from typing import Any, Iterator

from src.phase1.course_details_loader import (
    get_all_course_keys,
    get_course_data_with_source,
)


def load_courses_from_course_details() -> Iterator[tuple[str, dict[str, Any], str]]:
    """
    Load all courses from data/course_details/.
    Yields (course_key, course_data, source_url) for each course.
    """
    for course_key in get_all_course_keys():
        data, source_url = get_course_data_with_source(course_key)
        if data:
            yield course_key, data, source_url
