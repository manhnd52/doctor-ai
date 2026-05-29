from services.graph.utils import get_schema, remediate_triple, remidiate_label
from config import settings

def triple_remediation_node(state):
    """
    This function is responsible for remediating the extracted triples and entities to ensure they are in a consistent format for the next step of cypher generation. It takes the current state of the conversation, extracts the relevant information, and returns a dictionary containing the remediated triples and any associated metrics.
    """
    fixed_label = []
    triples = state.get("triples", [])
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
        remediated_domain_text = original_domain_text.lower()
        remediated_range_text = original_range_text.lower()

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
    for triple in triples:
        remediated = remediate_triple(
            domain=triple.get("subject", {}).get("label", ""),
            predicate=triple.get("predicate", ""),
            range=triple.get("object", {}).get("label", "")
        )

        if remediated is None:
            remediated_triples.append(triple)
            continue

        remediated_triple, remediated_part = remediated
        updated_triple = {
            **triple,
            "predicate": remediated_triple["predicate"],
            "subject": {
                **triple.get("subject", {}),
                "label": remediated_triple["domain"]
            },
            "object": {
                **triple.get("object", {}),
                "label": remediated_triple["range"]
            }
        }
        remediated_triples.append(updated_triple)

    remidiated_list = []
    
    # Log the remediation process for debugging purposes
    for i, remidiated_triple in enumerate(remediated_triples):
        if remidiated_triple != triples[i]:
            remidiated_list.append({
                "original": triples[i],
                "remediated": remidiated_triple
            })

    # Add remididated entities  
    entities = [entity for triple in remediated_triples for entity in [triple["subject"], triple["object"]]]

    if settings.DEBUG:
        print("[DEBUG] Remediated entities:", entities)
    return {
        "triples": remediated_triples,
        "entities": entities,
        "metrics": {
            **state.get("metrics", {}),
            "remediate_triples": remidiated_list,
            "fixed_labels": fixed_label
        }
    }

# Experimental feature for correcting relationship directions
def correct_relationship(cypher : str) -> str:
    from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
    # Cypher query corrector is experimental
    corrector_schema = [
        Schema(el["start"], el["type"], el["end"])
        for el in get_schema().get("relationships", [])
    ]
    cypher_query_corrector = CypherQueryCorrector(corrector_schema)
    return cypher_query_corrector(cypher)