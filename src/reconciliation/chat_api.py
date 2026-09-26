from pathlib import Path
from typing import Literal

import anthropic
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from reconciliation.agent import run_agent
from reconciliation.users import DEMO_USERS

router = APIRouter(tags=["chat"])

CHAT_PAGE = Path(__file__).parent / "static" / "chat.html"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    user_id: str = Field(max_length=50)
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class ToolCallOut(BaseModel):
    name: str
    arguments: dict
    is_error: bool


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallOut]
    input_tokens: int
    output_tokens: int


class UserOut(BaseModel):
    id: str
    name: str
    role: str


@router.get("/chat", response_class=HTMLResponse, include_in_schema=False)
def chat_page() -> str:
    return CHAT_PAGE.read_text(encoding="utf-8")


@router.get("/api/users")
def list_users() -> list[UserOut]:
    return [UserOut(id=user.id, name=user.name, role=user.role) for user in DEMO_USERS.values()]


@router.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    user = DEMO_USERS.get(request.user_id)
    if user is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Utente non riconosciuto")
    if request.messages[-1].role != "user":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "L'ultimo messaggio deve essere dell'utente")

    try:
        result = await run_agent([message.model_dump() for message in request.messages], user)
    except anthropic.APIError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Servizio LLM non disponibile") from error

    return ChatResponse(
        reply=result.text,
        tool_calls=[
            ToolCallOut(name=call.name, arguments=call.arguments, is_error=call.is_error)
            for call in result.tool_calls
        ],
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )