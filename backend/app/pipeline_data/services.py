
from sqlalchemy.orm import Session
from app.pipeline_data.models import PipelineRun
from app.pipeline_data.constants import *
from typing import Optional, AsyncGenerator, Dict, Any, List
from app.auth.models import User
from sqlalchemy import select, join, and_
from app.chat.models import ChatMessage, ChatSession
import asyncio
import json
import os
import sys
import time
import contextlib
from app.pipeline_data.utils import serialize_value, pipeline_context, PipelineProgressTracker

with pipeline_context():
    from facade import PipelineFacade, Message as PipelineMessage

def create_pipeline_run(
	db: Session,
	message_id: int,
	question: str,
	query: str,
	status: PipelineRunStatus,
	final_answer: Optional[str] = None,
	trace_data: Optional[dict] = None,
	error_message: Optional[str] = None,
) -> PipelineRun:
	"""Create and persist a new PipelineRun.

	Raises an Exception if a PipelineRun already exists for the given message_id.
	"""
	existing = db.query(PipelineRun).filter(PipelineRun.message_id == message_id).first()
	if existing:
		raise Exception("PipelineRun already exists for message_id=%s" % message_id)

	new_run = PipelineRun(
		message_id=message_id,
		question=question,
		query=query,
		final_answer=final_answer,
		status=status,
		trace_data=trace_data,
		error_message=error_message,
	)

	db.add(new_run)
	db.commit()
	db.refresh(new_run)
	return new_run


def get_pipeline_run_by_id(
    db: Session,
    user: User,
    run_id: int
) -> Optional[PipelineRun]:
    """Retrieve a PipelineRun by its ID, ensuring it belongs to the given user."""
    stmt = (
        select(PipelineRun)
        .join(ChatMessage, PipelineRun.message_id == ChatMessage.id)
        .join(ChatSession, ChatMessage.chat_session_id == ChatSession.id)
        .where(
            PipelineRun.id == run_id,
            ChatSession.user_id == user.id
        )
    )

    return db.scalar(stmt)

_facade_cache = dict()

def get_pipeline_facade(
    uri: str,
    username: str,
    password: str,
):
    """Initializes and returns the PipelineFacade from the pipeline package."""
    key = f"{uri}-{username}-{password}"
    if key in _facade_cache:
        return _facade_cache[key]

    with pipeline_context():
        from dotenv import load_dotenv
        load_dotenv(".env")
        _facade_cache[key] = PipelineFacade(uri, username, password, evaluate=False)
        return _facade_cache[key]

async def run_pipeline_service(
    uri: str,
    username: str,
    password: str,
    context: List[PipelineMessage],
    message_id: int
) -> AsyncGenerator[SSEEvent, None]:
    """Runs the LangGraph medical question answering pipeline and yields progress events.
    
    Yields events according to the schemas in constants.py:
      - ClassifyEvent at the beginning of the execution.
      - RunningEvent when a step begins processing.
      - PipelineStepEvent when a step finishes processing.
      - PipelineResultEvent with final answer if execution succeeds.
      - PipelineErrorEvent if an error occurs.
    """
    tracker = PipelineProgressTracker(message_id)
    
    # Retrieve compiled graph
    try:
        facade = get_pipeline_facade(uri, username, password)
    except Exception as e:
        yield PipelineErrorEvent(
            type=SSEEventType.ERROR,
            data=PipelineErrorEventData(
                message_id=message_id,
                error=f"Failed to initialize pipeline: {str(e)}",
                time=tracker.get_total_time_ms()
            )
        )
        return

    final_answer = None
    
    try:
        # Run graph execution in pipeline directory context to resolve internal cache paths
        with pipeline_context():
            # Load .env inside pipeline directory for runtime keys
            from dotenv import load_dotenv
            load_dotenv(".env")
            
            async for chunk in facade.astream_by_node(context):
                # node_type = chunk['type']
                # ns = chunk['ns']
                data = chunk['data']  

                node_name = list(data.keys())[0]
                node_output = data[node_name]

                print(f"[DEBUG] Node name: {node_name}, Node output: {node_output}")
                if node_name == "question_classification":
                    question_type = node_output.get("question_type", "PIPELINE")
                    yield ClassifyEvent(
                        type=SSEEventType.CLASSIFY,
                        data=ClassifyEventData(
                            message_id=message_id,
                            question_type=QuestionType(question_type)
                        )
                    )
                    # Transition to next step(s) based on classification
                    for transition_event in tracker.handle_transition(node_name, node_output):
                        yield transition_event
                    continue
                
                try:
                    step_enum = PipelineStep(node_name)
                except ValueError:
                    # Skip internal/dummy nodes like pipeline_branch
                    continue
                
                yield PipelineStepEvent(
                    type=SSEEventType.STEP,
                    data=PipelineStepEventData(
                        message_id=message_id,
                        step=step_enum,
                        output=serialize_value(node_output),
                        time=tracker.get_duration_ms(node_name)
                    )
                )
                
                # Transition to next step(s) running notifications
                for transition_event in tracker.handle_transition(node_name, node_output):
                    yield transition_event
                    
                if node_name == PipelineStep.ANSWER_GENERATION.value:
                    final_answer = node_output.get("answer")

        # Yield successful result event
        yield PipelineResultEvent(
            type=SSEEventType.RESULT,
            data=PipelineResultEventData(
                message_id=message_id,
                result=final_answer or "No answer generated.",
                time=tracker.get_total_time_ms()
            )
        )

    except Exception as e:
        import traceback
        err_str = f"Pipeline execution failed: {str(e)}\n{traceback.format_exc()}"
        print(err_str)
        yield PipelineErrorEvent(
            type=SSEEventType.ERROR,
            data=PipelineErrorEventData(
                message_id=message_id,
                error=f"Pipeline execution failed: {str(e)}",
                time=tracker.get_total_time_ms()
            )
        )

def format_context_for_pipeline(messages: List[ChatMessage]) -> List[PipelineMessage]:
    """Mapper db model `ChatMessage`to facade supported data type.
    Args:
        messages (List[ChatMessage]): List of chat messages from database.
    Returns:
        List[PipelineMessage]: List of chat messages in facade supported data type.
    """
    pipeline_messages = []
    for msg in messages:
        content = msg.content
        pipeline_messages.append(PipelineMessage(role=msg.role.value, content=content))

    return pipeline_messages