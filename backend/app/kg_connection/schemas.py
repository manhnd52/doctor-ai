from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class QueryRequest(BaseModel):
    knowledge_graph_id: int
    query: str

class CreateKnowledgeGraphRequest(BaseModel):
    name: str
    description: str | None = None
    uri: str
    database_name: str
    username: str
    password: str

class UpdateKnowledgeGraphRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    uri: str | None = None
    database_name: str | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None

class CheckKnowledgeGraphConnectionRequest(BaseModel):
    pass

class KnowledgeGraphResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    uri: str
    database_name: str
    is_active: bool
    created_at: datetime
    schema: Optional[dict] = None

    class Config:
        from_attributes = True

