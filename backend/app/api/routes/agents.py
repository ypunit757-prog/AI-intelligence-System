from fastapi import APIRouter, Depends

from app.ai.agents.graph import run_agent
from app.database.models import User
from app.schemas.agent import AgentRequest, AgentResponse
from app.security.auth import get_current_user

router = APIRouter(tags=["agent"])


@router.post("/agent", response_model=AgentResponse)
async def agent(payload: AgentRequest, user: User = Depends(get_current_user)):
    result = await run_agent(payload.question, user_id=user.id)
    return AgentResponse(**result)
