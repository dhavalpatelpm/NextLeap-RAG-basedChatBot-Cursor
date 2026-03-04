#!/usr/bin/env python3
"""
Run Phase 4: Backend API + frontend chat UI.
Serves the app at http://127.0.0.1:8000 (open in browser).
Requires: Phase 2 vector store, .env with GROQ_API_KEY.
"""
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

try:
    import uvicorn
except ImportError:
    print("Error: uvicorn not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from src.phase4.api import app
except ImportError as e:
    print("Error: could not load app.", e)
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
