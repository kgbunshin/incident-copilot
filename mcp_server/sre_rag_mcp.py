#!/usr/bin/env python3
"""
SRE RAG MCP Server — expõe a base de conhecimento como tools para o Claude Code.

Tools disponíveis:
  sre_query   — consulta RAG com linguagem natural
  sre_ingest  — ingere texto/runbook/decisão na base vetorial
  sre_stats   — mostra o que está armazenado
"""
import asyncio
import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

API_URL = os.getenv("SRE_API_URL", "http://localhost:8080")
API_KEY = os.getenv("SRE_API_KEY", "")

server = Server("sre-rag")


def _headers() -> dict:
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}


async def _check_connectivity() -> str | None:
    """Returns error message if API is unreachable, else None."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{API_URL}/health")
            resp.raise_for_status()
            return None
    except Exception as e:
        return f"SRE RAG API offline ({API_URL}): {e}"


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="sre_query",
            description=(
                "Consulta a base de conhecimento SRE com linguagem natural. "
                "Retorna resposta gerada pelo LLM com fontes e nível de confiança. "
                "Use para: diagnosticar incidentes, buscar runbooks, encontrar "
                "incidentes similares, ou recuperar decisões técnicas passadas."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Pergunta em linguagem natural sobre incidentes, alertas ou infraestrutura.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Número de chunks de contexto a recuperar (padrão: 5).",
                        "default": 5,
                    },
                },
                "required": ["question"],
            },
        ),
        types.Tool(
            name="sre_ingest",
            description=(
                "Ingere texto na base de conhecimento SRE. "
                "Use para adicionar: runbooks, post-mortems, decisões técnicas, "
                "notas de incidentes, configurações importantes ou qualquer "
                "conhecimento operacional que deva ser consultável no futuro."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Conteúdo a ser ingerido (markdown, texto livre, JSON).",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Nome de referência para o documento (ex: 'runbook-oom.md', 'decisao-embeddings.md').",
                    },
                },
                "required": ["content", "filename"],
            },
        ),
        types.Tool(
            name="sre_stats",
            description=(
                "Retorna estatísticas da base de conhecimento SRE: "
                "total de chunks armazenados e lista de fontes indexadas."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    err = await _check_connectivity()
    if err:
        return [types.TextContent(type="text", text=f"⚠️ {err}")]

    async with httpx.AsyncClient(timeout=120.0) as client:
        if name == "sre_query":
            question = arguments["question"]
            top_k = arguments.get("top_k", 5)
            resp = await client.post(
                f"{API_URL}/query",
                headers=_headers(),
                json={"question": question, "top_k": top_k},
            )
            resp.raise_for_status()
            data = resp.json()
            text = (
                f"**Resposta:** {data['answer']}\n\n"
                f"**Fontes:** {', '.join(data['sources']) or 'nenhuma'}\n"
                f"**Confiança:** {data['confidence']:.0%}"
            )
            return [types.TextContent(type="text", text=text)]

        elif name == "sre_ingest":
            content = arguments["content"]
            filename = arguments["filename"]
            import io
            files = {"file": (filename, content.encode(), "text/plain")}
            # multipart — sem Content-Type no header
            resp = await client.post(
                f"{API_URL}/ingest/file",
                headers={"X-API-Key": API_KEY},
                files=files,
            )
            resp.raise_for_status()
            data = resp.json()
            text = (
                f"✅ Ingerido: **{data['source']}** — "
                f"{data['chunks_stored']} chunks armazenados."
            )
            return [types.TextContent(type="text", text=text)]

        elif name == "sre_stats":
            resp = await client.get(f"{API_URL}/stats", headers=_headers())
            resp.raise_for_status()
            data = resp.json()
            sources_list = "\n".join(f"  - {s}" for s in data["sources"]) or "  (vazio)"
            text = (
                f"**Coleção:** {data['collection']}\n"
                f"**Total de chunks:** {data['total_chunks']}\n"
                f"**Fontes indexadas:**\n{sources_list}"
            )
            return [types.TextContent(type="text", text=text)]

        else:
            return [types.TextContent(type="text", text=f"Tool desconhecida: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
