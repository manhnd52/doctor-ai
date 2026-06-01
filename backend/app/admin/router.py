from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_admin
from app.kg_connection.schemas import (
    CreateKnowledgeGraphRequest,
    UpdateKnowledgeGraphRequest,
    QueryRequest
)
from app.kg_connection.services import (
    get_knowledge_graphs,
    create_knowledge_graph,
    update_knowledge_graph,
    delete_knowledge_graph,
    check_knowledge_graph_connection,
    get_schema,
    run_query
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/")
def hi_admin(
    db: Session = Depends(get_db), 
    current_user = Depends(require_admin)
):
    try:
        return {
            "status": True, 
            "message": f"Hello, admin {current_user.username}!!"
        }
    except Exception as e:
        return {"status": False, "error": str(e)}

# CRUD Knowledge Graphs
@router.get("/knowledge-graphs")
def get_all_kg(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Retrieve all knowledge graphs"""
    return get_knowledge_graphs(db)

@router.post("/knowledge-graphs")
def create_kg(
    request: CreateKnowledgeGraphRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Create a new knowledge graph"""
    return create_knowledge_graph(db, request)

@router.get("/knowledge-graphs/{id}")
def get_kg_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get a knowledge graph by id"""
    from app.kg_connection.models import KnowledgeGraph
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    return kg

@router.put("/knowledge-graphs/{id}")
def update_kg(
    id: int,
    request: UpdateKnowledgeGraphRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update an existing knowledge graph"""
    return update_knowledge_graph(db, id, request)

@router.delete("/knowledge-graphs/{id}")
def delete_kg(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Delete a knowledge graph"""
    return delete_knowledge_graph(db, id)

@router.post("/knowledge-graphs/{id}/check")
def check_kg_conn(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Check Neo4j connection for a knowledge graph"""
    return check_knowledge_graph_connection(db, id)

@router.post("/knowledge-graphs/{id}/schema")
def fetch_and_cache_schema(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Generate and cache the schema of a knowledge graph"""
    return get_schema(db, id)

@router.post("/knowledge-graphs/query")
def execute_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Run cypher query on a specific knowledge graph"""
    return run_query(db, request)
