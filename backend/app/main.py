from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import process_message
from app.config import settings
from app.memory import clear_memory, clear_paused, get_memory, is_paused, list_chat_phones
from app.schemas import (
    ChatResponse,
    CreateChatRequest,
    SendMessageRequest,
    SendMessageResponse,
)

app = FastAPI(title="Real Estate Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/chats")
async def get_chats() -> dict:
    return {"phones": await list_chat_phones()}


@app.post("/chats", response_model=ChatResponse)
async def create_chat(payload: CreateChatRequest) -> ChatResponse:
    phone = payload.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")

    await clear_memory(phone)
    await clear_paused(phone)
    memory = await get_memory(phone)

    return ChatResponse(phone=phone, messages=memory["messages"], paused=False)


@app.get("/chats/{phone}", response_model=ChatResponse)
async def get_chat(phone: str) -> ChatResponse:
    memory = await get_memory(phone)
    return ChatResponse(phone=phone, messages=memory["messages"], paused=await is_paused(phone))


@app.post("/chats/{phone}/messages", response_model=SendMessageResponse)
async def send_message(phone: str, payload: SendMessageRequest) -> SendMessageResponse:
    response = await process_message(phone=phone, text=payload.text.strip())
    return SendMessageResponse(response=response, paused=await is_paused(phone))
