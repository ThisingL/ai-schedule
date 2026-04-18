from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    related_task_ids: Optional[list] = None
    created_at: datetime

    model_config = {"from_attributes": True}
