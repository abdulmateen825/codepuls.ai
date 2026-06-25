import os
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Response, status

from app.schemas.ai_interactions import (
    FindingExplainRequest,
    FindingExplanationResponse,
    RepositoryChatRequest,
    RepositoryChatResponse,
)
from app.schemas.internal_analysis import AnalyzeAcceptedResponse, AnalyzeRequest
from app.schemas.report_generation import GenerateReportRequest
from app.services.analysis.scan_worker import process_scan
from app.services.llm.finding_explainer import explain_finding
from app.services.llm.repository_chat import answer_repository_question
from app.services.reports.pdf_generator import generate_scan_report_pdf

router = APIRouter(prefix="/internal", tags=["internal"])


def verify_internal_api_key(authorization: str | None) -> None:
    expected_key = os.getenv("INTERNAL_API_KEY", "change-me-internal-api-key")
    expected_header = f"Bearer {expected_key}"

    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key.",
        )


@router.post("/analyze", response_model=AnalyzeAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    authorization: Annotated[str | None, Header()] = None,
) -> AnalyzeAcceptedResponse:
    verify_internal_api_key(authorization)
    background_tasks.add_task(process_scan, request)

    return AnalyzeAcceptedResponse(
        accepted=True,
        scan_id=request.scan_id,
        status="accepted",
        file_tree={},
        parsed_files={},
        analysis={},
    )


@router.post("/repositories/chat", response_model=RepositoryChatResponse)
def repository_chat(
    request: RepositoryChatRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> RepositoryChatResponse:
    verify_internal_api_key(authorization)
    response = answer_repository_question(request.repository_id, request.question, request.history)
    return RepositoryChatResponse(**response)


@router.post("/findings/explain", response_model=FindingExplanationResponse)
def finding_explanation(
    request: FindingExplainRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> FindingExplanationResponse:
    verify_internal_api_key(authorization)
    response = explain_finding(request)
    return FindingExplanationResponse(**response)


@router.post("/reports/pdf")
def generate_report_pdf(
    request: GenerateReportRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    verify_internal_api_key(authorization)
    pdf_bytes = generate_scan_report_pdf(request)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="codepulse-{request.scan_id}.pdf"'},
    )
