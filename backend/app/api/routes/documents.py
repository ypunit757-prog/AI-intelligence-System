from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.documents import DocumentResponse
from app.security.auth import get_current_user
from app.services.document_service import DocumentValidationError, delete_document, reindex_document, upload_and_process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = DocumentRepository(db)
    data = await file.read()
    try:
        document = await upload_and_process_document(
            repo, user_id=user.id, filename=file.filename or "unnamed", data=data, mime_type=file.content_type or ""
        )
    except DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return document


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = DocumentRepository(db)
    return await repo.list_for_user(user.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = DocumentRepository(db)
    document = await repo.get_for_user(document_id, user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.delete("/{document_id}", status_code=204)
async def remove_document(document_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = DocumentRepository(db)
    document = await repo.get_for_user(document_id, user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    await delete_document(repo, document)


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
async def reindex(document_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = DocumentRepository(db)
    document = await repo.get_for_user(document_id, user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    await reindex_document(repo, document)
    return document
