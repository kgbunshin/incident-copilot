def chunk_text(text: str, max_chars: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks of at most max_chars characters."""
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to zero")
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")

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
        if end >= len(text):
            break
        start += max(len(chunk) - overlap, 1)

    return [c for c in chunks if c]
