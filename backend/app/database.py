import os
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator


# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")
if DATABASE_URL.startswith("sqlite:///"):
    # Convert relative sqlite path to absolute path
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    import os
    # Ensure it's resolved relative to the backend folder (which contains database.py)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = f"sqlite:///{os.path.join(backend_dir, db_path)}"

# Create engine
engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session for FastAPI routes.
    Usage: def your_route(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - creates all tables based on models."""

    Base.metadata.create_all(bind=engine)


def close_db() -> None:
    """Close database connection."""
    engine.dispose()
