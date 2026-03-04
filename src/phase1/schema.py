"""
Pydantic schemas for Phase 1 course/cohort data.
Matches the deep structured format needed for RAG and the important live data from nextleap.app.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Instructor(BaseModel):
    name: str
    role: Optional[str] = None
    image_url: Optional[str] = None


class SalaryOutcomes(BaseModel):
    average_ctc: Optional[str] = None  # e.g. "14-18 Lakhs" or "12-14 LPA"
    highest_salary: Optional[str] = None  # e.g. "31 Lakhs"
    note: Optional[str] = None


class HiringNetwork(BaseModel):
    hiring_partners: Optional[str] = None  # e.g. "20+ opportunities per month"
    companies: list = Field(default_factory=list)  # list[str]


class CourseFee(BaseModel):
    current_price: str  # e.g. "₹34,999"
    original_price: Optional[str] = None  # e.g. "₹49,999"
    emi_from: Optional[str] = None  # e.g. "₹1,577/month"
    price_increase_info: Optional[str] = None  # e.g. "Price increase from 8 Mar 11:59 PM"
    discounts: list = Field(default_factory=list)  # list[str]


class LiveScheduleSlot(BaseModel):
    day: str
    time: str
    description: Optional[str] = None


class CohortInfo(BaseModel):
    cohort_number: Optional[str] = None  # e.g. "48"
    starts_on: Optional[str] = None  # e.g. "Apr 4"


class CourseData(BaseModel):
    """Canonical course/cohort data for RAG. Supports both reference and scraped sources."""

    # Identifiers
    cohort_id: str
    course_name: str
    slug: str
    provider: str = "NextLeap"
    category: Optional[str] = None
    type: Optional[str] = "Online Fellowship Program"

    # Duration & commitment (important)
    duration: Optional[str] = None  # e.g. "16 weeks"
    duration_weeks: Optional[int] = None
    total_live_hours: Optional[str] = None  # e.g. "100+ hours"
    weekly_hours_min: Optional[int] = None
    weekly_hours_max: Optional[int] = None
    format: Optional[str] = None  # e.g. "Live online classes"

    # Fellowship timeline & mentorship (important)
    fellowship_timeline: Optional[str] = None  # e.g. "4 months"
    mentorship: Optional[str] = None  # e.g. "With experienced PMs"
    class_type: list = Field(default_factory=list)

    # Placement (important)
    placement_support: Optional[str] = None  # e.g. "Support for 1 year"
    placement_support_years: Optional[str] = None  # e.g. "1 year"
    placement_support_detail: Optional[str] = None  # e.g. cut-off marks, partner companies
    interview_prep_classes: Optional[str] = None
    career_support: list = Field(default_factory=list)

    # Cohort & pricing (important)
    cohort_info: Optional[CohortInfo] = None
    fee: Optional[CourseFee] = None
    course_fee: Optional[str] = None  # legacy field
    emi_options: Optional[str] = None

    # Live class schedule (important)
    live_class_schedule: list = Field(default_factory=list)
    schedule: dict = Field(default_factory=dict)

    # Instructors (important)
    instructors: list = Field(default_factory=list)
    learn_from_instructors: list = Field(default_factory=list)

    # Salary outcomes (important)
    salary_outcomes: Optional[SalaryOutcomes] = None
    average_salary: Optional[str] = None  # e.g. "14-18 Lakhs"
    highest_salary: Optional[str] = None  # e.g. "31 Lakhs"

    # Curriculum & learning
    curriculum_topics: list = Field(default_factory=list)
    learning_style: list = Field(default_factory=list)
    learning_activities: list = Field(default_factory=list)
    technical_skills: list = Field(default_factory=list)
    tools: list = Field(default_factory=list)
    ai_learning_modules: list = Field(default_factory=list)
    ai_learning_hours: Optional[str] = None
    projects: list = Field(default_factory=list)
    who_is_this_for: list = Field(default_factory=list)
    target_roles: list = Field(default_factory=list)
    unique_features: list = Field(default_factory=list)

    # Hiring & certification
    hiring_network: Optional[HiringNetwork] = None
    certification: Optional[str] = None
    graduation_requirement: list = Field(default_factory=list)
    top_fellow_criteria: Optional[str] = None
    community_learning: list = Field(default_factory=list)
    ai_learning_tools: list = Field(default_factory=list)

    # Rich scraped/reference (curriculum by week, program timeline, tools list, reviews, alumni)
    curriculum_by_week: list = Field(default_factory=list)
    program_timeline: list = Field(default_factory=list)
    tools_learned: list = Field(default_factory=list)
    projects_count: Optional[str] = None  # e.g. "10+ Projects"
    weekly_commitment: Optional[str] = None  # e.g. "8-10 Hours"
    reviews_summary: dict = Field(default_factory=dict)
    alumni_support: list = Field(default_factory=list)

    # Meta
    source: str = "merged"  # reference | scraped | merged
    last_updated: Optional[str] = None
    scraped_raw: dict = Field(default_factory=dict, exclude=True)

    model_config = {"extra": "allow"}

    def to_canonical_dict(self) -> dict[str, Any]:
        """Export for canonical JSON (excludes internal fields)."""
        d = self.model_dump(exclude={"scraped_raw"}, exclude_none=True)
        if self.fee:
            d["fee"] = self.fee.model_dump(exclude_none=True)
        if self.cohort_info:
            d["cohort_info"] = self.cohort_info.model_dump(exclude_none=True)
        if self.salary_outcomes:
            d["salary_outcomes"] = self.salary_outcomes.model_dump(exclude_none=True)
        if self.hiring_network:
            d["hiring_network"] = self.hiring_network.model_dump(exclude_none=True)
        return d
