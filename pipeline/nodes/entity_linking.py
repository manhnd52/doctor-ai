from services.graph import search_entity
from config import settings

def entity_linking_node(state):
    linked_entities = []
    entities = state.get("entities", [])

    def _find_match(searched, label):
        for result in searched:
            if result["label"] == label:
                return {
                    "index": result["index"],
                    "name": result["name"],
                    "label": result["label"],
                    "score": result["score"],
                }
        return None

    for e in entities:
        entity_text = e.get("text")
        label = e.get("label")

        # First attempt
        searched = search_entity(entity_text, top_k=3, threshold=1.0)
        linked_entity = _find_match(searched, label)

        # Fallback: Remove extra spaces and lowercase then search again
        if not linked_entity:
            print(f"[DEBUG] No match found for '{entity_text}' with label '{label}'. Retrying with cleaned text...")
            searched = search_entity(entity_text.replace(" ", "").lower(), top_k=3, threshold=1.0)
            if searched:
                linked_entity = _find_match(searched, label)

        # Append result
        if linked_entity:
            if settings.DEBUG:
                print(f"[DEBUG] Linked entity for '{entity_text}':", linked_entity)
            linked_entities.append(linked_entity)

    return {
        "linked_entities": linked_entities,
        "metrics": {
            **state.get("metrics", {}),
            "linked_entity_count": len(linked_entities)
        },
        "steps": ["entity_linking"]
    }

