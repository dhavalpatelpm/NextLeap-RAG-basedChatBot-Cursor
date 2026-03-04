"""
Chat service: user message → retrieval → Groq LLM → answer + sources.
"""
from __future__ import annotations

from typing import Any, Optional

from groq import Groq

from src.phase2 import retrieve
from src.phase2.config import RAGConfig

from .config import Phase3Config
from .out_of_scope import is_likely_personal_or_out_of_scope
from .prompts import (
    OUT_OF_SCOPE_MESSAGE,
    SYSTEM_PROMPT,
    build_context_block,
    build_user_message,
)


def _chunks_to_sources(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert retrieved chunks to source entries (cohort_id, text_snippet, source_url)."""
    seen_urls: set[str] = set()
    sources: list[dict[str, Any]] = []
    for c in chunks:
        meta = c.get("metadata") or {}
        url = meta.get("source_url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        sources.append({
            "cohort_id": meta.get("cohort_id", ""),
            "course_name": meta.get("course_name", ""),
            "text_snippet": (c.get("text") or "")[:300] + ("..." if len(c.get("text") or "") > 300 else ""),
            "source_url": url,
        })
    return sources


def chat(
    message: str,
    config: Optional[Phase3Config] = None,
    rag_config: Optional[RAGConfig] = None,
) -> dict[str, Any]:
    """
    Process a user message: optional out-of-scope check → retrieve → Groq → answer + sources.

    Returns:
        {
            "answer": str,
            "sources": [ {"cohort_id", "course_name", "text_snippet", "source_url"} ],
            "out_of_scope": bool,
        }
    """
    cfg = config or Phase3Config()
    rag_cfg = rag_config or RAGConfig()

    if is_likely_personal_or_out_of_scope(message):
        return {
            "answer": OUT_OF_SCOPE_MESSAGE,
            "sources": [],
            "out_of_scope": True,
        }

    chunks = retrieve(
        message,
        top_k=cfg.retrieval_top_k,
        config=rag_cfg,
    )
    context = build_context_block(chunks)
    user_content = build_user_message(message, context)

    client = Groq(api_key=cfg.groq_api_key)
    response = client.chat.completions.create(
        model=cfg.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=512,
    )
    answer = (response.choices[0].message.content or "").strip()
    sources = _chunks_to_sources(chunks)

    return {
        "answer": answer,
        "sources": sources,
        "out_of_scope": False,
    }
