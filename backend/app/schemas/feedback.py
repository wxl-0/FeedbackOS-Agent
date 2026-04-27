from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    feedback_text: str
    project_id: int = 1

