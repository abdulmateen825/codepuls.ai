import logging
from typing import Any

from app.schemas.internal_analysis import AnalyzeRequest
from app.services.analysis.analysis_runner import run_static_analysis
from app.services.analysis.health_score import calculate_health_scores, spring_score_summary
from app.services.analysis.spring_callback_client import SpringCallbackError, send_scan_results
from app.services.github.file_discovery import build_file_tree
from app.services.github.repo_cleaner import remove_ignored_paths
from app.services.github.repo_cloner import clone_public_repository
from app.services.parser.file_parser import parse_repository
from app.services.rag.retriever import index_repository_chunks

logger = logging.getLogger(__name__)


def prepare_repository_for_scan(request: AnalyzeRequest) -> dict:
    repository_path = clone_public_repository(
        scan_id=request.scan_id,
        github_url=request.github_url,
        branch=request.branch,
    )
    remove_ignored_paths(repository_path)
    return {
        "fileTree": build_file_tree(repository_path),
        "parsedFiles": parse_repository(repository_path),
        "analysis": run_static_analysis(repository_path),
        "ragIndex": _index_rag_chunks(repository_path, request),
    }


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
    return {
        **_base_metadata(request),
        "fileTree": repository_metadata["fileTree"],
        "parsedFiles": repository_metadata["parsedFiles"],
        "analysisTools": analysis.get("tools", []),
        "totalFindings": analysis.get("totalFindings", 0),
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
