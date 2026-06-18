from services.graph import get_formatted_schema
from services.llm_service import get_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from pipeline_state import GraphState
from config import settings
import re

class OutputSchema(BaseModel):
    cypher: str

system_prompt_baseline = """
You are a Cypher Query Generator for Neo4j.

Your task is to convert a natural language question into a Cypher query
using ONLY the provided database schema.

You must strictly follow the schema.
You are NOT allowed to invent or assume:
- node labels
- relationship types
- properties
- graph structure

Node name must be lowercase.

If something is not explicitly present in the schema, DO NOT use it.

# Database Context

<database_schema>
{schema}
</database_schema>

# Output Format
Return a structured object with EXACTLY these fields:
- cypher: string
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_baseline),
        ("human", "Question: {question}\n")
    ]
)

def baseline_cypher_generation_node(state: GraphState):
    if settings.DEBUG:
        print("[DEBUG] Generating Cypher query (Baseline)...")
        
    question = state.get("question", "")
    
    # Retrieve raw uncompiled schema
    raw_schema = get_formatted_schema()
    
    model = get_model()
    structured_model = model.with_structured_output(OutputSchema)
    chain = prompt | structured_model
    
    response = chain.invoke({
        "question": question,
        "schema": raw_schema
    })
    
    cypher_query = ""
    if isinstance(response, OutputSchema):
        cypher_query = response.cypher
    elif isinstance(response, dict):
        cypher_query = response.get("cypher", "")
        
    cypher_query = clean_cypher(cypher_query)
    
    if settings.DEBUG:
        print("[DEBUG] Generated Baseline Cypher:", cypher_query)
        
    return {
        "cypher": cypher_query,
        "steps": ["baseline_cypher_generation"]
    }

def clean_cypher(cypher: str) -> str:
    cypher = cypher.replace("\n", " ")
    cypher = cypher.replace("\\n", " ")
    cypher = re.sub(r"\s+", " ", cypher)
    return cypher.strip()
