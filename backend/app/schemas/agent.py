from pydantic import BaseModel


class AgentRunRequest(BaseModel):
    task: str
    project_id: int = 1
    user_id: str = "local_user"

