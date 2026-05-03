from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32)


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class MessageItem(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    phone: str
    messages: list[MessageItem]
    paused: bool


class SendMessageResponse(BaseModel):
    response: str | None
    paused: bool
