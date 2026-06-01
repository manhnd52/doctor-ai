from datetime import datetime
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.auth.models import User

class KnowledgeGraph(Base):
    __tablename__ = "knowledge_graphs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uri: Mapped[str] = mapped_column(String(512), nullable=False)
    database_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="knowledge_graph")

KgConnection = KnowledgeGraph