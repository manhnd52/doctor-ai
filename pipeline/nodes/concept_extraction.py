import os
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from services.llm_service import get_model
from config import settings


class ConceptExtractionOutput(BaseModel):
    concepts: List[str] = Field(
        description="The exact text spans/phrases from the question that represent abstract query concepts, constraints, or logical conditions (e.g., 'novel targets', 'not pills', 'side effects', etc.)."
    )


def extract_concepts_llm(question: str) -> List[str]:
    """Uses LLM to identify and extract concept text spans from the question."""
    model = get_model()
    try:
        structured_model = model.with_structured_output(ConceptExtractionOutput)
    except Exception:
        structured_model = model
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a medical query concept extraction assistant.\n"
            "Extract noun phrases exactly as they appear in the user's question.\n\n"
            "Rules:\n"
            "- Extract meaningful noun phrases that represent medical concepts, biomedical concepts, query concepts, entity types, conditions, treatments, symptoms, targets, effects, or diseases.\n"
            "- Preserve the exact text span from the question.\n"
            "- Do not rewrite, normalize, or infer meanings.\n"
            "- Do not return verbs, question words, or complete sentences.\n"
            "- Return only phrases that explicitly appear in the question.\n"
            "- If no noun phrase exists, return an empty list."
        )),
        ("human", "Question: {question}")
    ])
    
    chain = prompt | structured_model
    try:
        response = chain.invoke({"question": question})
        if isinstance(response, ConceptExtractionOutput):
            return response.concepts
        elif isinstance(response, dict):
            return response.get("concepts", [])
    except Exception as e:
        if settings.DEBUG:
            print("[DEBUG] LLM Concept extraction failed:", e)
    return []


def concept_extraction_node(state):
    """Extract relevant query concepts from the question."""
    question = state.get("question", "")
    
    detected_list = extract_concepts_llm(question)
    
    if settings.DEBUG:
        print("[DEBUG] Extracted concepts:", detected_list)
        
    return {
        "concepts": detected_list,
        "steps": ["concept_extraction"]
    }
