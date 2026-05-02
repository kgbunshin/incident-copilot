import httpx
import os
from fastapi import APIRouter
from api.models.schemas import HealthResponse, StatsResponse
from api.services.retriever import get_stats

router = APIRouter()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
CHROMA_HOST = os.getenv("CHROMA_HOST", "http://localhost:8000")


@router.get("/health", response_model=HealthResponse)
async def health():
    ollama_status = "ok"
    chroma_status = "ok"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{OLLAMA_HOST}/api/tags")
    except Exception:
        ollama_status = "unreachable"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{CHROMA_HOST}/api/v1/heartbeat")
    except Exception:
        chroma_status = "unreachable"

    overall = "ok" if ollama_status == "ok" and chroma_status == "ok" else "degraded"
    return HealthResponse(status=overall, ollama=ollama_status, chromadb=chroma_status)


@router.get("/stats", response_model=StatsResponse)
async def stats():
    data = await get_stats()
    return StatsResponse(**data)
