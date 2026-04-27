from pydantic import BaseModel
from typing import Any


class MemoryConfirmRequest(BaseModel):
    memory_id: int | None = None
    memory_type: str = "project"
    content: dict[str, Any] | None = None
    confirmed: bool = True
    project_id: int = 1
    user_id: str = "local_user"

