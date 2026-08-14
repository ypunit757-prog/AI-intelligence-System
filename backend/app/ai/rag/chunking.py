"""Text chunking with configurable size/overlap."""
from typing import List


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 4)

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    step = chunk_size - chunk_overlap
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
        start += step
    return chunks
