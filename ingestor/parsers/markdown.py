import re


def parse(content: str) -> list[str]:
    """Split markdown by H2/H3 headings, returning non-empty sections."""
    sections = re.split(r"\n#{2,3} ", content)
    result = []
    for section in sections:
        cleaned = section.strip()
        if len(cleaned) > 50:
            result.append(cleaned)
    return result
