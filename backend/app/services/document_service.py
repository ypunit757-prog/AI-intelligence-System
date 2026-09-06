"""Document ingestion pipeline:
upload -> validate -> store -> extract -> clean -> chunk -> metadata -> embed -> vector store
"""
import re
import uuid

from app.ai.retrieval.factory import get_embedding_model
from app.ai.rag.chunking import chunk_text
from app.ai.rag.document_loader import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, extract_text
from app.ai.retrieval.factory import get_vector_store
from app.config.settings import get_settings
from app.database.models import Document
from app.repositories.document_repository import DocumentRepository
from app.storage.factory import get_storage


class DocumentValidationError(Exception):
    pass


def _validate(filename: str, size: int) -> None:
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise DocumentValidationError(f"Unsupported file type: {filename}")
    if size > MAX_FILE_SIZE_BYTES:
        raise DocumentValidationError("File exceeds the 25MB size limit.")


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _safe_storage_key(user_id: str, filename: str) -> str:
    # Strip path components entirely to prevent traversal via filename.
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"{user_id}/{uuid.uuid4()}_{safe_name}"


async def upload_and_process_document(
    repo: DocumentRepository, user_id: str, filename: str, data: bytes, mime_type: str
) -> Document:
    _validate(filename, len(data))

    storage = get_storage()
    key = _safe_storage_key(user_id, filename)
    await storage.upload(key, data, content_type=mime_type)

    document = Document(user_id=user_id, filename=filename, storage_key=key, mime_type=mime_type, size=len(data), status="uploaded")
    document = await repo.create(document)

    try:
        await _process_document(document, data)
        await repo.update_status(document, "indexed")
    except Exception as e:
        await repo.update_status(document, "failed", error_message=str(e))
        raise

    return document


async def _process_document(document: Document, data: bytes) -> None:
    settings = get_settings()
    raw_text = extract_text(document.filename, data)
    cleaned = _clean_text(raw_text)
    chunks = chunk_text(cleaned, settings.chunk_size, settings.chunk_overlap)

    if not chunks:
        return

    embedder = get_embedding_model()
    vectors = embedder.embed_documents(chunks)

    store = get_vector_store()
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        await store.add(
            chunk_id=str(uuid.uuid4()),
            document_id=document.id,
            content=chunk,
            embedding=vector,
            metadata={"chunk_index": i, "filename": document.filename, "user_id": document.user_id},
        )


async def reindex_document(repo: DocumentRepository, document: Document) -> None:
    storage = get_storage()
    data = await storage.download(document.storage_key)

    store = get_vector_store()
    await store.delete_by_document(document.id)

    await repo.update_status(document, "processing")
    try:
        await _process_document(document, data)
        await repo.update_status(document, "indexed")
    except Exception as e:
        await repo.update_status(document, "failed", error_message=str(e))
        raise


async def delete_document(repo: DocumentRepository, document: Document) -> None:
    storage = get_storage()
    store = get_vector_store()
    await store.delete_by_document(document.id)
    try:
        await storage.delete(document.storage_key)
    except FileNotFoundError:
        pass
    await repo.delete(document)
