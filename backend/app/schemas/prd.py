from pydantic import BaseModel


class PrdGenerateRequest(BaseModel):
    opportunity_id: int
    project_id: int = 1
    conversation_id: str | None = None


class PrdUpdateRequest(BaseModel):
    prd_markdown: str


class PrdExportRequest(BaseModel):
    title: str = "prd"
    prd_markdown: str
