from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.system.health_service import get_health

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return get_health()
