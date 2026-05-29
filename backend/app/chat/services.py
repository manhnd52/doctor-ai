import os
from sqlalchemy.orm import Session, joinedload
from app.auth.models import User
import asyncio
from typing import List
from app.chat.models import ChatSession, ChatMessage, MessageRole
from app.chat.exceptions import ChatSessionNotFoundException
from app.pipeline_data.models import PipelineRun
from app.pipeline_data.constants import PipelineRunStatus, STEP_DISPLAY_NAMES, PipelineErrorEventData, SSEEventType, PipelineStep
from app.kg_connection.services import get_current_connection
from app.pipeline_data.services import format_context_for_pipeline
import json

async def chat_generator(chat_responses: List[ChatMessage]):
    for i in range(len(chat_responses)):
        yield {
            "event": f"Step {i+1}",
            "data": f"Response {i+1}: {chat_responses[i].content}",
        }
        await asyncio.sleep(1) # stop for 1 second but leave the CPU free to do other work


def get_chat_session_by_id(db: Session, session_id: int, user_id: int) -> ChatSession:
    """Retrieve a chat session by id and user_id, raise ChatSessionNotFoundException if not found"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()
    
    if not session:
        raise ChatSessionNotFoundException()
    return session


def create_chat_session(db: Session, title: str, user_id: int) -> ChatSession:
    """Create a new chat session for a user"""
    chat_session = ChatSession(
        title=title,
        user_id=user_id,
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def get_chat_sessions(db: Session, user_id: int) -> List[ChatSession]:
    """Retrieve all chat sessions for a user"""
    return db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).all()


def delete_chat_session(db: Session, session_id: int, user_id: int) -> None:
    """Delete a chat session and all its messages (cascade)"""
    session = get_chat_session_by_id(db, session_id, user_id)
    db.delete(session)
    db.commit()


def update_chat_session(db: Session, session_id: int, title: str, user_id: int) -> ChatSession:
    """Update a chat session's title"""
    session = get_chat_session_by_id(db, session_id, user_id)
    session.title = title
    db.commit()
    db.refresh(session)
    return session


async def stream_chat_message(db: Session, session_id: int, content: str, user_id: int):
    """
    Send a new message in a chat session. Saves the user's message,
    generates and saves an assistant response message.
    Return response by streaming event
    """
    # Verify chat session exists and belongs to the user
    get_chat_session_by_id(db, session_id, user_id)

    # Save user message
    message = ChatMessage(
        chat_session_id=session_id,
        role=MessageRole.USER,
        content=content,
    )
    
    # Get context from previous messages and current message
    recent_messages = get_recent_messages(db, session_id=session_id, limit=20)
    context = recent_messages + [message] 

    db.add(message)
    db.commit()
    db.refresh(message)

    # Init assistant message
    assistant_message = ChatMessage(
        chat_session_id=session_id,
        role=MessageRole.ASSISTANT,
        content="",
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    from app.pipeline_data.services import run_pipeline_service
    from app.pipeline_data.constants import SSEEventType, PipelineStep
    import datetime

    # Retrieve active Neo4j credentials for the user
    user = db.query(User).filter(User.id == user_id).first()
    current_connection = get_current_connection(user, db)
    
    if not current_connection:
        error_message = "No active Neo4j connection found. Please create a connection first."
        yield {
            "event": SSEEventType.ERROR,
            "data": json.dumps(PipelineErrorEventData(
                message_id=assistant_message.id,
                error=error_message,
                time=0
            ).model_dump())
        }
        return
        
    uri = current_connection.uri
    username = current_connection.username
    password = current_connection.password

    question_type = "LLM"
    steps_list = []
    generated_cypher = ""
    final_answer = ""
    error_message = None

    try:
        async for event in run_pipeline_service(
            uri, 
            username, 
            password, 
            format_context_for_pipeline(context), 
            assistant_message.id
        ):
            event_type = event.type
            
            if event_type == SSEEventType.CLASSIFY:
                question_type = event.data.question_type.value if hasattr(event.data.question_type, "value") else str(event.data.question_type)
                
            elif event_type == SSEEventType.STEP:
                step = event.data.step
                duration = event.data.time
                output = event.data.output
                
                if step == PipelineStep.CYPHER_GENERATION or step == PipelineStep.CYPHER_CORRECTION:
                    generated_cypher = output.get("cypher") or generated_cypher
                
                steps_list.append({
                    "name": step,
                    "duration": duration,
                    "output": output
                })
                
            elif event_type == SSEEventType.RESULT:
                final_answer = event.data.result
                assistant_message.content = final_answer
                
            elif event_type == SSEEventType.ERROR:
                error_message = event.data.error
            
            data_dict = event.data
            if hasattr(data_dict, "model_dump"):
                data_dict = data_dict.model_dump()
            elif hasattr(data_dict, "dict"):
                data_dict = data_dict.dict()
                
            yield {
                "event": event.type,
                "data": json.dumps(data_dict)
            }
        
        if question_type == "PIPELINE": 
            pipeline_run = PipelineRun(
                message_id=assistant_message.id,
                question=content,
                query="",
                status=PipelineRunStatus.COMPLETED,
                trace_data={},
            )
    
            pipeline_run.message_id = assistant_message.id
            pipeline_run.final_answer = final_answer
            pipeline_run.query = generated_cypher
            pipeline_run.trace_data = steps_list
            pipeline_run.finished_at = datetime.datetime.utcnow()
            
            if error_message:
                pipeline_run.status = PipelineRunStatus.FAILED
                pipeline_run.error_message = error_message
            else:
                pipeline_run.status = PipelineRunStatus.COMPLETED

            db.add(pipeline_run)
            db.commit()
            db.refresh(pipeline_run)
            
        db.add(assistant_message)
        db.commit()
        db.refresh(message)
        
    except Exception as e:
        yield {
            "event": SSEEventType.ERROR,
            "data": json.dumps(PipelineErrorEventData(
                message_id=assistant_message.id,
                error=str(e),
                time=0
            ).model_dump())
        }


def get_chat_messages(db: Session, session_id: int, user_id: int) -> List[ChatMessage]:
    """Get all messages in a chat session after verifying ownership"""
    get_chat_session_by_id(db, session_id, user_id)
    return db.query(ChatMessage).options(joinedload(ChatMessage.pipeline_run)).filter(
        ChatMessage.chat_session_id == session_id
    ).all()

def get_recent_messages(db: Session, session_id: int, limit: int = 10) -> List[ChatMessage]:
    """Get the latest messages in a chat session after verifying ownership"""
    return db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()



