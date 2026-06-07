from datetime import UTC, datetime

from app.schemas.health import HealthResponse


def get_health() -> HealthResponse:
    return HealthResponse(
        service="backend-ai",
        status="UP",
        checked_at=datetime.now(UTC),
        message="FastAPI AI engine is healthy",
    )
