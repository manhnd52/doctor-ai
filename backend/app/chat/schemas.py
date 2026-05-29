from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.chat.constants import MessageRole
from app.pipeline_data.schemas import PipelineRunResponse

class MessageBase(BaseModel):
    content: str

class MessageRequest(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    role: MessageRole
    created_at: datetime
    pipeline_run: Optional[PipelineRunResponse] = None

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: str = "New chat"

class ChatSessionUpdate(BaseModel):
    title: str

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True # Allow creating a Pydantic model from an ORM object by reading data from its attributes

class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[MessageResponse] = []
