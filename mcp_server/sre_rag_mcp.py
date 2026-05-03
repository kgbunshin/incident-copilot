#!/usr/bin/env python3
"""
SRE RAG MCP Server — exposes the knowledge base as tools for Claude Code.

Available tools:
  sre_query   — natural language RAG query
  sre_ingest  — ingest text/runbook/decision into the vector knowledge base
  sre_stats   — show what is stored in the knowledge base
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
                "Query the SRE knowledge base using natural language. "
                "Returns an LLM-generated answer with sources and confidence score. "
                "Use to: diagnose incidents, retrieve runbooks, find similar past incidents, "
                "or look up past technical decisions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about incidents, alerts, or infrastructure.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of context chunks to retrieve (default: 5).",
                        "default": 5,
                    },
                },
                "required": ["question"],
            },
        ),
        types.Tool(
            name="sre_ingest",
            description=(
                "Ingest text into the SRE knowledge base. "
                "Use to add: runbooks, post-mortems, technical decisions, "
                "incident notes, important configurations, or any operational "
                "knowledge that should be queryable in the future."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to ingest (markdown, plain text, JSON).",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Reference name for the document (e.g. 'runbook-oom.md', 'decision-embeddings.md').",
                    },
                },
                "required": ["content", "filename"],
            },
        ),
        types.Tool(
            name="sre_stats",
            description=(
                "Returns SRE knowledge base statistics: "
                "total stored chunks and list of indexed sources."
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
                f"**Answer:** {data['answer']}\n\n"
                f"**Sources:** {', '.join(data['sources']) or 'none'}\n"
                f"**Confidence:** {data['confidence']:.0%}"
            )
            return [types.TextContent(type="text", text=text)]

        elif name == "sre_ingest":
            content = arguments["content"]
            filename = arguments["filename"]
            import io
            files = {"file": (filename, content.encode(), "text/plain")}
            resp = await client.post(
                f"{API_URL}/ingest/file",
                headers={"X-API-Key": API_KEY},
                files=files,
            )
            resp.raise_for_status()
            data = resp.json()
            text = (
                f"✅ Ingested: **{data['source']}** — "
                f"{data['chunks_stored']} chunks stored."
            )
            return [types.TextContent(type="text", text=text)]

        elif name == "sre_stats":
            resp = await client.get(f"{API_URL}/stats", headers=_headers())
            resp.raise_for_status()
            data = resp.json()
            sources_list = "\n".join(f"  - {s}" for s in data["sources"]) or "  (empty)"
            text = (
                f"**Collection:** {data['collection']}\n"
                f"**Total chunks:** {data['total_chunks']}\n"
                f"**Indexed sources:**\n{sources_list}"
            )
            return [types.TextContent(type="text", text=text)]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
