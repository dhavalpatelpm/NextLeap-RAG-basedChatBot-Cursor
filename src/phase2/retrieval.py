"""
Retrieval API: query → embed → vector search → top-k chunks with metadata (including source_url).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .config import RAGConfig
from .embedder import get_embedder
from .store import load_collection, query_collection


def retrieve(
    query: str,
    top_k: Optional[int] = None,
    cohort_id: Optional[str] = None,
    config: Optional[RAGConfig] = None,
) -> list[dict[str, Any]]:
    """
    Run retrieval: embed query, search vector store, return top-k chunks.
    Each result has "text", "metadata" (course_name, source_url, section, cohort_id), and "distance".
    Optionally filter by cohort_id (e.g. "product_manager_fellowship").
    """
    cfg = config or RAGConfig()
    k = top_k if top_k is not None else cfg.top_k
    if not cfg.vector_store_path or not cfg.vector_store_path.exists():
        return []
    embedder = get_embedder(cfg.embed_model_name)
    query_embedding = embedder.encode(query)
    if isinstance(query_embedding[0], list):
        query_embedding = query_embedding[0]
    collection = load_collection(cfg.vector_store_path, cfg.collection_name)
    where = {"cohort_id": cohort_id} if cohort_id else None
    return query_collection(collection, query_embedding, top_k=k, where=where)
