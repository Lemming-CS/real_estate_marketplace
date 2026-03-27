from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | list


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
