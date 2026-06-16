from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.internal import router as internal_router

app = FastAPI(title="CodePulse AI Engine")

app.include_router(health_router)
app.include_router(internal_router)
