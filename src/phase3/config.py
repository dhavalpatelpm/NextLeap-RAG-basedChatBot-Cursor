"""
Phase 3 config: Groq API key and model from environment (.env).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def _load_dotenv() -> None:
    """Load .env from repo root if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env")
    except ImportError:
        pass


def get_groq_api_key() -> str:
    """Return Groq API key from environment. Loads .env first."""
    _load_dotenv()
    import os
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GROQ_API_KEY is not set. Create a .env file (see .env.example) with GROQ_API_KEY=your_key"
        )
    return key


def get_groq_model() -> str:
    """Return Groq model name from environment, with default."""
    _load_dotenv()
    import os
    return os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"


class Phase3Config:
    """Configuration for Phase 3 chatbot (Groq)."""

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        groq_model: Optional[str] = None,
        retrieval_top_k: int = 8,
    ) -> None:
        self.groq_api_key = groq_api_key or get_groq_api_key()
        self.groq_model = groq_model or get_groq_model()
        self.retrieval_top_k = retrieval_top_k
