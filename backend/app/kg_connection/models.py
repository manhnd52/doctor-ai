from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.auth.models import User

class KgConnection(Base):
    __tablename__ = "kg_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    uri: Mapped[str] = mapped_column(String(512), nullable=False)
    database_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), default="neo4j", nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, nullable=True)
    relationship_count: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user: Mapped["User"] = relationship("User")

class Connecting(Base):
    __tablename__ = "connecting"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    kg_connection_id: Mapped[int] = mapped_column(Integer, ForeignKey("kg_connections.id"), nullable=False)
    user: Mapped["User"] = relationship("User")
    kg_connection: Mapped["KgConnection"] = relationship("KgConnection")
