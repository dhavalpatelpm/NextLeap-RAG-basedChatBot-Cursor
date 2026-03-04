"""
Chunk course data by semantic sections (overview, fee, instructors, curriculum, etc.).
Each chunk has text + metadata: cohort_id, section, source_url, course_name.
"""
from __future__ import annotations

from typing import Any

# Section names used as metadata for filtering
SECTION_OVERVIEW = "overview"
SECTION_FEE = "fee"
SECTION_INSTRUCTORS = "instructors"
SECTION_CURRICULUM = "curriculum"
SECTION_SCHEDULE = "schedule"
SECTION_CAREER = "career_outcomes"
SECTION_TOOLS = "tools"
SECTION_PLATFORM = "platform"
SECTION_ELIGIBILITY = "eligibility"
SECTION_FEATURES = "features"


def _fmt(obj: Any) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, (int, float)):
        return str(obj)
    if isinstance(obj, list):
        return " ".join(_fmt(x) for x in obj)
    if isinstance(obj, dict):
        return " ".join(f"{k}: {_fmt(v)}" for k, v in obj.items())
    return str(obj)


def _text_overview(data: dict[str, Any]) -> str:
    parts = [
        f"Course: {data.get('course_name', '')}.",
        f"Provider: {data.get('provider', '')}.",
        f"Category: {data.get('category', '')}.",
        f"Type: {data.get('type', '')}.",
        f"Duration: {data.get('duration', '')} ({data.get('timeline', '')}).",
        f"Live classes: {data.get('live_classes', data.get('total_live_hours', ''))}.",
        f"Weekly commitment: {data.get('weekly_commitment', '')}.",
        f"Format: {data.get('format', '')}.",
        f"Mentorship: {data.get('mentorship', '')}.",
        f"Placement support: {data.get('placement_support', '')}.",
        f"Class type: {_fmt(data.get('class_type', []))}.",
        f"Learning style: {_fmt(data.get('learning_style', []))}.",
    ]
    if data.get("cohort"):
        parts.append(f"Cohort: {data['cohort']}.")
    return " ".join(p for p in parts if p.strip())


def _text_fee(data: dict[str, Any]) -> str:
    fee = data.get("fee") or {}
    parts = [
        f"Course fee: {data.get('course_fee', fee.get('current_price', ''))}.",
        f"Original price: {fee.get('original_price', '')}.",
        f"EMI from: {data.get('emi_options', fee.get('emi_from', ''))}.",
    ]
    if fee.get("discounts"):
        parts.append(f"Discounts: {', '.join(fee['discounts'])}.")
    if fee.get("price_increase_info"):
        parts.append(fee["price_increase_info"])
    return " ".join(p for p in parts if p.strip())


def _text_instructors(data: dict[str, Any]) -> str:
    instructors = data.get("instructors") or []
    parts = [f"Instructors: {len(instructors)} instructors."]
    for i in instructors:
        parts.append(f"{i.get('name', '')}: {i.get('role', '')}.")
    return " ".join(parts)


def _text_curriculum(data: dict[str, Any]) -> str:
    parts = []
    topics = data.get("curriculum_topics") or []
    if topics:
        parts.append("Curriculum topics: " + ", ".join(topics) + ".")
    weekly = data.get("weekly_curriculum") or []
    for w in weekly[:5]:  # first 5 weeks in one chunk
        parts.append(f"Week {w.get('week', '')}: {w.get('topic', '')}. Concepts: {', '.join(w.get('concepts', []))}.")
    if len(weekly) > 5:
        parts.append(f"Weeks 6-{weekly[-1].get('week', '')}: further curriculum (see full course).")
    if data.get("ai_learning_modules"):
        parts.append("AI modules: " + ", ".join(data["ai_learning_modules"]) + ".")
    if data.get("technical_skills"):
        parts.append("Technical skills: " + ", ".join(data["technical_skills"]) + ".")
    return " ".join(parts) if parts else "Curriculum: see course page."


def _text_curriculum_weeks(data: dict[str, Any]) -> list[str]:
    """Optional: one chunk per later weeks if we want more granular retrieval."""
    weekly = data.get("weekly_curriculum") or []
    if len(weekly) <= 5:
        return []
    texts = []
    for w in weekly[5:]:
        t = f"Week {w.get('week', '')}: {w.get('topic', '')}. Concepts: {', '.join(w.get('concepts', []))}."
        if w.get("case_studies"):
            t += f" Case studies: {', '.join(w['case_studies'])}."
        texts.append(t)
    return texts


def _text_schedule(data: dict[str, Any]) -> str:
    s = data.get("schedule") or {}
    parts = ["Schedule:"]
    for day, items in s.items():
        if isinstance(items, list):
            parts.append(f"{day}: {'; '.join(items)}.")
        else:
            parts.append(f"{day}: {items}.")
    return " ".join(parts)


def _text_career(data: dict[str, Any]) -> str:
    co = data.get("career_outcomes") or {}
    so = data.get("salary_outcomes") or {}
    parts = [
        f"Successful transitions: {co.get('successful_transitions', data.get('successful_transitions', ''))}.",
        f"Average salary: {co.get('average_pm_salary', so.get('average_ctc', data.get('average_salary', '')))}.",
        f"Highest salary: {co.get('highest_salary', so.get('highest_salary', data.get('highest_salary', '')))}.",
        f"Job titles: {', '.join(co.get('job_titles', data.get('target_roles', [])))}.",
    ]
    if data.get("career_support"):
        parts.append(f"Career support: {', '.join(data['career_support'])}.")
    if data.get("placement_support_detail"):
        parts.append(data["placement_support_detail"])
    return " ".join(p for p in parts if p.strip())


def _text_tools(data: dict[str, Any]) -> str:
    tools = data.get("tools_covered") or data.get("tools") or []
    return "Tools covered: " + ", ".join(tools) + "." if tools else ""


def _text_platform(data: dict[str, Any]) -> str:
    p = data.get("platform") or {}
    return f"Platform: {p.get('name', '')}. {p.get('description', '')} Learners: {p.get('learners', '')}. {_fmt(p.get('awards', []))}"


def _text_eligibility(data: dict[str, Any]) -> str:
    who = data.get("who_is_this_for") or []
    roles = data.get("target_roles") or []
    return f"Who is this for: {', '.join(who)}. Target roles: {', '.join(roles)}."


def _text_features(data: dict[str, Any]) -> str:
    parts = []
    if data.get("unique_features"):
        parts.append("Unique features: " + ", ".join(data["unique_features"]) + ".")
    if data.get("projects"):
        parts.append("Projects: " + ", ".join(data["projects"]) + ".")
    if data.get("learning_activities"):
        parts.append("Learning activities: " + ", ".join(data["learning_activities"]) + ".")
    if data.get("certification"):
        c = data["certification"]
        cert_text = c.get("type", str(c)) if isinstance(c, dict) else str(c)
        parts.append(f"Certification: {cert_text}.")
    return " ".join(parts) if parts else ""


def course_to_chunks(course_key: str, data: dict[str, Any], source_url: str) -> list[dict[str, Any]]:
    """
    Convert one course into section-based chunks with text and metadata.
    Returns list of {"text": str, "metadata": {cohort_id, section, source_url, course_name}}.
    """
    course_name = data.get("course_name", course_key)
    cohort_id = data.get("cohort_id", course_key)
    chunks: list[dict[str, Any]] = []

    def add(section: str, text: str) -> None:
        if not (text and text.strip()):
            return
        chunks.append({
            "text": text.strip(),
            "metadata": {
                "cohort_id": cohort_id,
                "section": section,
                "source_url": source_url,
                "course_name": course_name,
                "course_key": course_key,
            },
        })

    add(SECTION_OVERVIEW, _text_overview(data))
    add(SECTION_FEE, _text_fee(data))
    add(SECTION_INSTRUCTORS, _text_instructors(data))
    add(SECTION_CURRICULUM, _text_curriculum(data))
    for extra in _text_curriculum_weeks(data):
        add(SECTION_CURRICULUM, extra)
    add(SECTION_SCHEDULE, _text_schedule(data))
    add(SECTION_CAREER, _text_career(data))
    add(SECTION_TOOLS, _text_tools(data))
    add(SECTION_PLATFORM, _text_platform(data))
    add(SECTION_ELIGIBILITY, _text_eligibility(data))
    add(SECTION_FEATURES, _text_features(data))

    return chunks
