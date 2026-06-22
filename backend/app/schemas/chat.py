from pydantic import BaseModel


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    query: str
    limit: int = 5
    history: list[Message] = []


class Source(BaseModel):
    filename: str | None
    page: int | None
    chunk: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
