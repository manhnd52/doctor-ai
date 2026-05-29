from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.chat.constants import MessageRole
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.auth.models import User
    from app.pipeline_data.models import PipelineRun

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, default="New chat", nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    chat_session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    pipeline_run: Mapped[Optional["PipelineRun"]] = relationship("PipelineRun", back_populates="message", uselist=False, cascade="all, delete-orphan")

