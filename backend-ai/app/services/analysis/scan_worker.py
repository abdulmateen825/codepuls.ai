import logging
from typing import Any

from app.schemas.internal_analysis import AnalyzeRequest
from app.services.analysis.analysis_runner import run_static_analysis
from app.services.analysis.health_score import calculate_health_scores, spring_score_summary
from app.services.analysis.spring_callback_client import SpringCallbackError, send_scan_results
from app.services.github.file_discovery import build_file_tree
from app.services.github.repo_cleaner import cleanup_repository, remove_ignored_paths
from app.services.github.repo_cloner import clone_public_repository
from app.services.parser.file_parser import parse_repository
from app.services.code_smells.runner import run_code_smell_detection
from app.services.rag.retriever import index_repository_chunks

logger = logging.getLogger(__name__)


def prepare_repository_for_scan(request: AnalyzeRequest) -> dict:
    repository_path = clone_public_repository(
        scan_id=request.scan_id,
        github_url=request.github_url,
        branch=request.branch,
    )
    try:
        remove_ignored_paths(repository_path)
        parsed_files = parse_repository(repository_path)
        static_analysis = run_static_analysis(repository_path)
        code_smells = run_code_smell_detection(repository_path, parsed_files)
        return {
            "fileTree": build_file_tree(repository_path),
            "parsedFiles": parsed_files,
            "analysis": _merge_analysis(static_analysis, code_smells),
            "codeSmells": code_smells,
            "ragIndex": _index_rag_chunks(repository_path, request),
        }
    finally:
        cleanup_repository(repository_path)


def process_scan(request: AnalyzeRequest) -> None:
    _send_callback(
        request,
        {
            "status": "RUNNING",
            "metadata": _base_metadata(request),
            "findings": [],
            "scores": None,
            "errorMessage": None,
        },
    )

    try:
        repository_metadata = prepare_repository_for_scan(request)
        analysis = repository_metadata["analysis"]
        findings = analysis.get("findings", [])
        health_scores = calculate_health_scores(findings)
        _send_callback(
            request,
            {
                "status": "COMPLETED",
                "metadata": _completed_metadata(request, repository_metadata, health_scores),
                "findings": findings,
                "scores": spring_score_summary(health_scores),
                "errorMessage": None,
            },
        )
    except Exception as exception:
        logger.exception("Scan processing failed for scan %s.", request.scan_id)
        _send_callback(
            request,
            {
                "status": "FAILED",
                "metadata": _base_metadata(request),
                "findings": [],
                "scores": None,
                "errorMessage": str(exception)[:1000] or "Scan failed.",
            },
        )


def _send_callback(request: AnalyzeRequest, payload: dict[str, Any]) -> None:
    try:
        send_scan_results(request.scan_id, payload)
    except SpringCallbackError:
        logger.exception("Failed to send scan callback for scan %s.", request.scan_id)


def _base_metadata(request: AnalyzeRequest) -> dict:
    return {
        "repositoryId": str(request.repository_id),
        "githubUrl": request.github_url,
        "branch": request.branch,
    }


def _completed_metadata(request: AnalyzeRequest, repository_metadata: dict, health_scores: dict) -> dict:
    analysis = repository_metadata["analysis"]
    code_smells = repository_metadata.get("codeSmells", {})
    return {
        **_base_metadata(request),
        "fileTree": repository_metadata["fileTree"],
        "parsedFiles": repository_metadata["parsedFiles"],
        "analysisTools": analysis.get("tools", []),
        "totalFindings": analysis.get("totalFindings", 0),
        "codeSmells": {
            "totalSmells": code_smells.get("summary", {}).get("totalSmells", 0),
            "bySmellType": code_smells.get("summary", {}).get("bySmellType", {}),
            "bySeverity": code_smells.get("summary", {}).get("bySeverity", {}),
            "byLanguage": code_smells.get("summary", {}).get("byLanguage", {}),
            "detectors": code_smells.get("detectors", []),
            "warnings": code_smells.get("warnings", []),
        },
        "healthScores": health_scores,
        "ragIndex": repository_metadata.get("ragIndex", {}),
    }


def _index_rag_chunks(repository_path, request: AnalyzeRequest) -> dict:
    try:
        return {
            "status": "completed",
            **index_repository_chunks(repository_path, request.repository_id, request.scan_id),
        }
    except Exception as exception:
        logger.exception("RAG indexing failed for scan %s.", request.scan_id)
        return {
            "status": "failed",
            "error": str(exception)[:500] or "RAG indexing failed.",
        }


def _merge_analysis(static_analysis: dict, code_smells: dict) -> dict:
    findings = _deduplicate_findings([
        *static_analysis.get("findings", []),
        *code_smells.get("findings", []),
    ])
    findings.sort(key=lambda item: (
        str(item.get("filePath", "")),
        int(item.get("lineNumber") or item.get("startLine") or 1),
        str(item.get("toolName", "")),
        str(item.get("title", "")),
    ))

    return {
        "totalFindings": len(findings),
        "findings": findings,
        "tools": [
            *static_analysis.get("tools", []),
            {
                "toolName": "code-smell",
                "status": "completed",
                "findingCount": code_smells.get("totalFindings", 0),
                "detectors": code_smells.get("detectors", []),
                "warnings": code_smells.get("warnings", []),
            },
        ],
    }


def _deduplicate_findings(findings: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str, int, int, str]] = set()
    unique: list[dict] = []
    for finding in findings:
        start_line = int(finding.get("startLine") or finding.get("lineNumber") or 1)
        end_line = int(finding.get("endLine") or finding.get("lineNumber") or start_line)
        key = (
            str(finding.get("category", "")),
            str(finding.get("ruleId") or finding.get("toolName", "")),
            str(finding.get("filePath", "")),
            start_line,
            end_line,
            str(finding.get("title", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique
