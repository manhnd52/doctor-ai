from services.graph.utils import get_predicate_descriptions
from services.llm_service import get_model
from services.graph import get_formatted_schema
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from pipeline_state import GraphState
from config import settings
import re
from services.graph.schema_pruning import get_prune_schema_by_keywords

def cypher_generation_node(state : GraphState):
    if settings.DEBUG:
        print("[DEBUG] Generating Cypher query...")
    attemp = state.get("cypher_gen_attempt", 0)

    if (attemp > settings.ATTEMPT_THRESHOLD):
        return {
            "errors": [("Cypher Generation", f"Failed to generate valid Cypher after {attemp} attempts.")],
        }
    
    res = generate_cypher(
        question=state.get("question", ""),
        entities=state.get("linked_entities", []),
        triples=state.get("triples", []),
        concepts=state.get("concepts", [])
    )

    if settings.DEBUG:
        print("[DEBUG] Generated Cypher:", res.get("cypher", ""))

    return {
        "cypher": clean_cypher(res.get("cypher", "")), 
        "cypher_gen_attempt": attemp + 1,
        "metrics": {
            **state.get("metrics", {}),
            "cypher_explanation": res.get("explanation", "")
        },
        "steps": ["cypher_generation"]
    }

system_prompt_triple =  """
  You are a Cypher Query Generator for Neo4j.

  Your task is to convert a natural language question into a Cypher query
  using ONLY the provided database schema and the grounded graph context.

  You must strictly follow the schema and the resolved graph elements.
  You are NOT allowed to invent or assume:

  - node labels
  - relationship types
  - properties
  - nodes
  - graph structure

  If something is not explicitly present in the schema or provided inputs,
  DO NOT use it.

  # Objective

  Given:
  - a natural language question
  - the database schema
  - resolved graph entities
  - candidate labels
  - candidate relationships

  Generate ONE valid Cypher query that best answers the question.

  # Database Context

  <database_schema>
  {schema}
  </database_schema>

  <predicate_descriptions>
  {predicate_descriptions}
  </predicate_descriptions>

  <resolved_entities>
  These are REAL nodes already matched in the graph.
  Each entity includes its node `index`.
  {entities}
  </resolved_entities>

  <extracted_triples>
  These are relationships extracted from the question.
  {triples}
  </extracted_triples>

  # Query Construction Rules

  1. Entity Grounding (Highest Priority)
  If an entity contains an `index`, ALWAYS match it using the index property:
  MATCH (n {{index: <index_value>}})
  Do NOT match that entity by name or other properties.
  These entities represent already resolved graph nodes and should be treated
  as reliable anchors in the query.

  2. Intent-Driven Query Construction
  First determine the core intent of the question.
  Examples:
  - retrieving properties
  - finding related nodes
  - counting nodes
  - verifying existence
  - listing results
  Use only the entities and schema elements necessary to answer the question.
  Do NOT force all entities into the query.

  3. Label Usage
  Use ONLY labels that exist in the schema.
  If a label contains spaces, wrap it in backticks (`).

  4. Relationship Usage
  Use ONLY relationship types defined in the schema.
  Never invent relationships.

  5. Query Simplicity
  The query must be minimal and readable.
  Avoid:
  - unnecessary MATCH
  - unnecessary OPTIONAL MATCH
  - deep nesting
  - redundant patterns

  6. Answer Type Mapping
  Yes/No question  
  → return a boolean named `value`
  Aggregation (COUNT, SUM, AVG, MIN, MAX)  
  → return a single value named `value`
  Property retrieval  
  → return the requested properties
  List question  
  → return multiple rows (do NOT collect)

  7. Ambiguity Handling
  If the question is ambiguous:
  Generate a query that retrieves the most relevant
  information based strictly on:
  - grounded entities
  - schema structure
  - candidate labels
  - candidate relationships
  Never guess missing schema elements.

  8. Schema Safety
  The generated query MUST be valid Cypher.
  Only use:
  - labels defined in the schema
  - relationships defined in the schema
  - properties defined in the schema

  # Output Format
  Return a structured object with EXACTLY these fields:
  - cypher: string
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_triple),
        ("human", "{question}")
    ]
)

class OutputSchema(BaseModel):
    cypher: str


def generate_cypher(question, 
                    entities,
                    triples = [],
                    concepts = []):

    model = get_model()
    model = model.with_structured_output(OutputSchema)
    chain = prompt | model
    
    keywords = set()
    for entity in entities:
        keywords.add(entity.get("label", ""))
    for triple in triples:
        keywords.add(triple.get("subject", "").get("label", ""))
        keywords.add(triple.get("object", "").get("label", ""))
        keywords.add(triple.get("predicate", ""))
    for concept in concepts:
        keywords.add(concept)

    if settings.DEBUG:
        print("[DEBUG] Keywords: ", keywords)

    pruned_schema = get_prune_schema_by_keywords(keywords)

    if settings.DEBUG:
        import sys
        try:
            print("[DEBUG] Pruned schema: ", pruned_schema)
        except UnicodeEncodeError:
            safe_schema = pruned_schema.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            print("[DEBUG] Pruned schema (safe): ", safe_schema)
    response = chain.invoke({
        "question": question,
        "schema": pruned_schema,
        "predicate_descriptions": get_predicate_descriptions(),
        "entities": entities,
        "triples": triples,
    })
    if isinstance(response, OutputSchema):
        return response.model_dump()
    else:
        return {
            "cypher": ""
      }
    
def clean_cypher(cypher: str) -> str:    # Remove "\n" and extra spaces
    cypher = cypher.replace("\n", " ")
    cypher = cypher.replace("\\n", " ")
    cypher = re.sub(r"\s+", " ", cypher)

    return cypher.strip()


if __name__ == "__main__":
    question = "What are the symptoms of diabetes?"
    entities = [
        {"text": "diabetes", "type": "Node", "label": "Disease", "index": 123}
    ]
    print(generate_cypher(question, entities))

