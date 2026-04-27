from pydantic import BaseModel


class ConversationCreateRequest(BaseModel):
    title: str | None = None
    project_id: int = 1


class ConversationMessageRequest(BaseModel):
    conversation_id: str
    role: str
    content: str
