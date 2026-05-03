import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api.routes import health, ingest, query
from api.services.llm import warm_up

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
OLLAMA_PREWARM = os.getenv("OLLAMA_PREWARM", "true").lower() == "true"
TRUSTED_IPS = set(os.getenv("TRUSTED_IPS", "127.0.0.1,172.18.0.1").split(","))
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SRE RAG API starting up")
    if OLLAMA_PREWARM:
        try:
            logger.info("Pre-warming Ollama LLM")
            await warm_up()
            logger.info("Ollama LLM pre-warm complete")
        except Exception as exc:
            logger.warning("Ollama LLM pre-warm failed: %s", exc)
    yield
    logger.info("SRE RAG API shutting down")


app = FastAPI(
    title="SRE RAG API",
    description="Retrieval-Augmented Generation for SRE incident knowledge",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def ip_allowlist(request: Request, call_next):
    client_ip = request.client.host
    if TRUSTED_IPS and client_ip not in TRUSTED_IPS:
        logger.warning("Blocked request from untrusted IP: %s %s", client_ip, request.url.path)
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)


app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
