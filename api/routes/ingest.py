import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from api.models.schemas import AlertPayload, IngestAlertResponse, IngestFileResponse
from api.services.retriever import store_chunks
from ingestor.pipeline import ingest_bytes, ingest_alert_payload
from api.auth import verify_api_key

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/file", response_model=IngestFileResponse, dependencies=[Depends(verify_api_key)])
async def ingest_file(file: UploadFile = File(...)):
    allowed = {".md", ".txt", ".json", ".log"}
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    content = await file.read()
    chunks = await ingest_bytes(content, filename=file.filename)
    if not chunks:
        raise HTTPException(status_code=422, detail="No content could be extracted from file")

    stored = await store_chunks(chunks, source=file.filename)
    return IngestFileResponse(status="ok", chunks_stored=stored, source=file.filename)


@router.post("/alert", response_model=IngestAlertResponse, dependencies=[Depends(verify_api_key)])
async def ingest_alert(payload: AlertPayload):
    chunks = await ingest_alert_payload(payload.model_dump())
    if not chunks:
        return IngestAlertResponse(status="ok", chunks_stored=0, alert_count=len(payload.alerts))

    source = f"alert::{payload.groupKey or 'unknown'}"
    stored = await store_chunks(chunks, source=source)
    return IngestAlertResponse(status="ok", chunks_stored=stored, alert_count=len(payload.alerts))
