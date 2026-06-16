from typing import Optional, List
from pydantic import BaseModel, Field
from services.graph.utils import get_formatted_schema, validate_cypher, get_schema, get_graph
from services.llm_service import get_model
from langchain_core.prompts import ChatPromptTemplate
from config import settings

def cypher_validation_node(state):
    if settings.DEBUG: print("[DEBUG] Validating Cypher query...")
    query = state.get("cypher", "")
    errors = []
    mapping_errors = []
    
    is_referencing = "n10s" in query
    
    if not is_referencing:
        is_valid, metadata_list = validate_cypher(query)
    else:
        is_valid, metadata_list = True, []

    if metadata_list:
        for item in metadata_list:
            code = item.get("code", "N/A") if isinstance(item, dict) else "N/A"
            description = item.get("description", "") if isinstance(item, dict) else str(item)
            errors.append(f"code={code}; description={description}")
    
    llm_output = validate_cypher_chain.invoke(
        {   
            "question": state.get("question"),
            "schema": state.get("pruned_schema", ""),
            "cypher": state.get("cypher"),
            "entities": state.get("entities", []),
            "triples": state.get("triples", [])
        }
    ) 

    llm_output = ValidateCypherOutput.model_validate(llm_output)

    if llm_output.errors:
        errors.extend([f"code=llm-gen; description={e}" for e in llm_output.errors])

    if errors:
        if settings.DEBUG:
            print("[DEBUG] Validation errors found:", errors)
        attemp = state.get("cypher_gen_attempt", 0)
        if attemp >= settings.ATTEMPT_THRESHOLD:
            if settings.DEBUG:
                print(f"[DEBUG] Attempt count {attemp} reached/exceeded threshold {settings.ATTEMPT_THRESHOLD}. Proceeding straight to execution with errors.")
            next_action = "query_execution"
        else:
            next_action = "cypher_correction"
    else:
        next_action = "query_execution"

    return {
        "next_action": next_action,
        "cypher_errors": errors,
        "steps": ["validate_cypher"],
        "metric": {
            **state.get("metric", {}),
            "validation_errors": errors,
            "mapping_errors": mapping_errors
        }
    }

validate_cypher_system = """
You are a Cypher expert reviewing a statement written by a junior developer.
"""

validate_cypher_user = """You must check the following:
* Are there any syntax errors in the Cypher or n10s statement?
* Are there any missing or undefined variables in the Cypher statement?
* Are any node labels missing from the schema?
* Are any relationship types missing from the schema?
* Are any of the properties not included in the schema?
* Does the Cypher statement include enough information to answer the question?
* Does the Cypher do more than what is asked in the question, such as including extra nodes, relationships, or properties, or limiting that are not necessary to answer the question?

Notice:
* You DON'T NEED TO CHECK THE DIRECTION of the relationships because it is checked before then the current Cypher's direction is valid.
* Note on Neosemantics (n10s) Inference Queries: Queries using Neosemantics inference (via `CALL n10s.inference.getRels(startNode, 'rel_type', {{relDirection: ...}}) YIELD rel, node`) are completely valid and expected for hierarchical/ontology relationships (like `associated_with`). DO NOT flag the procedure call `n10s.inference.getRels` or its arguments as errors or missing from the schema.
* If the query have index, and that index matching with the entity, the cypher IS OKE. PLEASE IGNORE.
Example: 
ENTITIES: 
[{{"text": "tricuspid valve atresia", "label": "", "index": 30396}}]
CYPHER: MATCH (n {{index: 30396}})-[:associated_with]->() RETURN n.name
VALIDATE RESULT: [] // OK
* IF the query have index but don't have label, it's OKAY.
* Don't feedback about RETURN type, property type, or data format in the result, it will be handled in the execution step.

Examples of good errors:
* Label (:Foo) does not exist, did you mean (:Bar)?
* Property bar does not exist for label Foo, did you mean baz?
* Relationship FOO does not exist, did you mean FOO_BAR?
* The question does not ask for limiting the results, but the Cypher statement includes a LIMIT clause.

Schema:
{schema}

The question is:
{question}

The Cypher statement is:
{cypher}

Extracted Entities (the entities that are extracted from the question and their index used in the Cypher statement) is:
{entities}
"""

validate_cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            validate_cypher_system,
        ),
        (
            "human",
            (validate_cypher_user),
        ),
    ]
)

class Property(BaseModel):
    """
    Represents a filter condition based on a specific node property in a graph in a Cypher statement.
    """

    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )
    property_key: str = Field(description="The key of the property being filtered.")
    property_value: str = Field(
        description="The value that the property is being matched against."
    )

class ValidateCypherOutput(BaseModel):
    """
    Represents the validation result of a Cypher query's output,
    including any errors and applied filters.
    """

    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )
    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    )

llm = get_model()
validate_cypher_chain = validate_cypher_prompt | llm.with_structured_output(
    ValidateCypherOutput
)

if __name__ == "__main__":
    question = "What are the symptoms of diabetes?"
    cypher = "MATCH (d:Disease)-[:has_symptom]->(s:Symptom) WHERE d.name = 'diabetes' RETURN s LIMIT 5"
    schema = {
        "labels": ["Disease", "Symptom"],
        "relationships": ["has_symptom"],
        "properties": {
            "Disease": ["name"],
            "Symptom": ["name"]
        }
    }
    response = validate_cypher_chain.invoke({
        "question": question,
        "cypher": cypher,
        "schema": schema
    })
    print(response)