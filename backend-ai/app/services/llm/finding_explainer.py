import json
from pathlib import Path

from app.schemas.ai_interactions import FindingExplainRequest
from app.services.github.repo_cloner import scan_workspace
from app.services.llm.llm_service import LlmService, LlmServiceError
from app.services.rag.retriever import semantic_search


def explain_finding(request: FindingExplainRequest) -> dict:
    context = _nearby_code_context(request)
    prompt = (
        "Explain this static-analysis finding as JSON with keys summary, whyItMatters, risk, "
        "correctiveAction, possibleFixedCode, confidenceScore.\n\n"
        f"Finding: {request.title}\n"
        f"Severity: {request.severity}\n"
        f"Category: {request.category}\n"
        f"Rule: {request.rule_id}\n"
        f"Description: {request.description}\n"
        f"Recommendation: {request.recommendation or 'None provided'}\n"
        f"Location: {request.file_path}:{request.line_number or 1}\n\n"
        f"Nearby code:\n{context['content'] or 'No nearby code context was available.'}"
    )

    try:
        raw_answer = LlmService().complete(
            "You are CodePulse AI. Return concise valid JSON only.",
            prompt,
        )
        explanation = _parse_json_answer(raw_answer)
    except (LlmServiceError, ValueError, KeyError, json.JSONDecodeError):
        explanation = _fallback_explanation(request, context["content"])

    return {
        **explanation,
        "fileReferences": context["fileReferences"],
    }


def _nearby_code_context(request: FindingExplainRequest) -> dict:
    workspace = scan_workspace(request.scan_id)
    file_path = (workspace / request.file_path).resolve()
    content = ""
    start_line = max(1, (request.line_number or 1) - 8)
    end_line = start_line

    try:
        file_path.relative_to(workspace.resolve())
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        end_line = min(len(lines), (request.line_number or 1) + 8)
        content = "\n".join(
            f"{line_number}: {line}"
            for line_number, line in enumerate(lines[start_line - 1:end_line], start=start_line)
        )
    except (OSError, ValueError):
        rag_context = _rag_context(request)
        if rag_context:
            return rag_context

    return {
        "content": content,
        "fileReferences": [
            {
                "filePath": request.file_path,
                "startLine": start_line,
                "endLine": max(start_line, end_line),
                "symbolName": None,
                "score": None,
            }
        ],
    }


def _rag_context(request: FindingExplainRequest) -> dict | None:
    try:
        results = semantic_search(request.repository_id, f"{request.title} {request.description}", limit=3)["results"]
    except Exception:
        return None

    if not results:
        return None

    return {
        "content": "\n\n---\n\n".join(result.get("content", "")[:2000] for result in results),
        "fileReferences": [
            {
                "filePath": result.get("filePath", ""),
                "startLine": int(result.get("startLine") or 1),
                "endLine": int(result.get("endLine") or result.get("startLine") or 1),
                "symbolName": result.get("symbolName"),
                "score": result.get("score"),
            }
            for result in results
        ],
    }


def _parse_json_answer(answer: str) -> dict:
    cleaned = answer.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()

    data = json.loads(cleaned)
    return {
        "summary": str(data["summary"]),
        "whyItMatters": str(data["whyItMatters"]),
        "risk": str(data["risk"]),
        "correctiveAction": str(data["correctiveAction"]),
        "possibleFixedCode": str(data["possibleFixedCode"]),
        "confidenceScore": float(data["confidenceScore"]),
    }


def _fallback_explanation(request: FindingExplainRequest, context: str) -> dict:
    fixed_code = request.recommendation or "Apply the scanner recommendation and rerun the scan."
    if context:
        fixed_code = f"// Review {request.file_path}:{request.line_number or 1}\n{fixed_code}"

    return {
        "summary": f"{request.title} was reported in {request.file_path}.",
        "whyItMatters": request.description,
        "risk": f"{request.severity} severity {request.category} issue that may affect repository health.",
        "correctiveAction": request.recommendation or "Review the affected code and apply the tool-specific remediation.",
        "possibleFixedCode": fixed_code,
        "confidenceScore": 0.72,
    }
