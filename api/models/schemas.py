from pydantic import BaseModel, Field
from typing import Optional


class IngestFileResponse(BaseModel):
    status: str
    chunks_stored: int
    source: str


class AlertPayload(BaseModel):
    version: str = "4"
    groupKey: Optional[str] = None
    status: str
    receiver: str
    groupLabels: dict = {}
    commonLabels: dict = {}
    commonAnnotations: dict = {}
    externalURL: str = ""
    alerts: list[dict] = []


class IngestAlertResponse(BaseModel):
    status: str
    chunks_stored: int
    alert_count: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float


class SimilarRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class SimilarResult(BaseModel):
    text: str
    source: str
    score: float


class HealthResponse(BaseModel):
    status: str
    ollama: str
    chromadb: str


class StatsResponse(BaseModel):
    collection: str
    total_chunks: int
    sources: list[str]
