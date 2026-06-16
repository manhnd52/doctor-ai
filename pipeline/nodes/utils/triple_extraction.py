from services.ner import get_llm_ner_service
from typing import List, Dict, Any
from services.graph.utils import get_predicate_descriptions
from pydantic import BaseModel, Field
from services.llm_service import get_model
from langchain_core.prompts import ChatPromptTemplate
from config import settings

def tripple_extraction_node(state):
    """Extract tripples from the question"""
    triples = extract_triples(state.get("question", ""))
    if settings.DEBUG:
        print("[DEBUG] Extracted triples:", triples)
    return {
        "triples": triples,
        "metrics": {
            **state.get("metrics", {}),
            "relationship_count": len(triples)
        }
    }

def extract_triples(question: str) -> List[Dict[str, Any]]:
    predicate_descriptions = get_predicate_descriptions()
    
    # Format aliases from the same_as fields in predicate descriptions
    aliases = []
    for rel in predicate_descriptions:
        if "same_as" in rel:
            for syn in rel["same_as"]:
                aliases.append(f"- {syn} -> {rel['predicate']}")
    alias_str = "\n".join(aliases)

    model = get_model()
    structured_model = model.with_structured_output(TripleExtractionResult)
    chain = prompt | structured_model
    res = chain.invoke({
        "question": question,
        "predicate_descriptions": predicate_descriptions,
        "alias": alias_str
    })

    if isinstance(res, TripleExtractionResult):
        return [rel.model_dump() for rel in res.triples]

    if isinstance(res, dict):
        tripples = res.get("triples", [])
        if isinstance(tripples, list):
            return [
                rel.model_dump() if isinstance(rel, BaseModel) else rel
                for rel in tripples
                if isinstance(rel, (BaseModel, dict))
            ]

    return []

class Node(BaseModel):
    text: str = Field(
        description="The name of the entity. If is a specific entity, use its name; if is a variable, leave it as a placeholder like `?disease`"
    )
    label: str = Field(
        description="The type of the entity, corresponding to a node label in the graph."
    )

class Triple(BaseModel):
    subject: Node = Field(
        description="The source node that this relationship originates from."
    )
    predicate: str = Field(
        description="The specific relationship type connecting the subject and object."
    )
    object: Node = Field(
        description="The target node that this relationship points to."
    )


class TripleExtractionResult(BaseModel):
    triples: List[Triple] = Field(
        description="A list of extracted triples, each containing subject, predicate, and object."
    )

system_prompt = """
You are a triple extractor for a Neo4j graph.

Task: From a natural language question, extract valid relationships between entities using the given predicate schema.

Input:
- question: natural language question
- predicate_descriptions: list of valid relationships in the graph
- alias: aliases for relationships in the graph

Output:
- List of relationships with:
  - subject: source node with text and label
  - predicate: relationship type
  - object: target node with text and label

Rules:
- Only extract relationships that are stated in the question.
- Only use predicates from predicate_descriptions. You can match relationships using their aliases listed in the alias.
- Do not invent new relationships.
- Do NOT answer the question.
- If you don't recognize any relationship in the question, return empty list.

Example:
Input:
question: "What are the symptoms of diabetes?"
predicate_descriptions:
[
  {{"subject": "disease", "predicate": "has_symptom", "object": "symptom"}},
  {{"subject": "disease", "predicate": "treated_by", "object": "treatment"}},
  {{"subject": "treatment", "predicate": "treats", "object": "disease"}}
]

Output:
relationships:
[
  {{"subject": {{"text": "diabetes", "label": "disease"}}, "predicate": "has_symptom", "object": {{"text": "?", "label": "Symptom"}}}}
]

Example 2:
question: "Which relationships exist between diabetes and metformin?"
predicate_descriptions:
[
  {{"subject": "disease", "predicate": "has_symptom", "object": "symptom"}},
  {{"subject": "disease", "predicate": "treated_by", "object": "treatment"}},
  {{"subject": "treatment", "predicate": "treats", "object": "disease"}}
]
Output:
relationships:
[
  {{"subject": {{"text": "diabetes", "label": "disease"}}, "predicate": "?", "object": {{"text": "metformin", "label": "drug"}}}}
]

Predicate Descriptions:
<predicate_descriptions>
{predicate_descriptions}
</predicate_descriptions>

Alias:
<alias>
{alias}
</alias>
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}")
    ]
)

if __name__ == "__main__":
    question = "Which drugs to treat ocular hypertension may cause the loss of eyelashes?"
    print(extract_triples(question))

    question_2 = "Which drugs have pterygium as side effect?"
    print(extract_triples(question_2))


