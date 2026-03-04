"""
Phase 2 config: chunk size, embedding model, vector store path, retrieval k.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RAGConfig:
    """Configuration for the RAG pipeline."""

    # Chunking
    chunk_size_tokens: int = 384
    chunk_overlap_tokens: int = 64

    # Embedding
    embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Vector store
    vector_store_path: Optional[Path] = None
    collection_name: str = "nextleap_courses"

    # Retrieval
    top_k: int = 8

    def __post_init__(self) -> None:
        if self.vector_store_path is None:
            root = Path(__file__).resolve().parent.parent.parent
            self.vector_store_path = root / "data" / "vector_store"

    @classmethod
    def from_repo_root(cls, repo_root: Optional[Path] = None, **overrides: object) -> "RAGConfig":
        cfg = cls()
        if repo_root is not None:
            cfg.vector_store_path = repo_root / "data" / "vector_store"
        for k, v in overrides.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg
