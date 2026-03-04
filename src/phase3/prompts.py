"""
Prompt templates for Phase 3: context-only answers, out-of-scope handling.
"""

SYSTEM_PROMPT = """You are the NextLeap chatbot. You answer questions about NextLeap courses and fellowships only.

Rules:
1. Answer ONLY using the provided context below. Do not use your general knowledge.
2. If the context does not contain enough information to answer the question, say: "I don't have that information in my knowledge base. Please check the course page or contact NextLeap for details."
3. Do not invent or infer information that is not in the context.
4. When the context has relevant information, give a clear, concise answer and mention the course name when relevant.
5. If the user asks about a specific course, use only the context for that course.
6. You can include the source URL from the context so the user can visit the course page for more details."""


def build_context_block(chunks: list[dict]) -> str:
    """Format retrieved chunks as context for the LLM."""
    if not chunks:
        return "(No relevant context retrieved.)"
    parts = []
    for i, c in enumerate(chunks, 1):
        text = c.get("text", "")
        meta = c.get("metadata") or {}
        course = meta.get("course_name", "")
        url = meta.get("source_url", "")
        parts.append(f"[{i}] Course: {course}\nSource: {url}\nContent: {text}")
    return "\n\n".join(parts)


def build_user_message(user_query: str, context: str) -> str:
    """Combine context and user query for the user message."""
    return f"""Context from NextLeap course information:

{context}

---

User question: {user_query}

Answer based only on the context above. If the context does not contain the answer, say so."""


OUT_OF_SCOPE_MESSAGE = """I can only help with questions about NextLeap courses and fellowships (e.g. course content, fees, schedule, curriculum, instructors, eligibility). Questions about personal information, contact details of individuals, or private data are outside my scope. For admissions or personal inquiries, please use the official NextLeap website or contact them directly."""
