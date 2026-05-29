from enum import Enum
from typing import Literal, Union, Dict, Any
from pydantic import BaseModel

class PipelineStep(str, Enum):
    TRIPLE_EXTRACTION = "triple_extraction"
    ENTITY_EXTRACTION = "entity_extraction"
    TRIPLE_REMEDIATION = "triple_remediation" 
    ENTITY_LINKING = "entity_linking"
    CYPHER_GENERATION = "cypher_generation"
    QUERY_EXECUTION = "query_execution"
    CYPHER_VALIDATION = "cypher_validation"
    CYPHER_CORRECTION = "cypher_correction"
    EVALUATION = "evaluation"
    ANSWER_GENERATION = "answer_generation"

class PipelineRunStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"

class SSEEventType(str, Enum):
    RUNNING = "RUNNING"
    CLASSIFY = "CLASSIFY"
    STEP = "STEP"
    RESULT = "RESULT"
    ERROR = "ERROR"

class QuestionType(str, Enum):
    PIPELINE = "PIPELINE"
    LLM = "LLM"

class BaseEvent(BaseModel):
    type: str
    data: Dict[str, Any]

class RunningEventData(BaseModel):
    message_id: int
    running_step: PipelineStep

class ClassifyEventData(BaseModel):
    message_id: int
    question_type: QuestionType
    
class PipelineStepEventData(BaseModel):
    message_id: int
    step: PipelineStep
    output: Dict[str, Any]
    time: int

class PipelineResultEventData(BaseModel):
    message_id: int
    result: str
    time: int

class PipelineErrorEventData(BaseModel):
    message_id: int
    error: str
    time: int

class RunningEvent(BaseEvent):
    type: Literal[SSEEventType.RUNNING]
    data: RunningEventData

class ClassifyEvent(BaseEvent):
    type: Literal[SSEEventType.CLASSIFY]
    data: ClassifyEventData

class PipelineStepEvent(BaseEvent):
    type: Literal[SSEEventType.STEP]
    data: PipelineStepEventData

class PipelineResultEvent(BaseEvent):
    type: Literal[SSEEventType.RESULT]
    data: PipelineResultEventData

class PipelineErrorEvent(BaseEvent):
    type: Literal[SSEEventType.ERROR]
    data: PipelineErrorEventData

SSEEvent = Union[
    RunningEvent,
    ClassifyEvent,
    PipelineStepEvent,
    PipelineResultEvent,
    PipelineErrorEvent,
]

STEP_DISPLAY_NAMES = {
    PipelineStep.ENTITY_EXTRACTION: "Entity Extraction",
    PipelineStep.TRIPLE_EXTRACTION: "Triple Extraction",
    PipelineStep.TRIPLE_REMEDIATION: "Triple Remediation",
    PipelineStep.ENTITY_LINKING: "Entity Linking",
    PipelineStep.CYPHER_GENERATION: "Cypher Generation",
    PipelineStep.CYPHER_VALIDATION: "Cypher Validation",
    PipelineStep.CYPHER_CORRECTION: "Cypher Correction",
    PipelineStep.QUERY_EXECUTION: "Neo4j Query Execution",
    PipelineStep.EVALUATION: "Evaluation",
    PipelineStep.ANSWER_GENERATION: "Answer Synthesis",
}