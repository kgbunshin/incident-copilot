from __future__ import annotations

import chromadb
import os
from api.services.embedder import embed_query, embed_texts


CHROMA_HOST = os.getenv("CHROMA_HOST", "http://localhost:8000")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "sre_knowledge")

_client = None


async def get_client():
    global _client
    if _client is None:
        host, port = _parse_host(CHROMA_HOST)
        _client = await chromadb.AsyncHttpClient(host=host, port=port)
    return _client


def _parse_host(url: str) -> tuple[str, int]:
    url = url.replace("http://", "").replace("https://", "")
    if ":" in url:
        h, p = url.rsplit(":", 1)
        return h, int(p)
    return url, 8000


def _distance_to_score(distance: float) -> float:
    """Convert Chroma distance values into a bounded confidence-like score."""
    if distance < 0:
        return 0.0
    return 1 / (1 + distance)


async def get_collection():
    client = await get_client()
    return await client.get_or_create_collection(name=COLLECTION_NAME)


async def store_chunks(chunks: list[str], source: str) -> int:
    collection = await get_collection()
    embeddings = await embed_texts(chunks)
    ids = [f"{source}::{i}" for i in range(len(chunks))]
    metadatas = [{"source": source} for _ in chunks]
    await collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)


async def search(text: str, top_k: int = 5) -> list[dict]:
    collection = await get_collection()
    embedding = await embed_query(text)
    results = await collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "score": _distance_to_score(dist),
        })
    return hits


async def get_stats() -> dict:
    collection = await get_collection()
    count = await collection.count()
    all_items = await collection.get(include=["metadatas"])
    sources = sorted({m.get("source", "unknown") for m in all_items["metadatas"]})
    return {"collection": COLLECTION_NAME, "total_chunks": count, "sources": sources}
