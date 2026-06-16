from langchain_core.prompts import ChatPromptTemplate
from nodes.cypher_generation import clean_cypher
from services.graph.utils import get_formatted_schema, get_graph, get_schema
from services.llm_service import get_model
from langchain_core.output_parsers import StrOutputParser
from config import settings

def cypher_correction_node(state):    
    """
    Correct the Cypher statement based on the provided errors.
    """
    if settings.DEBUG:
        print("[DEBUG] Correcting Cypher query...")
        print("[DEBUG] Current Cypher:", state.get("cypher", ""))

    corrected_cypher = correct_cypher_chain.invoke(
        {
            "question": state.get("question"),
            "errors": state.get("cypher_errors"),
            "cypher": state.get("cypher"),
            "schema": get_formatted_schema(),
        }
    )

    corrected_cypher = clean_cypher(corrected_cypher)
    
    if settings.DEBUG: print("[DEBUG] Corrected Cypher:", corrected_cypher)

    return {
        "cypher_gen_attempt": state.get("cypher_gen_attempt", 0) + 1,
        "next_action": "validate_cypher",
        "cypher": corrected_cypher,
        "steps": ["cypher_correction"],
    }

correct_cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a Cypher expert reviewing a statement written by a junior developer. "
                "You need to correct the Cypher statement based on the provided errors. No pre-amble."
                "Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"
                "Do not add line breaks, tabs, or similar formatting characters."
            ),
        ),
        (
            "human",
            (
                """Check for invalid syntax or semantics and return a corrected Cypher statement.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not wrap the response in any backticks or anything else.
Respond with a Cypher statement only!

Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.

Note on Neosemantics (n10s) Inference Queries:
If the Cypher statement uses Neosemantics inference (via `CALL n10s.inference.getRels(...) YIELD rel, node`), it is the correct way to query hierarchical relationships (e.g. `associated_with`). Keep this structure, do not rewrite it to use standard relationship syntax, and do not treat `n10s.inference.getRels` or its arguments as errors.

The question is:
{question}

The Cypher statement is:
{cypher}

The errors are:
{errors}

Corrected Cypher statement: """
            ),
        ),
    ]
)
llm = get_model()
correct_cypher_chain = correct_cypher_prompt | llm | StrOutputParser()

if __name__ == "__main__":
    state = {
        "question": "What are the symptoms of diabetes?",
        "cypher": "MATCH (d:Disease {name: 'diabetes'})-[:has_symptom]->(s:Symptom RETURN s LIMIT 5",
        "cypher_errors": ["Syntax error: missing closing parenthesis", "The question doesn't require a limit of 5 results, so the LIMIT clause is unnecessary and can be removed."],
    }
    result = cypher_correction_node(state)
    print(result)