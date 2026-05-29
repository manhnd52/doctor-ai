from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.auth.dependencies import get_current_user
from backend.app.pipeline_data.services import get_pipeline_run_by_id

router = APIRouter(prefix="/pipeline", tags=["pipeline_data"])

@router.get("/{pipeline_run_id}")
def get_pipeline_run(
    pipeline_run_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = get_pipeline_run_by_id(db, current_user, pipeline_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run

