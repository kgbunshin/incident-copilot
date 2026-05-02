import httpx
import os


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct-q4_K_M")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

SYSTEM_PROMPT = """You are an SRE assistant. Answer questions about incidents, alerts,
and infrastructure based solely on the context provided. Be concise and actionable.
If the context is insufficient, say so — never hallucinate."""


async def generate(question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    prompt = f"""[CONTEXT]
{context}

[QUESTION]
{question}

[ANSWER]"""

    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        resp = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": LLM_MODEL,
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
            },
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()


async def warm_up() -> None:
    """Load the LLM into Ollama before the first user query hits MCP timeouts."""
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        resp = await client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": "ready",
                "stream": False,
                "options": {"num_predict": 1},
            },
        )
        resp.raise_for_status()
