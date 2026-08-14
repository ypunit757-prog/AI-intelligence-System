from app.ai.rag.chunking import chunk_text


def test_chunk_text_basic():
    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 20 for c in chunks)


def test_chunk_text_empty():
    assert chunk_text("", chunk_size=20, chunk_overlap=5) == []


def test_chunk_text_overlap_guard():
    # overlap >= chunk_size must not infinite-loop or error
    text = "a b c d e f g h"
    chunks = chunk_text(text, chunk_size=5, chunk_overlap=10)
    assert len(chunks) >= 1
