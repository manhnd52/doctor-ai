from services.llm_service import get_model
from pipeline_state import GraphState
from pydantic import BaseModel, Field
from typing import Literal
from config import settings

class ClassifyResult(BaseModel): 
    type: Literal["PIPELINE", "LLM"]

def classify_question_node(state : GraphState):
    question = state.get("question", "")

    model = get_model()
    model = model.with_structured_output(ClassifyResult)

    classification_prompt = (
        "Classify the following user question into either 'PIPELINE' or 'LLM'.\n"
        "Use 'PIPELINE' if user intent is looking up or require information about medical entities, relationships, diseases, treatments, "
        "or querying a database/graph. "
        "Use 'LLM' if it is a general greeting, conversational chit-chat, or a generic question.\n"
        "Respond with exactly one word: 'PIPELINE' or 'LLM'.\n\n"
        f"Question: {question}\n"
        "Classification:"
    )

    try:
        response = model.invoke(classification_prompt)
        response = ClassifyResult.model_validate(response)
        question_type = response.type
    except Exception as e:
        if settings.DEBUG:
            print(f"[DEBUG] Classification failed: {e}, defaulting to LLM")
        question_type = "LLM"

    return {
        "question_type": question_type
    }

