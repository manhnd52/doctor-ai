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

def get_knowledge_graph_by_id(db: Session, id: int):
    """Retrieve a knowledge graph"""
    return db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()

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
    
    return refresh_schema(db, id)

def refresh_schema(db: Session, id: int):
    """Refresh the schema of the knowledge graph and cache it in the database"""
    kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == id).first()
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
        # 1. Fetch labels
        labels_res = session.run("CALL db.labels()")
        label_names = [record[0] for record in labels_res]

        # 2. Fetch properties
        properties_by_label = {}
        try:
            props_res = session.run("CALL db.schema.nodeTypeProperties()")
            for record in props_res:
                rec_dict = dict(record)
                node_labels = rec_dict.get("nodeType") or rec_dict.get("nodeLabels")
                prop_name = rec_dict.get("propertyName")
                prop_types = rec_dict.get("propertyTypes")
                
                if not node_labels or not prop_name:
                    continue
                    
                if isinstance(node_labels, str):
                    node_labels = [node_labels]
                    
                for label in node_labels:
                    clean_label = label.lstrip(":") if isinstance(label, str) else str(label)
                    clean_label = clean_label.strip("`").strip()
                    if clean_label not in properties_by_label:
                        properties_by_label[clean_label] = []
                    
                    prop_type = prop_types[0].lower()
                    properties_by_label[clean_label].append({
                        "name": prop_name,
                        "type": prop_type
                    })
        except Exception as e:
            print(f"Error fetching schema properties: {e}")

        # 3. Assemble labels list
        labels_list = []
        for idx, name in enumerate(label_names):
            labels_list.append({
                "name": name,
                "description": f"Nodes with label {name}",
                "properties": properties_by_label.get(name, [])
            })

        # 4. Fetch relationships with source and target
        relationships_list = []
        try:
            rels_query = """
            MATCH (a)-[r]->(b)
            WITH labels(a) AS a_labels, type(r) AS rel_type, labels(b) AS b_labels
            UNWIND a_labels AS source
            UNWIND b_labels AS target
            RETURN DISTINCT rel_type AS name, source, target
            """
            rels_res = session.run(rels_query)
            for record in rels_res:
                rec_dict = dict(record)
                relationships_list.append({
                    "name": rec_dict.get("name"),
                    "source": rec_dict.get("source"),
                    "target": rec_dict.get("target"),
                    "properties": []
                })
        except Exception:
            pass

        schema_data = {
            "labels": labels_list,
            "relationships": relationships_list
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
