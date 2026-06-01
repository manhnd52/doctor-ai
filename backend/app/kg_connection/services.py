from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.kg_connection.models import KnowledgeGraph
from app.kg_connection.schemas import (
    CreateKnowledgeGraphRequest, 
    UpdateKnowledgeGraphRequest,
    QueryRequest
)
from app.kg_connection.utils import KGSessionManager

def get_knowledge_graphs(db: Session):
    """Retrieve all knowledge graphs"""
    return db.query(KnowledgeGraph).all()

def get_active_knowledge_graph(db: Session):
    """Retrieve all active (aka available) knowledge graphs"""
    return db.query(KnowledgeGraph).filter(KnowledgeGraph.is_active == True).all()

def create_knowledge_graph(db: Session, request: CreateKnowledgeGraphRequest):
    """Create a new knowledge graph"""
    kg = KnowledgeGraph(
        name=request.name,
        description=request.description,
        uri=request.uri,
        database_name=request.database_name,
        username=request.username,
        password=request.password,
        is_active=True
    )
    # Load db info 
    
    db.add(kg)
    db.commit()
    db.refresh(kg)
    return kg

def update_knowledge_graph(db: Session, id: int, request: UpdateKnowledgeGraphRequest):
    """Update an existing knowledge graph"""
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    if request.name is not None:
        kg.name = request.name
    if request.description is not None:
        kg.description = request.description
    if request.uri is not None:
        kg.uri = request.uri
    if request.database_name is not None:
        kg.database_name = request.database_name
    if request.username is not None:
        kg.username = request.username
    if request.password is not None:
        kg.password = request.password
    if request.is_active is not None:
        kg.is_active = request.is_active
        
    db.commit()
    db.refresh(kg)
    return kg

def delete_knowledge_graph(db: Session, id: int):
    """Delete a knowledge graph"""
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    db.delete(kg)
    db.commit()
    return {"status": "success", "message": "Knowledge graph deleted successfully"}

def check_knowledge_graph_connection(db: Session, id: int):
    """Check Neo4j connection for an existing knowledge graph"""
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    manager = KGSessionManager()
    result = manager.validate_connection(kg)
    
    if result is None:
        return {
            "status": False,
            "message": "Failed to connect to Knowledge Graph",
            "error": "Connection error"
        }
    
    return {
        "status": True,
        "node_count": result.get("nodeCount", 0),
        "relationship_count": result.get("relationshipCount", 0),
        "message": "Connection check successful"
    }

def get_schema(db: Session, id: int):
    """Get the schema of the knowledge graph and cache it in the database"""
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    if kg.schema:
        return kg.schema
    
    manager = KGSessionManager()
    try:
        session = manager._create_kg_session(kg)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to establish Neo4j connection: {str(e)}"
        )
        
    try:
        # Fetch labels
        labels_res = session.run("CALL db.labels()")
        labels = [record[0] for record in labels_res]

        # Fetch relationship types
        rels_res = session.run("CALL db.relationshipTypes()")
        relationships = [record[0] for record in rels_res]
        
        # Try to get node type properties
        properties = []
        try:
            props_res = session.run("CALL db.schema.nodeTypeProperties()")
            properties = [dict(record) for record in props_res]
        except Exception:
            pass
            
        schema_data = {
            "node_labels": labels,
            "relationship_types": relationships,
            "properties": properties
        }
        
        kg.schema = schema_data
        db.commit()
        db.refresh(kg)
        
        return schema_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error querying Neo4j schema: {str(e)}"
        )
    finally:
        session.close()

def run_query(db: Session, request: QueryRequest):
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == request.knowledge_graph_id).first()
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    manager = KGSessionManager()
    try:
        session = manager._create_kg_session(kg)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to establish Neo4j connection: {str(e)}"
        )
    try:
        result = session.run(request.query)
        return [dict(record) for record in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")
    finally:
        session.close()
