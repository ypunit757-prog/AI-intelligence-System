from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.security.auth import get_current_user
from app.services.chat_service import handle_chat, handle_chat_stream

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.stream:
        async def event_stream():
            async for delta in handle_chat_stream(user.id, payload.message):
                yield f"data: {delta}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    repo = ConversationRepository(db)
    result = await handle_chat(repo, user.id, payload.conversation_id, payload.message)
    return ChatResponse(**result)


@router.get("/conversations")
async def list_conversations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ConversationRepository(db)
    return await repo.list_for_user(user.id)


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ConversationRepository(db)
    return await repo.get_messages(conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    repo = ConversationRepository(db)
    conversation = await repo.get_or_create(conversation_id, user.id)
    await repo.delete(conversation)
