def chunk_text(text: str, max_chars: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks of at most max_chars characters."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        # try to break at a paragraph or sentence boundary
        if end < len(text):
            for sep in ("\n\n", "\n", ". ", " "):
                idx = chunk.rfind(sep)
                if idx > max_chars // 2:
                    chunk = chunk[: idx + len(sep)]
                    break
        chunks.append(chunk.strip())
        start += len(chunk) - overlap

    return [c for c in chunks if c]
