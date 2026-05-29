from services.ner import get_llm_ner_service
from config import settings

def entity_extraction_node(state): 
    """Extract intermediate representation: entities, relationships, and labels from the question"""
    ner_service = get_llm_ner_service()
    ir = ner_service.extract(state["question"])

    entities = (ir or {}).get("entities") or []
    if settings.DEBUG:
        print("[DEBUG] Extracted entities:", entities)

    return {
        "entities": entities,
        "steps": ["entity_extraction"]
    }
