from pydantic import BaseModel
from typing import Any


class ConfirmSchemaRequest(BaseModel):
    mapping: dict[str, Any]

