import pytest
from unittest.mock import AsyncMock, Mock, patch
from api.services.embedder import normalize_embedding
from api.services.llm import generate, warm_up
from api.services.retriever import _distance_to_score


@pytest.mark.asyncio
async def test_generate_calls_ollama():
    mock_response = Mock()
    mock_response.json.return_value = {"response": "Likely a memory leak. Restart the pod and check limits."}

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
    mock_response = Mock()
    mock_response.json.return_value = {"response": "  Check the logs.  \n"}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await generate("what happened?", ["some context"])

    assert result == "Check the logs."


@pytest.mark.asyncio
async def test_warm_up_loads_ollama_model_with_minimal_generation():
    mock_response = Mock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        await warm_up()

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["prompt"] == "ready"
    assert payload["stream"] is False
    assert payload["options"]["num_predict"] == 1
    mock_response.raise_for_status.assert_called_once()


def test_distance_to_score_is_bounded():
    assert _distance_to_score(0) == 1.0
    assert 0 < _distance_to_score(404.5872) < 1
    assert _distance_to_score(-1) == 0.0


def test_normalize_embedding_returns_unit_vector():
    assert normalize_embedding([3.0, 4.0]) == [0.6, 0.8]
    assert normalize_embedding([0.0, 0.0]) == [0.0, 0.0]
