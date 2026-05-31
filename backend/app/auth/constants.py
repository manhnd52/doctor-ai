import os
from enum import Enum


class ErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    USER_INACTIVE = "USER_INACTIVE"


class UserRole(str, Enum):
    USER = "User"
    ADMIN = "Admin"


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "please-change-this-secret")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60