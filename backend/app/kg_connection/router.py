from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.kg_connection.schemas import ConnectionRequest, ConnectionResponse, QueryRequest
from app.kg_connection.services import (
    add_kg_connection, 
    get_all_connections, 
    connect_to_kg, 
    delete_connection, 
    get_current_connection,
    run_query
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/kg", tags=["kg_connection"])

@router.post("/connect", response_model=ConnectionResponse)
def connect(
    payload: ConnectionRequest, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        connection = add_kg_connection(current_user, payload.uri, payload.database_name, payload.username, payload.password, db)
        return ConnectionResponse(
            connection_id=connection.id, 
            node_count=connection.node_count, 
            relationship_count=connection.relationship_count, 
            status=True, 
            message="Connection added successfully"
        )
    
    except Exception as e:
        return ConnectionResponse(error=str(e), status=False)

@router.get("/connections")
def get_connections(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        connections = get_all_connections(current_user, db)
        return connections
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 

@router.post("/connect/{connection_id}")
def reconnect(
    connection_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        connection = connect_to_kg(current_user, connection_id, db)
        return ConnectionResponse(connection_id=connection.id, status=True, message="Connected to knowledge graph successfully")
    
    except Exception as e:
        return ConnectionResponse(error=str(e), status=False)

@router.delete("/connections/{connection_id}")
def delete_connection_endpoint(
    connection_id: int, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        delete_connection(current_user, connection_id, db)
        return {"status": True, "message": "Connection deleted successfully"}
    
    except Exception as e:
        return {"status": False, "error": str(e)}

@router.get("/current")
def get_current_connection_endpoint(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    try:
        current_connection = get_current_connection(current_user, db)
        if not current_connection:
            return {"status": False, "message": "No active connection found"}
        return {"status": True, "current_connection": current_connection}
    
    except Exception as e:
        return {"status": False, "error": str(e)}
    
@router.post("/query")
def query_kg(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        result = run_query(current_user, payload.query, db)
        return {"status": True, "result": result}
    except Exception as e:
        return {"status": False, "error": str(e)}