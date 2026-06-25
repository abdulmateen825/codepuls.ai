from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.internal import router as internal_router
from app.core.config import validate_startup_settings

app = FastAPI(title="CodePulse AI Engine")

app.include_router(health_router)
app.include_router(internal_router)


@app.on_event("startup")
def validate_configuration() -> None:
    validate_startup_settings()
