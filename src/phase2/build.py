"""
Build the RAG index: load courses, chunk, embed, persist to Chroma.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .chunker import course_to_chunks
from .config import RAGConfig
from .embedder import get_embedder
from .loader import load_courses_from_course_details
from .store import build_and_persist


def run_phase2(config: Optional[RAGConfig] = None) -> Path:
    """
    Load all courses from course_details, chunk by section, embed, persist to vector store.
    Returns the path to the vector store.
    """
    cfg = config or RAGConfig()
    cfg.vector_store_path = cfg.vector_store_path or (
        Path(__file__).resolve().parent.parent.parent / "data" / "vector_store"
    )
    cfg.vector_store_path.mkdir(parents=True, exist_ok=True)
    all_chunks: list[dict] = []
    for course_key, data, source_url in load_courses_from_course_details():
        all_chunks.extend(course_to_chunks(course_key, data, source_url))
    embedder = get_embedder(cfg.embed_model_name)
    build_and_persist(
        all_chunks,
        embedder,
        cfg.vector_store_path,
        collection_name=cfg.collection_name,
    )
    return cfg.vector_store_path
