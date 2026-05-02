import pytest
from unittest.mock import AsyncMock, patch
from api.services.llm import generate


@pytest.mark.asyncio
async def test_generate_calls_ollama():
    mock_response = AsyncMock()
    mock_response.json.return_value = {"response": "Likely a memory leak. Restart the pod and check limits."}
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await generate("payment service OOMKilled", ["OOMKilled usually means memory limit exceeded"])

    assert "memory" in result.lower() or "restart" in result.lower()


@pytest.mark.asyncio
async def test_generate_strips_whitespace():
    mock_response = AsyncMock()
    mock_response.json.return_value = {"response": "  Check the logs.  \n"}
    mock_response.raise_for_status = AsyncMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await generate("what happened?", ["some context"])

    assert result == "Check the logs."
