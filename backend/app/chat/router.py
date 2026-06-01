from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.chat import services
from app.chat.schemas import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    MessageRequest,
    MessageResponse,
)
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/chat", tags=["chat"])

# POST /sessions: Create a new chat session, return session_id
@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(
    request: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session, return session_id"""
    return services.create_chat_session(
        db=db, 
        title=request.title, 
        user_id=current_user.id, 
        kg_id=request.knowledge_graph_id
    )

# GET /sessions: Get the list of chat sessions for the user
@router.get("/sessions", response_model=list[ChatSessionResponse])
def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the list of chat sessions for the user"""
    return services.get_chat_sessions(db=db, user_id=current_user.id)

# GET /sessions/{session_id}: Get detailed information about a chat session
@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed information about a chat session, including title, created at, and messages"""
    return services.get_chat_session_by_id(db=db, session_id=session_id, user_id=current_user.id)


# DELETE /sessions/{session_id}: Delete a chat session and all its messages
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat session and cascade delete all its messages """
    services.delete_chat_session(db=db, session_id=session_id, user_id=current_user.id)


# PATCH /sessions/{session_id}: Update title of the chat session.
@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
def update_session(
    session_id: int,
    request: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the title of a chat session."""
    return services.update_chat_session(db=db, session_id=session_id, title=request.title, user_id=current_user.id)


# POST /sessions/{session_id}/messages: Send a new message
@router.post("/sessions/{session_id}/messages")
def create_message(
    session_id: int,
    request: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a new message in the chat session, return the created message with id and timestamp"""
    chat_response = services.stream_chat_message(db=db, session_id=session_id, content=request.content, user_id=current_user.id)

    return EventSourceResponse(chat_response)


# GET /sessions/{session_id}/messages: Get all messages in a chat session
@router.get("/sessions/{session_id}/messages")
def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all messages in a chat session"""
    return services.get_chat_messages(db=db, session_id=session_id, user_id=current_user.id)
