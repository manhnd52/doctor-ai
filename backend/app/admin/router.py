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
from app.auth.dependencies import require_admin

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
