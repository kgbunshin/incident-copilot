import json


SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "apikey", "authorization", "passwd"}


def _sanitize(obj: dict) -> dict:
    return {
        k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else v
        for k, v in obj.items()
    }


def parse(content: str) -> list[str]:
    """Parse newline-delimited JSON or a JSON array of log entries."""
    entries = []
    try:
        data = json.loads(content)
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = [data]
    except json.JSONDecodeError:
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    result = []
    for entry in entries:
        if isinstance(entry, dict):
            entry = _sanitize(entry)
            result.append(json.dumps(entry, ensure_ascii=False))
    return result
