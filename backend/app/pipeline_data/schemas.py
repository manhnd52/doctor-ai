from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from app.pipeline_data.constants import PipelineRunStatus

class PipelineRunResponse(BaseModel):
    id: int
    message_id: int
    question: str
    query: str
    final_answer: Optional[str] = None
    status: PipelineRunStatus
    trace_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
