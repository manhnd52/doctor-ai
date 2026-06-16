from operator import add, or_
from typing import Literal, Optional, Tuple, TypedDict, List, Dict, Any, Set
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

def merge_entities(a, b):
    # deduplicate theo toàn bộ key
    seen = set()
    result = []
    for item in a + b:
        if not isinstance(item, dict): continue
        key = tuple(sorted(item.items())) 
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

class GraphState(TypedDict, total=False):
    next_action: str
    cypher_errors: List[str]
    steps: Annotated[List[str], add]    
    # input
    context: List[BaseMessage] # conversation history, should be provided in the input state for question classification and intent resolving nodes to work correctly
    question: str
    expected_nodes: Optional[List[Dict[str, Any]]] # Expected nodes for evaluation, should be provided in the input state for evaluation node to work correctly

    # classify
    question_type: Literal["PIPELINE", "LLM"]

    # step_01_extraction
    entities: Annotated[List[Dict], merge_entities]
    relationships: List[str]
    labels: List[str]
    triples: List[Dict]
    concepts: List[str]
    
    # step_02_entity_linking
    linked_entities: List[Dict]
    inference_relationships: List[str] # parent rel has child rel
    
    # step_03_cypher_generation
    cypher: str
    pruned_schema: str

    # step_04_query_execution
    query_result: Any
    cypher_gen_attempt: int

    # step_05_answer_generation
    answer: str

    # evaluation
    evaluation: Dict[str, Any]

    # Additional fields for evaluation
    errors: Annotated[List[Tuple[str, Any]], add]
    metrics: Dict[str, Any]
