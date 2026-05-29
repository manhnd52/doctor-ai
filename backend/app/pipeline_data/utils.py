import os
import sys
import contextlib
import time
from typing import Any
from app.kg_connection.models import KgConnection
from app.auth.models import User
from neo4j import GraphDatabase, Session


class KGSessionManager:
    def __init__(self):
        self._cache = {}  # Cache to store active sessions keyed by connection ID

    def get_session(self, connection: KgConnection) -> Session:
        if not connection:
            raise Exception("No active KG connection found.")

        if connection.id in self._cache:
            return self._cache[connection.id]

        session = self._create_kg_session(connection)

        self._cache[connection.id] = session

        return session

    def validate_connection(self, connection: KgConnection) -> bool:
        try:
            session = self._create_kg_session(connection)
            print("Testing connection to KG...")
            session.run("RETURN 1")  # Test the connection
            session.close()
            return True
        except Exception as e:
            print(
                f"Connect info: {connection.uri}, {connection.database_name}, {connection.username}"
            )
            print(f"Failed to connect to KG: {str(e)}")
            return False

    def _create_kg_session(self, connection: KgConnection):
        driver = GraphDatabase.driver(
            connection.uri, auth=(connection.username, connection.password)
        )
        return driver.session(database=connection.database_name)

    def close_session(self, connection_id: int):
        session = self._cache.pop(connection_id, None)
        if session:
            session.close()


def serialize_value(val: Any) -> Any:
    """Recursively serializes nested values, handling Pydantic objects, dicts, and iterables."""
    if hasattr(val, "model_dump"):
        return serialize_value(val.model_dump())
    elif hasattr(val, "dict"):
        return serialize_value(val.dict())
    elif isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple, set)):
        return [serialize_value(v) for v in val]
    return val


@contextlib.contextmanager
def pipeline_context():
    """Context manager to run in the pipeline directory context, setting path and CWD."""
    original_cwd = os.getcwd()
    original_path = list(sys.path)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.abspath(os.path.join(current_dir, "../.."))

    # Load .env if it exists in backend root
    env_path = os.path.join(backend_root, ".env")
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            pass

    pipeline_path = os.getenv("PIPELINE_PATH")
    if not pipeline_path:
        pipeline_path = os.path.abspath(os.path.join(current_dir, "../../../pipeline"))
    else:
        if not os.path.isabs(pipeline_path):
            pipeline_path = os.path.abspath(os.path.join(backend_root, pipeline_path))

    os.chdir(pipeline_path)
    if pipeline_path not in sys.path:
        sys.path.insert(0, pipeline_path)

    try:
        yield
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


class PipelineProgressTracker:
    """Tracks elapsed times and state transitions during pipeline execution."""

    def __init__(self, message_id: int):
        self.message_id = message_id
        self.start_time = time.perf_counter_ns()
        self.node_start_times = {}
        self.initial_completed = set()

    def start_node(self, step_name: str) -> None:
        self.node_start_times[step_name] = time.perf_counter_ns()

    def start_node_and_event(self, step: Any) -> Any:
        from app.pipeline_data.constants import (
            SSEEventType,
            RunningEvent,
            RunningEventData,
        )

        self.start_node(step.value)
        return RunningEvent(
            type=SSEEventType.RUNNING,
            data=RunningEventData(message_id=self.message_id, running_step=step),
        )

    def get_duration_ms(self, step_name: str) -> int:
        start_ns = self.node_start_times.get(step_name, self.start_time)
        return int((time.perf_counter_ns() - start_ns) / 1_000_000)

    def get_total_time_ms(self) -> int:
        return int((time.perf_counter_ns() - self.start_time) / 1_000_000)

    def handle_transition(self, node_name: str, node_output: dict) -> list:
        from app.pipeline_data.constants import PipelineStep

        events = []

        if node_name == "question_classification":
            question_type = node_output.get("question_type")
            if question_type == "LLM":
                events.append(self.start_node_and_event(PipelineStep.ANSWER_GENERATION))
            else:
                events.append(self.start_node_and_event(PipelineStep.ENTITY_EXTRACTION))
                events.append(self.start_node_and_event(PipelineStep.TRIPLE_EXTRACTION))

        elif node_name in ("entity_extraction", "triple_extraction"):
            self.initial_completed.add(node_name)
            if len(self.initial_completed) == 2:
                events.append(
                    self.start_node_and_event(PipelineStep.TRIPLE_REMEDIATION)
                )

        elif node_name == "triple_remediation":
            events.append(self.start_node_and_event(PipelineStep.ENTITY_LINKING))

        elif node_name == "entity_linking":
            events.append(self.start_node_and_event(PipelineStep.CYPHER_GENERATION))

        elif node_name == "cypher_generation":
            events.append(self.start_node_and_event(PipelineStep.CYPHER_VALIDATION))

        elif node_name == "cypher_validation":
            next_action = node_output.get("next_action")
            errors = node_output.get("cypher_errors")

            if next_action == "cypher_correction" or errors:
                events.append(self.start_node_and_event(PipelineStep.CYPHER_CORRECTION))
            else:
                events.append(self.start_node_and_event(PipelineStep.QUERY_EXECUTION))

        elif node_name == "cypher_correction":
            events.append(self.start_node_and_event(PipelineStep.CYPHER_VALIDATION))

        elif node_name == "query_execution":
            events.append(self.start_node_and_event(PipelineStep.ANSWER_GENERATION))

        return events
