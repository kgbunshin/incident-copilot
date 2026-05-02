import pytest
from ingestor.parsers import markdown, json_logs, alertmanager
from ingestor.chunker import chunk_text
from ingestor.pipeline import ingest_bytes, ingest_alert_payload


def test_markdown_parse_splits_on_headings():
    content = "# Title\n## Section One\nSome content here that is long enough to pass the filter.\n## Section Two\nAnother section with sufficient content to include."
    result = markdown.parse(content)
    assert len(result) == 2
    assert "Section One" in result[0]


def test_markdown_parse_filters_short_sections():
    content = "## Short\nHi\n## Long enough section\nThis section has more than fifty characters of content here."
    result = markdown.parse(content)
    assert len(result) == 1


def test_json_logs_parse_ndjson():
    content = '{"level":"error","msg":"OOM","service":"payment"}\n{"level":"warn","msg":"high latency","service":"api"}'
    result = json_logs.parse(content)
    assert len(result) == 2
    assert "payment" in result[0]


def test_json_logs_sanitizes_secrets():
    content = '{"token":"supersecret","msg":"login failed"}'
    result = json_logs.parse(content)
    assert "supersecret" not in result[0]
    assert "[REDACTED]" in result[0]


def test_json_logs_parse_array():
    content = '[{"level":"info","msg":"started"},{"level":"error","msg":"crashed"}]'
    result = json_logs.parse(content)
    assert len(result) == 2


def test_alertmanager_parse():
    payload = {
        "status": "firing",
        "groupKey": "test-group",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighCPU", "service": "api"},
                "annotations": {"summary": "CPU above 90%"},
                "startsAt": "2024-01-14T10:00:00Z",
            }
        ],
        "commonLabels": {},
        "commonAnnotations": {},
    }
    result = alertmanager.parse(payload)
    assert len(result) == 1
    assert "HighCPU" in result[0]
    assert "CPU above 90%" in result[0]


def test_chunk_text_short_passthrough():
    text = "short text"
    result = chunk_text(text, max_chars=1000)
    assert result == ["short text"]


def test_chunk_text_splits_long():
    text = "word " * 300  # ~1500 chars
    result = chunk_text(text, max_chars=500, overlap=50)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 510  # small margin for boundary search


def test_chunk_text_handles_tail_smaller_than_overlap():
    text = "word " * 101  # final chunk is shorter than overlap
    result = chunk_text(text, max_chars=500, overlap=50)
    assert result[-1]
    assert "".join(chunk.replace(" ", "") for chunk in result)


@pytest.mark.asyncio
async def test_ingest_bytes_markdown():
    content = b"# Runbook\n## Step One\nDo this and that to resolve the incident when things go wrong in production.\n## Step Two\nCheck metrics and logs for anomalies before escalating to on-call engineer."
    chunks = await ingest_bytes(content, filename="runbook.md")
    assert len(chunks) >= 1


@pytest.mark.asyncio
async def test_ingest_bytes_json():
    content = b'{"level":"error","msg":"disk full","host":"web-01"}'
    chunks = await ingest_bytes(content, filename="app.json")
    assert len(chunks) == 1


@pytest.mark.asyncio
async def test_ingest_alert_payload():
    payload = {
        "status": "firing",
        "alerts": [{"status": "firing", "labels": {"alertname": "DiskFull"}, "annotations": {"summary": "Disk usage above 95%"}, "startsAt": "2024-01-14T10:00:00Z"}],
        "commonLabels": {},
        "commonAnnotations": {},
    }
    chunks = await ingest_alert_payload(payload)
    assert len(chunks) >= 1
    assert "DiskFull" in chunks[0]
