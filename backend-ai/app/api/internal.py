import os
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status

from app.schemas.internal_analysis import AnalyzeAcceptedResponse, AnalyzeRequest
from app.services.analysis.scan_worker import prepare_repository_for_scan, process_scan_placeholder

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
    repository_metadata = prepare_repository_for_scan(request)
    background_tasks.add_task(process_scan_placeholder, request, repository_metadata)

    return AnalyzeAcceptedResponse(
        accepted=True,
        scan_id=request.scan_id,
        status="accepted",
        file_tree=repository_metadata["fileTree"],
        parsed_files=repository_metadata["parsedFiles"],
        analysis=repository_metadata["analysis"],
    )
