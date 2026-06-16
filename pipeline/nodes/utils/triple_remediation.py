from services.graph.utils import get_schema, remediate_triple, remidiate_label, is_parent_relationship
from config import settings

def triple_remediation_node(state):
    """
    This function is responsible for remediating the extracted triples and entities to ensure they are in a consistent format for the next step of cypher generation. It takes the current state of the conversation, extracts the relevant information, and returns a dictionary containing the remediated triples and any associated metrics.
    """
    fixed_label = []
    triples = state.get("triples", [])
    if not isinstance(triples, list):
        triples = []
        
    cleaned_triples = []
    for triple in triples:
        if not isinstance(triple, dict):
            continue
        # Ensure subject and object are dictionaries
        subject = triple.get("subject")
        if not isinstance(subject, dict):
            subject = {"text": "", "label": ""}
        obj = triple.get("object")
        if not isinstance(obj, dict):
            obj = {"text": "", "label": ""}
        
        triple["subject"] = subject
        triple["object"] = obj
        cleaned_triples.append(triple)
    triples = cleaned_triples

    # Cypher
    # Remidiate label for each node in the triples, and log any changes for debugging purposes
    for triple in triples:
        original_domain = triple.get("subject", {}).get("label", "")
        original_range = triple.get("object", {}).get("label", "")
        original_predicate = triple.get("predicate", "")
        original_domain_text = triple.get("subject", {}).get("text", "")
        original_range_text = triple.get("object", {}).get("text", "")

        remediated_domain = remidiate_label(original_domain, "node")
        remediated_range = remidiate_label(original_range, "node")
        remediated_predicate = remidiate_label(original_predicate, "relationship")
        remediated_domain_text = original_domain_text.lower() if original_domain_text else ""
        remediated_range_text = original_range_text.lower() if original_range_text else ""

        triple["subject"]["label"] = remediated_domain if remediated_domain else original_domain
        triple["object"]["label"] = remediated_range if remediated_range else original_range
        triple["subject"]["text"] = remediated_domain_text
        triple["object"]["text"] = remediated_range_text
        triple["predicate"] = remediated_predicate if remediated_predicate else original_predicate

        if original_domain != remediated_domain:
            fixed_label.append(f"Remediated domain from '{original_domain}' to '{remediated_domain}'")

        if original_range != remediated_range:
            fixed_label.append(f"Remediated range from '{original_range}' to '{remediated_range}'")

        if original_predicate != remediated_predicate:
            fixed_label.append(f"Remediated predicate from '{original_predicate}' to '{remediated_predicate}'")


    remediated_triples = []
    remidiated_list = []
    for triple in triples:
        if settings.DEBUG:
            print("[DEBUG] tripple before remediation: ",triple)
        remediated = remediate_triple(
            domain=triple.get("subject", {}).get("label", ""),
            predicate=triple.get("predicate", ""),
            range=triple.get("object", {}).get("label", "")
        )

        if not remediated:
            remediated_triples.append(triple)
            continue

        expanded = []
        for rem_triple in remediated:
            updated_triple = {
                **triple,
                "predicate": rem_triple["predicate"],
                "subject": {
                    **triple.get("subject", {}),
                    "label": rem_triple["domain"]
                },
                "object": {
                    **triple.get("object", {}),
                    "label": rem_triple["range"]
                }
            }
            remediated_triples.append(updated_triple)
            expanded.append(updated_triple)
        
        # Log modifications if any actual changes or expansion occurred
        if len(expanded) == 1 and expanded[0] == triple:
            continue
        
        remidiated_list.append({
            "original": triple,
            "remediated": expanded
        })

    # Add remididated entities  
    entities = [entity for triple in remediated_triples for entity in [triple["subject"], triple["object"]]]
    
    # Detect any hierarchical parent relationships that need n10s inference
    inference_relationships = []
    for triple in remediated_triples:
        subject = triple.get("subject", [])
        subject_label = subject.get("label", "") if subject else ""
        objectt = triple.get("object", [])
        object_label = objectt.get("label", "") if subject else ""
        predicate = triple.get("predicate", "")
        if not subject_label or not object_label: continue
        if is_parent_relationship(subject_label=subject_label, predicate=predicate, object_label=object_label):
            inference_relationships.append(predicate)
    inference_relationships = list(set(inference_relationships))

    if settings.DEBUG:
        print("[DEBUG] Remediated entities:", entities)
        print("[DEBUG] Remediated triples:", remediated_triples)
        print("[DEBUG] Detected inference relationships:", inference_relationships)
    return {
        "triples": remediated_triples,
        "entities": entities,
        "inference_relationships": inference_relationships,
        "metrics": {
            **state.get("metrics", {}),
            "remediate_triples": remidiated_list,
            "fixed_labels": fixed_label
        }
    }

# Experimental feature for correcting relationship directions
def correct_relationship(subject : str|None, object : str|None, predicate : str|None):
    schema = get_schema()
    relationships = schema.get("relationships", [])
    for rel in relationships:
        if rel.get("type") == predicate and rel.get("start") == subject and rel.get("end") == object:
            return {
                "subject": rel.get("end"),
                "predicate": rel.get("type"),
                "object": rel.get("start")
            }
    return None
