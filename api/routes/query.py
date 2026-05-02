from fastapi import APIRouter, Depends
from api.models.schemas import QueryRequest, QueryResponse, SimilarRequest, SimilarResult
from api.services.retriever import search
from api.services.llm import generate
from api.auth import verify_api_key

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
async def rag_query(req: QueryRequest):
    hits = await search(req.question, top_k=req.top_k)
    if not hits:
        return QueryResponse(answer="No relevant context found in the knowledge base.", sources=[], confidence=0.0)

    context_chunks = [h["text"] for h in hits]
    sources = sorted({h["source"] for h in hits})
    avg_score = sum(h["score"] for h in hits) / len(hits)

    answer = await generate(req.question, context_chunks)
    return QueryResponse(answer=answer, sources=sources, confidence=round(avg_score, 4))


@router.get("/similar", response_model=list[SimilarResult], dependencies=[Depends(verify_api_key)])
async def similar(text: str, top_k: int = 5):
    hits = await search(text, top_k=top_k)
    return [SimilarResult(text=h["text"], source=h["source"], score=round(h["score"], 4)) for h in hits]
