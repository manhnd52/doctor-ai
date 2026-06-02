from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin
from app.auth.models import User
from app.kg_connection import services
from app.kg_connection.schemas import (
    CreateKnowledgeGraphRequest,
    UpdateKnowledgeGraphRequest,
    CheckKnowledgeGraphConnectionRequest,
    KnowledgeGraphResponse,
)

router = APIRouter(prefix="/knowledge-graphs", tags=["kg"])

@router.get("/", response_model=list[KnowledgeGraphResponse])
def get_knowledge_graphs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Depend on the role of the request:
    - If the request is from an admin, return all knowledge graphs
    - If the request is from a user, return only active knowledge graphs
    """
    if current_user.role == "admin":
        return services.get_knowledge_graphs(db=db)
    else: 
        return services.get_active_knowledge_graph(db=db)

@router.post("/", response_model=KnowledgeGraphResponse)
def create_knowledge_graph(
    request: CreateKnowledgeGraphRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new knowledge graph"""
    return services.create_knowledge_graph(db=db, request=request)

@router.get("/{id}") 
def get_knowledge_graph(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a knowledge graph"""
    kg = services.get_knowledge_graph_by_id(db=db, id=id)
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    return kg

@router.put("/{id}", response_model=KnowledgeGraphResponse)
def update_knowledge_graph(
    id: int,
    request: UpdateKnowledgeGraphRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a knowledge graph"""
    return services.update_knowledge_graph(db=db, id=id, request=request)

@router.delete("/{id}")
def delete_knowledge_graph(
    id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a knowledge graph"""
    return services.delete_knowledge_graph(db=db, id=id)

@router.post("/{id}/check")
def check_knowledge_graph_connection(
    id: int,
    request: CheckKnowledgeGraphConnectionRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Check knowledge graph connection"""
    return services.check_knowledge_graph_connection(db=db, id=id)

@router.get("/{id}/schema")
def get_schema(
    id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get the schema of the knowledge graph"""
    return services.refresh_schema(db=db, id=id)