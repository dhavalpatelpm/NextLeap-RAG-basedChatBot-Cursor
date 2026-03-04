"""
Extract structured fields from scraped course page text/HTML.
Uses regex and simple parsing for the important data points.
"""
from __future__ import annotations

import re
from typing import Any


def extract_price_and_emi(text: str) -> dict[str, Any]:
    """Extract current price, original price, EMI, and price increase info."""
    out: dict[str, Any] = {}
    # ₹34,999 or ₹49,999 (with optional comma)
    prices = re.findall(r"₹\s*([\d,]+)", text)
    if prices:
        # Often two prices: discounted first, original second
        clean = [p.replace(",", "") for p in prices]
        if len(clean) >= 2:
            out["current_price"] = f"₹{clean[0]}"
            out["original_price"] = f"₹{clean[1]}"
        else:
            out["current_price"] = f"₹{clean[0]}"
    # EMI from ₹1,577/month or ₹1322/month
    emi = re.search(r"EMI\s+from\s+₹\s*([\d,]+)/month", text, re.I)
    if emi:
        out["emi_from"] = f"₹{emi.group(1).replace(',', '')}/month"
    else:
        emi2 = re.search(r"₹\s*([\d,]+)/month", text)
        if emi2:
            out["emi_from"] = f"₹{emi2.group(1).replace(',', '')}/month"
    # Price increase from 8 Mar 11:59 PM
    inc = re.search(r"Price\s+increase\s+from\s+([^.]+?)(?:\s|$|\.)", text, re.I)
    if inc:
        out["price_increase_info"] = ("Price increase from " + inc.group(1)).strip()
    return out


def extract_duration_and_hours(text: str) -> dict[str, Any]:
    """Extract duration (weeks/months) and live hours."""
    out: dict[str, Any] = {}
    # 100+ Hours, 60+ Hours Live Classes, 4 months
    hours = re.search(r"(\d+\+?)\s*[Hh]ours?\s*(?:Live|live)?", text)
    if hours:
        out["total_live_hours"] = hours.group(1) + (" hours" if not hours.group(1).endswith("+") else "+ hours")
    # 8-10 Hours Weekly commitment
    weekly = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*[Hh]ours?\s*(?:Weekly|weekly)?", text)
    if weekly:
        out["weekly_commitment"] = f"{weekly.group(1)}-{weekly.group(2)} hours/week"
        try:
            out["weekly_hours_min"] = int(weekly.group(1))
            out["weekly_hours_max"] = int(weekly.group(2))
        except ValueError:
            pass
    # 4 months or 16 weeks or 10 weeks (Program timeline)
    months = re.search(r"(\d+)\s*months?", text, re.I)
    if months:
        out["fellowship_timeline"] = months.group(1) + " months"
    weeks = re.search(r"(\d+)\s*weeks?", text, re.I)
    if weeks:
        out["duration"] = weeks.group(1) + " weeks"
        try:
            out["duration_weeks"] = int(weeks.group(1))
        except ValueError:
            pass
    # 10+ Projects
    proj = re.search(r"(\d+\+?)\s*[Pp]rojects?", text)
    if proj:
        out["projects_count"] = proj.group(1) + (" Projects" if not proj.group(1).endswith("+") else "+ Projects")
    return out


def extract_cohort_info(text: str) -> dict[str, Any] | None:
    """Extract cohort number and start date."""
    # Cohort 48 starts on Apr 4, Cohort 3 starts on
    m = re.search(r"Cohort\s+(\d+)\s+starts?\s+on\s*(\w+\s+\d+|\d+\s+\w+)?", text, re.I)
    if m:
        return {"cohort_number": m.group(1), "starts_on": (m.group(2) or "").strip() or None}
    return None


def extract_salary(text: str) -> dict[str, Any]:
    """Extract average and highest salary mentions."""
    out: dict[str, Any] = {}
    # Average PM Salary -> 14-18 Lakhs or Average ... 14-18 Lakhs
    avg = re.search(r"(?:Average|Avg\.?)\s*(?:\w+\s+)?[Ss]alary\s*[:\-–>]*\s*(\d+(?:\s*[-–]\s*\d+)?\s*Lakhs?)", text, re.I)
    if avg:
        out["average_salary"] = (avg.group(1) + " Lakhs") if "Lakh" not in avg.group(1) else avg.group(1)
    else:
        avg2 = re.search(r"(\d+\s*[-–]\s*\d+)\s*Lakhs?", text)
        if avg2 and "salary" in text.lower()[:text.lower().index(avg2.group(0)) + 200]:
            out["average_salary"] = avg2.group(0)
    # Highest Salary at NextLeap -> 31 Lakhs
    high = re.search(r"Highest\s+[Ss]alary\s*(?:at\s+NextLeap)?\s*[:\-–>]*\s*(\d+)\s*Lakhs?", text, re.I)
    if high:
        out["highest_salary"] = high.group(1) + " Lakhs"
    return out


def extract_placement_detail(text: str) -> str | None:
    """Extract placement support detail (cut-off, partner companies)."""
    # Clear the cut-off marks in your graduation project to get access to jobs at our partner companies
    m = re.search(
        r"Clear\s+the\s+cut-off\s+marks[^.]+(?:partner\s+companies)?\.?",
        text,
        re.I | re.DOTALL,
    )
    if m:
        return m.group(0).strip().rstrip(".")
    if "1 year" in text and "placement" in text.lower():
        return "1 year placement support for top fellows; clear cut-off in graduation project for partner company access."
    return None


def extract_schedule_section(text: str) -> list[dict[str, Any]]:
    """Try to get Live Class Schedule as list of day/time/description."""
    schedule: list[dict[str, Any]] = []
    lower = text.lower()
    # Every Saturday 2 Live Classes 10:30 AM - 12:30 PM & 2:00 PM - 4:00 PM IST
    for day in ["saturday", "sunday", "wednesday", "thursday", "weekday"]:
        pat = re.compile(
            rf"(?:every\s+)?{day}\s*[:\-]?\s*([\d:]+?\s*[AP]M\s*[-–]\s*[\d:]+?\s*[AP]M)(?:\s*&\s*)?\s*([\d:]+?\s*[AP]M\s*[-–]\s*[\d:]+?\s*[AP]M)?\s*([^\n]*)",
            re.I,
        )
        for m in pat.finditer(text):
            time_str = m.group(1)
            if m.group(2):
                time_str += " & " + m.group(2)
            schedule.append({"day": day, "time": time_str, "description": (m.group(3) or "").strip() or None})
    if not schedule and "saturday" in lower:
        # Fallback: any AM/PM range
        for day in ["saturday", "sunday", "thursday", "wednesday"]:
            pat = re.compile(
                rf"{day}\s*[:\-]?\s*([\d:]+?\s*[AP]M\s*[-–]\s*[\d:]+?\s*[AP]M)\s*([^\n]*)",
                re.I,
            )
            for m in pat.finditer(text):
                schedule.append({"day": day, "time": m.group(1), "description": m.group(2).strip() or None})
    return schedule


def extract_instructors_from_text(text: str) -> list[dict[str, Any]]:
    """Extract instructor names/roles from 'Learn Concepts From Our Instructors' or similar."""
    instructors: list[dict[str, Any]] = []
    # Section header then names; often names are in cards or list items
    # Fallback: look for "Instructor" or "Mentor" near names (Title Case words that might be names)
    # Simple heuristic: lines that look like "Name - Role" or "Name, Role" after "Instructor" section
    idx = text.lower().find("instructor")
    if idx >= 0:
        block = text[idx : idx + 2000]
        # Pattern: "Name" or "Name - Role" or "Name, Role"
        for line in block.split("\n"):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            # Skip if it's clearly a heading or number
            if re.match(r"^[\d\.\-\*]+$", line) or len(line) > 80:
                continue
            # Could be "Full Name - Lead Instructor"
            if " - " in line or "," in line:
                parts = re.split(r"\s+-\s+|\s*,\s*", line, 1)
                if len(parts) >= 2 and 2 < len(parts[0]) < 50:
                    instructors.append({"name": parts[0].strip(), "role": parts[1].strip()})
    return instructors


def extract_curriculum_weeks(text: str) -> list[dict[str, Any]]:
    """Extract week-by-week curriculum (What Will You Learn, Week 1, Week 2, ...)."""
    weeks: list[dict[str, Any]] = []
    # Week N or Week N & M ... Topics ... Tools you will learn ...
    for m in re.finditer(r"Week\s+(\d+(?:\s*&\s*\d+)?)\s*(.*?)(?=Week\s+\d+|Tools you will learn|BONUS|$)", text, re.I | re.DOTALL):
        week_num = m.group(1).strip()
        block = m.group(2).strip()
        topics: list[str] = []
        tools: list[str] = []
        for line in block.split("\n"):
            line = line.strip()
            if not line or len(line) < 2:
                continue
            if "tools you will learn" in line.lower():
                continue
            if re.match(r"^[A-Za-z][a-zA-Z0-9.]*(AI|ML|API|SDK|RAG|LLM|MCP|CoT|STT|TTS|UX)$", line) or (line.endswith("AI") and len(line) < 25):
                tools.append(line)
            elif 5 < len(line) < 120 and not line.startswith("http"):
                topics.append(line)
        if week_num or topics or tools:
            weeks.append({"week": week_num, "topics": topics[:15], "tools": tools[:10]})
    return weeks


def extract_tools_list(text: str) -> list[str]:
    """Extract tool names from 'Tools You Will Learn' or 'Tools you will learn' sections."""
    tools: list[str] = []
    # Common tool names on NextLeap pages
    known_tools = [
        "Cursor", "FastAPI", "OpenAI", "HuggingFace", "LangChain", "n8n", "Crew.ai", "LangGraph",
        "promptfoo", "TruLens", "Deepgram", "ElevenLabs", "Loveable AI", "Figma", "Gemini", "RunwayML",
        "bolt.new", "Emergent", "MidJourney", "Google Gemini", "CursorAI", "ClaudeAI",
        "JIRA", "Tableau", "Excel", "SQL", "Python", "Pandas", "NumPy", "Whimsical", "Hotjar",
        "Microsoft Clarity", "Google Analytics",
    ]
    lower = text.lower()
    for t in known_tools:
        if t.lower() in lower:
            tools.append(t)
    # Also capture TitleCase words after "Tools you will learn" or "Tools You Will Learn"
    idx = lower.find("tools you will learn")
    if idx >= 0:
        block = text[idx : idx + 1500]
        for t in known_tools:
            if t in block and t not in tools:
                tools.append(t)
    return list(dict.fromkeys(tools))


def extract_reviews_mention(text: str) -> dict[str, Any]:
    """Extract reviews summary or rating mentions."""
    out: dict[str, Any] = {}
    if "review" in text.lower():
        out["has_reviews_section"] = True
        # "Reviews Summary" or rating pattern
        m = re.search(r"(\d+\.?\d*)\s*\/\s*5|(\d+)\s*stars?", text, re.I)
        if m:
            out["rating"] = m.group(1) or m.group(2)
    return out


def extract_alumni_support(text: str) -> list[str]:
    """Extract alumni support items (Job Board, Resume Reviews, AI Interviewer, etc.)."""
    support: list[str] = []
    keywords = ["Alumni Job Board", "Resume", "Portfolio Reviews", "AI Interviewer", "mock interviews", "curated jobs"]
    for k in keywords:
        if k.lower() in text.lower():
            support.append(k)
    return support


def extract_all(text: str) -> dict[str, Any]:
    """Run all extractors and return a single scraped payload."""
    payload: dict[str, Any] = {
        "raw_text_preview": text[:8000] if len(text) > 8000 else text,
        "raw_text_length": len(text),
    }
    payload.update(extract_price_and_emi(text))
    payload.update(extract_duration_and_hours(text))
    cohort = extract_cohort_info(text)
    if cohort:
        payload["cohort_info"] = cohort
    payload.update(extract_salary(text))
    pd = extract_placement_detail(text)
    if pd:
        payload["placement_support_detail"] = pd
    sched = extract_schedule_section(text)
    if sched:
        payload["live_class_schedule"] = sched
    instr = extract_instructors_from_text(text)
    if instr:
        payload["instructors"] = instr
    curriculum_w = extract_curriculum_weeks(text)
    if curriculum_w:
        payload["curriculum_by_week"] = curriculum_w
    tools_list = extract_tools_list(text)
    if tools_list:
        payload["tools_learned"] = tools_list
    payload.update(extract_reviews_mention(text))
    alumni = extract_alumni_support(text)
    if alumni:
        payload["alumni_support"] = alumni
    # Booleans for key phrases
    payload["has_100_plus_hours"] = "100+" in text or "100 +" in text
    payload["has_placement_1_year"] = "1 year" in text and "placement" in text.lower()
    payload["has_mentorship"] = "mentorship" in text.lower() or "mentor" in text.lower()
    return payload
