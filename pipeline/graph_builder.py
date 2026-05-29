from langgraph.graph import END, START, StateGraph
from nodes.condition import validate_cypher_condition
from services.ner.llm_ner_service import LlmNerService
from pipeline_state import GraphState
from config import Settings, settings
from typing import List, Dict, Any, Tuple
from nodes import *

def build_nlp_subgraph(evaluate=False):
    builder = StateGraph(GraphState)

    builder.add_node("triple_extraction", tripple_extraction_node)
    builder.add_node("entity_extraction", entity_extraction_node)
    builder.add_node("triple_remediation", triple_remediation_node)
    builder.add_node("entity_linking", entity_linking_node)
    builder.add_node("cypher_generation", cypher_generation_node)
    builder.add_node("cypher_validation", cypher_validation_node)
    builder.add_node("cypher_correction", cypher_correction_node)
    builder.add_node("query_execution", query_execution_node)
    builder.add_node("evaluation", evaluation_node)
    # entry
    builder.add_edge(START, "triple_extraction")
    builder.add_edge(START, "entity_extraction")

    builder.add_edge("triple_extraction", "triple_remediation")
    builder.add_edge("entity_extraction", "triple_remediation")

    builder.add_edge("triple_remediation", "entity_linking")
    builder.add_edge("entity_linking", "cypher_generation")
    builder.add_edge("cypher_generation", "cypher_validation")

    builder.add_edge("cypher_correction", "cypher_validation")

    builder.add_conditional_edges(
        "cypher_validation",
        validate_cypher_condition,
        {
            "query_execution": "query_execution",
            "cypher_correction": "cypher_correction",
            "end": END
        }
    )

    if evaluate:
        builder.add_edge("query_execution", "evaluation")
        builder.add_edge("evaluation", END)
    else:
        builder.add_edge("query_execution", END)

    return builder.compile()

def build_graph(evaluate=False):
    builder = StateGraph(GraphState)

    # nodes
    builder.add_node("intent_resolving", intent_resolving_node)
    builder.add_node("question_classification", classify_question_node)
    builder.add_node("answer_generation", answer_generation_node)

    # subgraph node
    nlp_subgraph = build_nlp_subgraph(evaluate=evaluate)
    builder.add_node("nlp_pipeline", nlp_subgraph)

    # flow
    builder.add_edge(START, "intent_resolving")
    builder.add_edge("intent_resolving", "question_classification")

    def route(state):
        return "LLM" if state.get("question_type") == "LLM" else "PIPELINE"

    builder.add_conditional_edges(
        "question_classification",
        route,
        {
            "LLM": "answer_generation",
            "PIPELINE": "nlp_pipeline"
        }
    )

    builder.add_edge("nlp_pipeline", "answer_generation")
    builder.add_edge("answer_generation", END)

    return builder.compile()