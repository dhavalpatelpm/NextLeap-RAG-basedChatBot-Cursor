#!/usr/bin/env python3
"""
Run Phase 2: build RAG pipeline (load course_details → chunk → embed → Chroma).
Usage:
  python scripts/run_phase2.py
  python scripts/run_phase2.py --top-k 10  # override retrieval k (for config only; index is built once)
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.phase2.build import run_phase2
from src.phase2.config import RAGConfig


def main():
    import argparse
    p = argparse.ArgumentParser(description="Phase 2: Build RAG index (chunk + embed + vector store)")
    p.add_argument("--top-k", type=int, default=None, help="Retrieval top_k (stored in config; index build unchanged)")
    args = p.parse_args()
    config = None
    if args.top_k is not None:
        config = RAGConfig.from_repo_root(repo_root, top_k=args.top_k)
    path = run_phase2(config=config)
    print("Phase 2 complete. Vector store at:", path)


if __name__ == "__main__":
    main()
