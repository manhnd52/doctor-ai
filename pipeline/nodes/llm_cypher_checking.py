from services.llm_service import get_model
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from enum import Enum

def llm_cypher_checking_node(state):
    """Check if the generated Cypher query is valid and executable"""
    question = state.get("question", "")
    intent = state.get("intent", "")
    cypher = state.get("cypher", "")
   
    if not cypher:
        return {
            "is_valid": False,
            "error": "No Cypher query provided."
        }

    is_valid = validate_cypher(cypher, question, intent)
    
    return {
        "is_valid": is_valid,
        "error": None if is_valid else "The Cypher query is invalid or cannot be executed."
    }

class CypherError(str, Enum):
    LIMIT_UNNESSARY = "LIMIT_UNNESSARY"
    DIRTY_NULL = "DIRTY_NULL"
    OTHER = "OTHER"

ERROR_DESCRIPTIONS = {
    "LIMIT_UNNESSARY": "The question does not require a limit clause, but it is present in the query.",
    "DIRTY_NULL": "OPTIONAL MATCH without filtering NULL values; Returning fields from OPTIONAL MATCH that may be NULL; Missing WHERE ... IS NOT NULL when needed",
    "OTHER": "Any other common error that does not fall into the above categories."
}


def build_error_block():
    return "\n".join(
        f"- {k}: {v}" for k, v in ERROR_DESCRIPTIONS.items()
    ) 

class CypherErrorResult(BaseModel):
    errors: List[CypherError]
    explaination: Optional[str] = Field(
        None, description="Optional explanation for the identified errors."
    )

system_prompt = """
You are a Cypher query error analyzer.

Task:
Identify ALL applicable error types in the Cypher query.

Error Types:
{error_block}

Instructions:
- You may return MULTIPLE errors and explanations if applicable especially when OTHER is involved.
- Only choose from the predefined list
- Do NOT invent new errors
- If no error exists, return an empty list

Return:
{{
  "errors": [...],
  "explaination": "Optional explanation for the identified errors."
}}
"""

human_prompt = """
Question: {question}
Intent: {intent}
Cypher Query: {cypher}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", human_prompt)
])

def validate_cypher(cypher: str, question: str, intent: str) -> CypherErrorResult:
    model = get_model()
    structured_model = model.with_structured_output(CypherErrorResult)
    chain = prompt | structured_model
    res = chain.invoke({
        "error_block": build_error_block(),
        "cypher": cypher,
        "question": question,
        "intent": intent
    })
    if isinstance(res, CypherErrorResult):
        return res
    elif isinstance(res, dict):
        return CypherErrorResult(**res)
    else:
        return CypherErrorResult(
            errors=[CypherError.OTHER]
        )

if __name__ == "__main__":
    # Example usage
    state = {
        "question": "Which drugs are used to treat Alzheimer and what do they act on?",
        "intent": "lookup_triple",
        "cypher": "MATCH (dr:drug)-[:indication]->(dis:disease {index:28780}) OPTIONAL MATCH (dr)-[:target]->(t:gene_or_protein) RETURN dr.name AS drug, t.name AS acts_on ORDER BY drug, acts_on LIMIT 10"
    }
    result = validate_cypher(**state)
    print(result)



