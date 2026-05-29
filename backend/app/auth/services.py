from sqlalchemy.orm import Session
from app.auth.models import User
from app.auth.utils import verify_password, hash_password
from app.auth.exceptions import InvalidCredentialsException, InactiveUserException


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise InvalidCredentialsException()

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException()

    if not user.is_active:
        raise InactiveUserException()

    return user


def register_user(db: Session, username: str, password: str) -> User:
    hashed_password = hash_password(password)
    user = db.query(User).filter(User.username == username).first()

    if user:
        raise Exception("Username already exists")

    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user