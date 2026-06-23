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


class ChunkInfo(BaseModel):
    page: int | None = None
    chunk: str = ""
    score: float = 0.0


class GroupedSource(BaseModel):
    filename: str
    chunks: list[ChunkInfo]
    avg_score: float = 0.0
    total_chunks: int = 0


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    grouped_sources: list[GroupedSource] = []
