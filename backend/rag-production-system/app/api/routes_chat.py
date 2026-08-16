from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_rag_service
from app.core.security import validate_session_id
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    SessionHistoryResponse,
    SessionSummary,
)
from app.rag.service import RagService

router = APIRouter(tags=["chat"])


def _sse(event: str, data) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode()


# STATIC ROUTES MUST BE DECLARED BEFORE PARAMETERIZED ROUTES
@router.get("/chat/sessions", response_model=list[SessionSummary])
async def list_sessions(service: RagService = Depends(get_rag_service)):
    sessions = await service.history.list_sessions()
    return [SessionSummary(**s) for s in sessions]


@router.get("/chat/{session_id}/messages", response_model=SessionHistoryResponse)
async def get_session_messages(session_id: str, service: RagService = Depends(get_rag_service)):
    try:
        valid_id = validate_session_id(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    messages = await service.history.get_messages(valid_id)
    return SessionHistoryResponse(session_id=valid_id, messages=messages)


@router.post("/chat", response_model=ChatResponse | None)
async def chat(request: ChatRequest, service: RagService = Depends(get_rag_service)):
    try:
        session_id = validate_session_id(request.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not request.stream:
        return await service.answer(session_id, request.message)

    async def generator():
        async for item in service.stream(session_id, request.message):
            yield _sse(item["event"], item["data"])

    return StreamingResponse(generator(), media_type="text/event-stream")
