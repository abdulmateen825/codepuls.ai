from uuid import UUID

from app.schemas.ai_interactions import ChatMessage
from app.services.llm.llm_service import LlmService, LlmServiceError
from app.services.rag.retriever import semantic_search


def answer_repository_question(
    repository_id: UUID,
    question: str,
    history: list[ChatMessage],
) -> dict:
    references = _retrieve_references(repository_id, question)
    context = _format_context(references)
    history_text = "\n".join(f"{message.role}: {message.content}" for message in history[-6:])
    prompt = (
        f"Question:\n{question}\n\n"
        f"Recent conversation:\n{history_text or 'No prior messages.'}\n\n"
        f"Repository context:\n{context or 'No indexed context was available.'}"
    )

    try:
        answer = LlmService().complete(
            "You are CodePulse AI. Answer repository questions using only the provided code context. "
            "When useful, mention file references.",
            prompt,
        )
    except LlmServiceError:
        answer = _fallback_answer(question, references)

    return {
        "answer": answer,
        "fileReferences": _file_references(references),
        "suggestedQuestions": _suggested_questions(references),
    }


def _retrieve_references(repository_id: UUID, question: str) -> list[dict]:
    try:
        return semantic_search(repository_id, question, limit=5)["results"]
    except Exception:
        return []


def _format_context(references: list[dict]) -> str:
    parts = []
    for reference in references:
        parts.append(
            f"{reference.get('filePath')}:{reference.get('startLine')}-{reference.get('endLine')}\n"
            f"{reference.get('content', '')[:3000]}"
        )
    return "\n\n---\n\n".join(parts)


def _file_references(references: list[dict]) -> list[dict]:
    return [
        {
            "filePath": reference.get("filePath", ""),
            "startLine": int(reference.get("startLine") or 1),
            "endLine": int(reference.get("endLine") or reference.get("startLine") or 1),
            "symbolName": reference.get("symbolName"),
            "score": reference.get("score"),
        }
        for reference in references
    ]


def _suggested_questions(references: list[dict]) -> list[str]:
    if references:
        first_path = references[0].get("filePath", "this file")
        return [
            f"What responsibilities does {first_path} have?",
            "Where are the highest-risk changes needed?",
            "How does this code path connect to the rest of the repository?",
        ]

    return [
        "What are the most important files in this repository?",
        "What should I scan or review first?",
        "How can I improve the repository health score?",
    ]


def _fallback_answer(question: str, references: list[dict]) -> str:
    if not references:
        return (
            f"### Answer\n\nI could not find indexed code context for: **{question}**.\n\n"
            "Run a completed scan first so CodePulse can index source chunks for repository-aware answers."
        )

    files = ", ".join(reference.get("filePath", "") for reference in references[:3])
    return (
        f"### Answer\n\nI found relevant context in {files}.\n\n"
        "Review the referenced chunks first; they are the strongest matches for your question. "
        "The configured LLM provider is unavailable, so this response is intentionally conservative."
    )
