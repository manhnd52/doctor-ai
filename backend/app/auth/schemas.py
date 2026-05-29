from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    username: str
    password: str

class RegisterResponse(BaseModel):
    status: bool
    access_token: str | None = None
    errors: list[str] = []