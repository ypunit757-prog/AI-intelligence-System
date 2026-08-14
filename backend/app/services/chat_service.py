from app.ai.rag.pipeline import run_rag, stream_rag
from app.repositories.conversation_repository import ConversationRepository


async def handle_chat(repo: ConversationRepository, user_id: str, conversation_id: str | None, message: str) -> dict:
    conversation = await repo.get_or_create(conversation_id, user_id)
    await repo.add_message(conversation.id, "user", message)

    result = await run_rag(message, user_id)
    await repo.add_message(conversation.id, "assistant", result.answer, sources=result.sources)

    return {"conversation_id": conversation.id, "answer": result.answer, "sources": result.sources}


async def handle_chat_stream(user_id: str, message: str):
    async for delta in stream_rag(message, user_id):
        yield delta
