from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import app.chat.models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.chat.models import ChatSession
    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user")
