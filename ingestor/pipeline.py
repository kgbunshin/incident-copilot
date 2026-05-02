from ingestor.parsers import markdown, json_logs, alertmanager
from ingestor.chunker import chunk_text


async def ingest_bytes(content: bytes, filename: str) -> list[str]:
    text = content.decode("utf-8", errors="replace")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("md", "txt"):
        sections = markdown.parse(text)
    elif ext in ("json", "log"):
        sections = json_logs.parse(text)
    else:
        sections = [text]

    chunks = []
    for section in sections:
        chunks.extend(chunk_text(section))
    return chunks


async def ingest_alert_payload(payload: dict) -> list[str]:
    raw_chunks = alertmanager.parse(payload)
    chunks = []
    for chunk in raw_chunks:
        chunks.extend(chunk_text(chunk))
    return chunks
