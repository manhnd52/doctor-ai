from pydantic import BaseModel

class ConnectionRequest(BaseModel):
    uri: str
    database_name: str
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str

class ConnectionResponse(BaseModel):
    status: bool
    connection_id: int | None = None
    node_count: int | None = None
    relationship_count: int | None = None
    message: str | None = None
    error: str | None = None

