"""
Phase 3 — Chatbot Service: retrieval + Groq LLM, context-only answers, out-of-scope handling.
"""
from .chat import chat
from .config import Phase3Config

__all__ = ["chat", "Phase3Config"]
