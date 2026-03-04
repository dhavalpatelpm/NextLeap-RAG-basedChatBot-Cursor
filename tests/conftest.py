"""
Pytest fixtures for integration tests. Phase 3 tests require GROQ_API_KEY and Phase 2 vector store.
"""
import sys
from pathlib import Path

import pytest

# Ensure repo root is on path so "src" is importable
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


# Add repo root to path once at collection time
_root = repo_root()
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root for path-based config."""
    return repo_root()


def _has_groq_key() -> bool:
    try:
        from dotenv import load_dotenv
        load_dotenv(repo_root() / ".env")
    except ImportError:
        pass
    import os
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def _has_vector_store() -> bool:
    root = repo_root()
    vs = root / "data" / "vector_store"
    if not vs.exists():
        return False
    # Chroma creates chroma.sqlite3 or similar
    return any(vs.iterdir())


@pytest.fixture(scope="session")
def skip_if_no_integration(request):
    """Skip integration tests if GROQ_API_KEY is missing or vector store not built."""
    if not _has_groq_key():
        pytest.skip("GROQ_API_KEY not set (set in .env for integration tests)")
    if not _has_vector_store():
        pytest.skip(
            "Phase 2 vector store not found. Run: python scripts/run_phase2.py"
        )
