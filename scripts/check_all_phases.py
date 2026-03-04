#!/usr/bin/env python3
"""
Quick sanity check that Phase 1–3 and tests are runnable.
Run from repo root after: pip install -r requirements.txt
Optional: .env with GROQ_API_KEY, and python scripts/run_phase2.py for full flow.
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

def main():
    errors = []
    # Phase 1
    try:
        from src.phase1.course_details_loader import get_all_course_keys, get_course_data_with_source
        keys = get_all_course_keys()
        assert len(keys) >= 1, "No course keys"
        data, url = get_course_data_with_source(keys[0])
        assert data and url, "No course data or source_url"
        print("Phase 1: OK (course_details loader)")
    except Exception as e:
        errors.append(f"Phase 1: {e}")
        print("Phase 1: FAIL", e)

    # Phase 2
    try:
        from src.phase2 import retrieve, RAGConfig
        cfg = RAGConfig()
        chunks = retrieve("What is the price of product management fellowship?", top_k=2, config=cfg)
        if chunks:
            print("Phase 2: OK (retrieval returned", len(chunks), "chunks)")
        else:
            print("Phase 2: OK (retrieval runs; index empty? Run: python scripts/run_phase2.py)")
    except Exception as e:
        errors.append(f"Phase 2: {e}")
        print("Phase 2: FAIL", e)

    # Phase 3
    try:
        from src.phase3.config import get_groq_api_key, get_groq_model
        get_groq_api_key()
        get_groq_model()
        print("Phase 3 config: OK (GROQ_API_KEY and model)")
    except ValueError as e:
        print("Phase 3 config: SKIP (set GROQ_API_KEY in .env for chat)")
    except Exception as e:
        errors.append(f"Phase 3 config: {e}")
        print("Phase 3 config: FAIL", e)

    try:
        from src.phase3 import chat
        r = chat.chat("What is the price of product management fellowship?")
        assert "answer" in r and "sources" in r and "out_of_scope" in r
        print("Phase 3 chat: OK (answer length:", len(r.get("answer", "")), ")")
        if r.get("sources"):
            print("  sources:", [s.get("source_url", "")[:50] for s in r["sources"][:2]])
    except ValueError:
        print("Phase 3 chat: SKIP (no GROQ_API_KEY)")
    except Exception as e:
        errors.append(f"Phase 3 chat: {e}")
        print("Phase 3 chat: FAIL", e)

    # Tests
    try:
        import pytest
        print("pytest: OK")
    except ImportError:
        print("pytest: not installed (pip install pytest)")

    if errors:
        print("\nErrors:", errors)
        sys.exit(1)
    print("\nAll phases OK.")

if __name__ == "__main__":
    main()
