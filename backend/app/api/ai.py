from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.common.response import Response
from app.services import ai_service
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.services import agent_service
import json

router = APIRouter(prefix="/ai", tags=["AI相关的api"])


def _sse_line(payload: dict) -> str:
    return f"data:{json.dumps(payload,ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    # 让流式 Agent 拥有并管理自己的数据库 Session，而不是依赖鉴权阶段的 Session。
    async def event_gen():
        with SessionLocal() as db:
            stream_user = db.get(User, user_id)
            if stream_user is None or stream_user.status != 1:
                yield _sse_line(
                    {"type": "error", "message": "用户不存在或者用户被禁用,请重新登录"}
                )
                return

            async for event in agent_service.stream_agent(
                db=db, data=data, current_user=stream_user
            ):
                yield _sse_line(event)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
