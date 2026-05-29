from sqlalchemy import (
    Integer,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base
from app.pipeline_data.constants import PipelineRunStatus
from app.chat.models import ChatMessage

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    final_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PipelineRunStatus] = mapped_column(Enum(PipelineRunStatus), nullable=False)
    trace_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
  
    message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="pipeline_run", uselist=False)