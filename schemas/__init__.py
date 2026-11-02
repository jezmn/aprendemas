from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str | None = "default_user"
    pdf_page: int | None = None
    pdf_name: str | None = None
    show_thinking: bool | None = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_count: int = 0
    title: str | None = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    history: list[dict]
    total_messages: int
