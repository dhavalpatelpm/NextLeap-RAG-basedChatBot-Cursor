"""
Phase 4 Backend: FastAPI app with POST /chat, GET /health, GET /api/status.
Serves frontend static files and delegates chat to Phase 3.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NextLeap Chat API",
    description="RAG-based chatbot for NextLeap courses",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Optional session id for conversation")


class SourceItem(BaseModel):
    cohort_id: str
    course_name: str
    text_snippet: str
    source_url: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = []
    out_of_scope: bool = False
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the NextLeap chatbot. Returns answer and optional sources.
    """
    try:
        from src.phase3 import chat as chat_service
        result: dict[str, Any] = chat_service(request.message)
        sources = [
            SourceItem(
                cohort_id=s.get("cohort_id", ""),
                course_name=s.get("course_name", ""),
                text_snippet=s.get("text_snippet", ""),
                source_url=s.get("source_url", ""),
            )
            for s in result.get("sources", [])
        ]
        return ChatResponse(
            answer=result.get("answer", ""),
            sources=sources,
            out_of_scope=result.get("out_of_scope", False),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ModuleNotFoundError as e:
        missing = str(e).replace("No module named ", "").strip("'\"")
        return ChatResponse(
            answer="",
            sources=[],
            out_of_scope=False,
            error=f"Missing dependency: {missing}. Run 'pip install -r requirements.txt' and restart the server.",
        )
    except Exception as e:
        err_msg = str(e)
        if "numpy" in err_msg.lower() or "NumPy" in err_msg:
            err_msg = (
                "NumPy compatibility issue. Run: pip install \"numpy<2\" -r requirements.txt "
                "then restart the server. Then try your question again."
            )
        return ChatResponse(
            answer="",
            sources=[],
            out_of_scope=False,
            error=f"Service error: {err_msg}",
        )


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok", "service": "nextleap-chat"}


@app.get("/api/status")
def status() -> dict[str, Any]:
    """Status and last data refresh (Phase 5)."""
    last_refresh = None
    try:
        from src.phase5.refresh import get_last_refresh_iso
        last_refresh = get_last_refresh_iso()
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "nextleap-chat",
        "phase": 4,
        "data_last_refreshed_at": last_refresh,
    }


# ---------------------------------------------------------------------------
# Serve frontend (single-page app)
# ---------------------------------------------------------------------------

_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "public"


@app.get("/")
def index() -> FileResponse:
    """Serve the chat UI."""
    index_path = _FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found. Ensure frontend/public/index.html exists.")


@app.get("/{path:path}")
def serve_static(path: str) -> FileResponse:
    """Serve static assets (JS, CSS, etc.)."""
    full = _FRONTEND_DIR / path
    if full.is_file() and full.exists():
        return FileResponse(full)
    # SPA fallback: return index.html for unknown paths so client-side routing works
    index_path = _FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not found")
