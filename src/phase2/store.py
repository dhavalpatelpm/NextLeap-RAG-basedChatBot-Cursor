"""
Chroma vector store: build index from chunks, query by embedding.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings


def build_and_persist(
    chunks: list[dict[str, Any]],
    embedder: Any,
    persist_path: Path,
    collection_name: str = "nextleap_courses",
) -> None:
    """
    Build Chroma collection from chunks (each has "text" and "metadata").
    Embeds texts, stores in Chroma at persist_path.
    """
    if not chunks:
        return
    texts = [c["text"] for c in chunks]
    metadatas = [_metadata_for_chroma(c["metadata"]) for c in chunks]
    ids = [str(uuid.uuid4()) for _ in chunks]
    embeddings = embedder.encode(texts)
    client = chromadb.PersistentClient(path=str(persist_path), settings=Settings(anonymized_telemetry=False))
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = client.create_collection(name=collection_name, metadata={"description": "NextLeap course chunks"})
    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)
    return None


def _metadata_for_chroma(meta: dict) -> dict:
    """Chroma allows only str, int, float, bool in metadata."""
    out = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def load_collection(persist_path: Path, collection_name: str = "nextleap_courses"):
    """Return Chroma collection for querying."""
    client = chromadb.PersistentClient(path=str(persist_path), settings=Settings(anonymized_telemetry=False))
    return client.get_collection(name=collection_name)


def query_collection(
    collection: Any,
    query_embedding: list[float],
    top_k: int = 8,
    where: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """
    Query Chroma by embedding. Returns list of dicts with document, metadata, distance.
    where: optional filter e.g. {"cohort_id": "product_manager_fellowship"}.
    """
    kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where is not None:
        kwargs["where"] = where
    result = collection.query(**kwargs)
    # result keys: ids, documents, metadatas, distances (each list of lists)
    out: list[dict[str, Any]] = []
    docs = (result.get("documents") or [[]])[0] or []
    metadatas = (result.get("metadatas") or [[]])[0] or []
    distances = (result.get("distances") or [[]])[0] or []
    for i, doc in enumerate(docs):
        out.append({
            "text": doc,
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "distance": distances[i] if i < len(distances) else None,
        })
    return out
