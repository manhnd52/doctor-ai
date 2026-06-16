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
        if settings.DEBUG:
            print(f"[DEBUG] Attempt count {attemp} exceeded threshold {settings.ATTEMPT_THRESHOLD}. Proceeding straight to execution.")
        return {
            "cypher": state.get("cypher", ""),
            "steps": ["cypher_generation"]
        }
    
    entities = state.get("linked_entities") or []
    triples = state.get("triples") or []
    concepts = state.get("concepts") or []

    keywords = set()
    for entity in entities:
        if isinstance(entity, dict):
            keywords.add(entity.get("label", ""))
    for triple in triples:
        if isinstance(triple, dict):
            subject = triple.get("subject")
            obj = triple.get("object")
            if isinstance(subject, dict):
                keywords.add(subject.get("label", ""))
            if isinstance(obj, dict):
                keywords.add(obj.get("label", ""))
            keywords.add(triple.get("predicate", ""))
    for concept in concepts:
        if isinstance(concept, str):
            keywords.add(concept)

    if settings.DEBUG:
        print("[DEBUG] Keywords: ", keywords)

    pruned_schema = get_prune_schema_by_keywords(keywords)

    inference_relationships = state.get("inference_relationships", [])
    inference_hint = ""
    if inference_relationships:
        inference_hint = f"""
  ### [CRITICAL ALERT] Neosemantics (n10s) Inference Required:
  The relationship(s) {inference_relationships} are parent properties in the ontology and do NOT exist directly in the database.
  You MUST use `n10s.inference.getRels` to query them.
  
  Syntax rules for using n10s.inference.getRels:
  - For OUTGOING relationship from node `n` to node `m` via relationship type `R` (e.g., `(n)-[:R]->(m)`):
    MATCH (n {{index: <index_value>}})
    CALL n10s.inference.getRels(n, 'R', {{relDirection: 'OUTGOING'}}) YIELD rel, node
    MATCH (m:<Label>) WHERE m = node
    RETURN DISTINCT m.name
  - For INCOMING relationship from node `m` to node `n` via relationship type `R` (e.g., `(n)<-[:R]-(m)`):
    MATCH (n {{index: <index_value>}})
    CALL n10s.inference.getRels(n, 'R', {{relDirection: 'INCOMING'}}) YIELD rel, node
    MATCH (m:<Label>) WHERE m = node
    RETURN DISTINCT m.name
  - For UNDIRECTED or BOTH directions:
    MATCH (n {{index: <index_value>}})
    CALL n10s.inference.getRels(n, 'R', {{relDirection: 'BOTH'}}) YIELD rel, node
    MATCH (m:<Label>) WHERE m = node
    RETURN DISTINCT m.name

  Example: "Which drugs are associated with diabetes?"
  - Input Entities: `[[{{"text": "diabetes", "label": "disease", "index": 123}}]]`
  - Extracted Triple: `[[{{"subject": {{"text": "diabetes", "label": "disease"}}, "predicate": "associated_with", "object": {{"text": "?", "label": "drug"}}}}]]`
  - Since `associated_with` is a parent relationship in the ontology (not directly stored in the graph for drug-disease), use n10s:
    MATCH (d {{index: 123}})
    CALL n10s.inference.getRels(d, 'associated_with', {{relDirection: 'INCOMING'}}) YIELD rel, node
    MATCH (t:drug) WHERE t = node
    RETURN t.name
"""

    res = generate_cypher(
        question=state.get("question", ""),
        entities=entities,
        triples=triples,
        pruned_schema=pruned_schema,
        inference_hint=inference_hint
    )

    if settings.DEBUG:
        print("[DEBUG] Generated Cypher:", res.get("cypher", ""))

    return {
        "cypher": clean_cypher(res.get("cypher", "")), 
        "pruned_schema": pruned_schema,
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

  # Database Context

  <database_schema>
  {schema}
  </database_schema>

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

  2. Answer Type Mapping
  Yes/No question  
  → return a boolean named `value`
  Aggregation (COUNT, SUM, AVG, MIN, MAX)  
  → return a single value named `value`
  Property retrieval  
  → return the requested properties
  A list of nodes, edges, or properties retrival → DON'T use collect()
  
  3. When a question compares counts of relationships   
      (e.g. more, fewer, most, least, higher than, lower than),
      assume absent relationships contribute a count of zero unless 
      the question explicitly requires the relationship to exist.

      Therefore prefer OPTIONAL MATCH over MATCH for counted relationships.
      
  # Output Format
  Return a structured object with EXACTLY these fields:
  - cypher: string

  {inference_hint}
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_triple),
        ("human", "Question: {question}\n")
    ]
)

class OutputSchema(BaseModel):
    cypher: str


def generate_cypher(question, 
                    entities,
                    triples = [],
                    pruned_schema = {},
                    inference_hint = ""):

    model = get_model()
    model = model.with_structured_output(OutputSchema)
    chain = prompt | model
    

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
        "entities": entities,
        "triples": triples,
        "inference_hint": inference_hint,
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

