from collections import namedtuple
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional, Literal, cast, LiteralString, Any
import re
import json
from flatten_json import flatten
from CyVer import SyntaxValidator, SchemaValidator, PropertiesValidator
from helper import pretty_print, pretty_print_flattened
from rapidfuzz import process, fuzz
from helper import normalize_text

load_dotenv()

graph = None

def get_graph_driver():
    return get_graph()._driver

def get_graph():
    global graph
    if graph is None:
        graph = Neo4jGraph(
            url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "12345678"),
            enhanced_schema=True
        )
    return graph

def get_schema(): 
    "Schema is in the json format with keys: node_props, relationships, node_types, relationship_types"
    cache_file = "cache/schema_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    
    graph = get_graph()
    schema = graph.get_structured_schema
    schema["node_types"] = sorted(schema.get("node_props", {}).keys())
    schema["relationship_types"] = sorted(
        {rel["type"] for rel in schema.get("relationships", [])}
    )

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(schema, f)

    return schema

if __name__ == "__main__":
    pretty_print(get_schema())

def get_formatted_schema(get_new: bool = False) -> str:
    cache_file = "cache/formatted_schema_cache.txt"
    if os.path.exists(cache_file) and not get_new:
        with open(cache_file, "r") as f:
            return f.read()
    
    graph = get_graph()
    schema = graph.schema
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w") as f:
        f.write(schema)
    return schema

def get_langchain_formatted_schema():
    from langchain_neo4j.chains.graph_qa.cypher_utils import Schema

    schema = get_schema()
    relationships = schema.get("relationships", [])
    schemas = [Schema(rel["start"], rel["type"], rel["end"]) for rel in relationships]
    return schemas

def search_entity(entity: str, top_k: int, threshold: Optional[float] = None) -> List[Dict]:
    graph = get_graph()

    query_parts = [
        """
        CALL db.index.fulltext.queryNodes("label_name_ft", $entity)
        YIELD node, score
        """
    ]

    if threshold is not None:
        query_parts.append("WHERE score >= $threshold")

    query_parts.append("""
        RETURN node.index as index,
               node.name as name,
               labels(node)[0] as label,
               score
        ORDER BY score DESC
        LIMIT $top_k
    """)

    search_query = "\n".join(query_parts)

    # clean data for fulltext search
    entity = re.sub(r"[^0-9a-zA-Z'’\s]", "", entity)

    if not entity:
        return []
    
    params = {
        "entity": entity,
        "top_k": top_k
    }

    if threshold is not None:
        params["threshold"] = threshold

    results = graph.query(search_query, params=params)

    return results

def validate_cypher(cypher: str) -> tuple[bool, List[Dict]]:
    driver = get_graph_driver()
    syntax_validator = SyntaxValidator(driver, check_multilabeled_nodes=True)
    is_valid, syntax_metadata = syntax_validator.validate(cypher, database_name="neo4j")

    schema_validator = SchemaValidator(driver)
    schema_score, schema_metadata = schema_validator.validate(cypher, database_name="neo4j")

    property_validator = PropertiesValidator(driver)
    props_score, props_metadata = property_validator.validate(cypher, database_name="neo4j", strict=False)

    all_metadata: List[Dict] = []
    if isinstance(syntax_metadata, list):
        all_metadata.extend(syntax_metadata)
    if isinstance(schema_metadata, list):
        all_metadata.extend(schema_metadata)
    if isinstance(props_metadata, list):
        all_metadata.extend(props_metadata)

    is_fully_valid = bool(
        is_valid is True
        and schema_score == 1
        and (props_score == 1 or props_score is None)
    )

    return is_fully_valid, all_metadata

def get_predicate_descriptions() -> List[Dict[str, str]]:
    from data import predicate_descriptions
    return predicate_descriptions

def is_valid_tripple(domain: str, predicate: str, range: str) -> bool:
    from data import predicate_descriptions
    for rel in predicate_descriptions:
        if rel["subject"] == domain and rel["predicate"] == predicate and rel["object"] == range:
            return True
    return False

def remediate_triple(domain: str, predicate: str, range: str) -> Optional[tuple[Dict[str, str], Optional[str]]]:
    """Given a potentially invalid triple, attempt to remediate it by finding the closest valid triple in the predicate descriptions. Returns the remediated triple and the part that was remediated (domain, predicate, or range).
    **If can't be remediated, returns `None`**.
    """
    from data import predicate_descriptions

    normalized_domain = _normalize_label(domain)
    normalized_predicate = _normalize_label(predicate)
    normalized_range = _normalize_label(range)

    if is_valid_tripple(domain, predicate, range):
        return {
            "domain": domain,
            "predicate": predicate,
            "range": range
        }, None
    
    for rel in predicate_descriptions:
        subject = _normalize_label(rel["subject"])
        rel_predicate = _normalize_label(rel["predicate"])
        obj = _normalize_label(rel["object"])

        if subject == normalized_domain and rel_predicate == normalized_predicate:
            return {
                "domain": rel["subject"],
                "predicate": rel["predicate"],
                "range": rel["object"]
            }, "range"
        
        if rel_predicate == normalized_predicate and obj == normalized_range:
            return {
                "domain": rel["subject"],
                "predicate": rel["predicate"],
                "range": rel["object"]
            }, "domain"
        
        if subject == normalized_domain and obj == normalized_range:
            return {
                "domain": rel["subject"],
                "predicate": rel["predicate"],
                "range": rel["object"]
            }, "predicate"
        
    return None # Cannot remediate

def remidiate_label(label: str, label_type: Literal["node", "relationship"], threshold: float = 0.8) -> Optional[str]:
    """Given a potentially invalid label, attempt to remediate it by finding the closest valid label in the schema. Returns the remediated label and the type of the label (node or relationship).
    **If can't be remediated, returns `None`**.
    """
    schema = get_schema()
    valid_labels = []
    if label_type == "node":
        valid_labels = schema.get("node_types", [])
    elif label_type == "relationship":
        valid_labels = schema.get("relationship_types", [])
    else:
        raise ValueError("Schema is not available for remediation")

    normarized_label = _normalize_label(label)

    # First check for exact match (case-insensitive)
    for valid_label in valid_labels:
        if valid_label.lower() == normarized_label.lower():
            return valid_label
    
    # If no exact match, use fuzzy matching to find the closest label
    res = process.extractOne(
        query=normarized_label,
        choices=valid_labels,
        scorer=fuzz.ratio
    )

    if res is None:
        return None

    match, score, idx = res
    
    if score >= threshold * 100:  # Convert to percentage
        return match

    return None # Cannot remediate

def _normalize_label(label: str) -> str:
    label = label.strip().lower()
    label = re.sub(r'[\s\-]+', '_', label)   # space, dash -> _
    label = re.sub(r'[^a-z0-9_]', '', label)  # remove ký tự lạ
    label = re.sub(r'_+', '_', label)  # multiple _ -> single _
    return label


def set_graph(new_graph: Neo4jGraph) -> None:
    """Inject a custom Neo4jGraph instance (Dependency Injection)."""
    global graph
    graph = new_graph


def init_graph(
    url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Neo4jGraph:
    """Initialize and set the global Neo4jGraph instance."""
    global graph

    url_val = url or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user_val = username or os.getenv("NEO4J_USER", "neo4j")
    pwd_val = password or os.getenv("NEO4J_PASSWORD", "12345678")

    graph = Neo4jGraph(
        url=url_val,
        username=user_val,
        password=pwd_val,
        enhanced_schema=True
    )
    return graph


if __name__ == "__main__":
    # Example usage
    remediated_label = remidiate_label("PhenotypePresent", "relationship")

    print(remediated_label)

    print(remediate_triple("disease", "phenotype_present", "disease"))
