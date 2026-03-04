"""
Out-of-scope detection: personal information and off-topic queries.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# Phrases that suggest the user is asking for personal/private information
PERSONAL_PATTERNS: List[Tuple[str, int]] = [
    (r"\b(what is|what\'s|give me|send me|share)\s+(your|his|her|their)\s+(email|phone|number|address|contact)\b", 1),
    (r"\b(email|phone|mobile|contact)\s+(number|address|details)\s+(of|for)\b", 1),
    (r"\bpersonal\s+(data|information|details)\b", 1),
    (r"\bprivate\s+(information|data|details)\b", 1),
    (r"\b(ssn|social security|aadhaar|passport)\s*(number)?\b", 1),
    (r"\bmy\s+(application\s+status|enrollment\s+status)\b", 1),
    (r"\b(stalk|find)\s+(someone|a person)\b", 1),
]
COMPILED = [(re.compile(p, re.I), w) for p, w in PERSONAL_PATTERNS]


def is_likely_personal_or_out_of_scope(query: str) -> bool:
    """
    Return True if the query appears to ask for personal information or similar out-of-scope content.
    """
    q = (query or "").strip()
    if not q:
        return False
    for pattern, _ in COMPILED:
        if pattern.search(q):
            return True
    return False
