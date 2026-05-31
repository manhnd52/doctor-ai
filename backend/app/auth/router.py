from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.schemas import LoginRequest, TokenResponse, RegisterRequest, RegisterResponse
from app.auth.services import authenticate_user, register_user
from app.auth.utils import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    access_token = create_access_token(subject=user.username)
    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload.username, payload.password)
        access_token = create_access_token(subject=user.username)
        return RegisterResponse(status=True, access_token=access_token, errors=[])
    except Exception as e:
        return RegisterResponse(status=False, errors=[str(e)])

@router.get("/me")
def read_current_user(current_user = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}
