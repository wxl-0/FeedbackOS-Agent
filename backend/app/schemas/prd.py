from pydantic import BaseModel


class PrdGenerateRequest(BaseModel):
    opportunity_id: int
    project_id: int = 1
    conversation_id: str | None = None
