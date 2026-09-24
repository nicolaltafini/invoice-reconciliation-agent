from typing import Literal

import anthropic
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from reconciliation.agent import run_agent

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
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


@router.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    if request.messages[-1].role != "user":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "L'ultimo messaggio deve essere dell'utente")

    try:
        result = await run_agent([message.model_dump() for message in request.messages])
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