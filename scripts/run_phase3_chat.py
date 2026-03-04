#!/usr/bin/env python3
"""
Test Phase 3 chat from the command line. Requires Phase 2 index (run scripts/run_phase2.py first)
and .env with GROQ_API_KEY.
Usage:
  python scripts/run_phase3_chat.py "What is the fee for Product Manager Fellowship?"
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from src.phase3 import chat as chat_service


def main() -> None:
    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What courses does NextLeap offer?"
    print("Query:", message)
    print("-" * 60)
    result = chat_service.chat(message)
    print("Answer:", result["answer"])
    if result.get("sources"):
        print("\nSources:")
        for s in result["sources"]:
            print(f"  - {s.get('course_name', '')} | {s.get('source_url', '')}")


if __name__ == "__main__":
    main()
