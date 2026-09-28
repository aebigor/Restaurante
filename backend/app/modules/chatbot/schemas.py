from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: str = Field(pattern="^(user|bot)$")
    content: str = Field(min_length=1, max_length=1000)


class ChatMessage(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=12)


class SupportRequestCreate(BaseModel):
    message: str = Field(default="Necesito hablar con una persona.", max_length=500)
