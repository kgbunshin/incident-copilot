import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routes import health, ingest, query

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SRE RAG API starting up")
    yield
    logger.info("SRE RAG API shutting down")


app = FastAPI(
    title="SRE RAG API",
    description="Retrieval-Augmented Generation for SRE incident knowledge",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(query.router)
