from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str
    checked_at: datetime
    message: str
