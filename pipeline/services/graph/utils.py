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
from config import settings

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
    schema_path = os.path.join("data", "schema.json")
    if not os.path.exists(schema_path):
        schema_path = "cache/schema_cache.json"
        
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    graph = get_graph()
    schema = graph.get_structured_schema
    schema["node_types"] = sorted(schema.get("node_props", {}).keys())
    schema["relationship_types"] = sorted(
        {rel["type"] for rel in schema.get("relationships", [])}
    )

    os.makedirs(os.path.dirname(schema_path), exist_ok=True)
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)

    return schema

def is_parent_relationship(predicate: str, subject_label: str, object_label: str) -> bool:
    """Check if a relationship type is a parent relationship in the schema ontology/hierarchy."""
    schema = get_schema()
    relationships = schema.get("relationships", [])
    if settings.DEBUG:
        print(f"[DEBUG] Parent relationship check: {predicate}: ({subject_label}) -> ({object_label})")
    for rel in relationships:
        if rel.get("type") == predicate and rel.get("start") == subject_label and rel.get("end") == object_label:
            if "children" in rel and isinstance(rel["children"], list): return True
        if rel.get("type") == predicate and rel.get("start") == object_label and rel.get("end") == subject_label:
            if "children" in rel and isinstance(rel["children"], list): return True
    return False


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

_predicate_descriptions = None

def get_predicate_descriptions() -> List[Dict[str, str]]:
    global _predicate_descriptions
    if _predicate_descriptions is not None:
        return _predicate_descriptions
    
    schema_path = os.path.join("data", "schema.json")
    if not os.path.exists(schema_path):
        schema_path = os.path.join("cache", "schema_cache.json")
        
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    else:
        schema = get_schema()
        
    relationships = schema.get("relationships", [])
    _predicate_descriptions = []
    for rel in relationships:
        desc = {
            "predicate": rel.get("type", ""),
            "object": rel.get("end", ""),
            "subject": rel.get("start", ""),
            "definition": rel.get("description", "")
        }
        if "same_as" in rel:
            desc["same_as"] = rel["same_as"]
        _predicate_descriptions.append(desc)
    return _predicate_descriptions

def is_valid_tripple(domain: str, predicate: str, range: str) -> bool:
    predicate_descriptions = get_predicate_descriptions()
    for rel in predicate_descriptions:
        if rel["subject"] == domain and rel["predicate"] == predicate and rel["object"] == range:
            return True
    return False

def remediate_triple(domain: str, predicate: str, range: str) -> List[Dict[str, str]]:
    """Given a potentially invalid triple, attempt to remediate it by finding the closest valid triple in the predicate descriptions. Returns a list of remediated/feasible triples.
    """
    def is_missing(val: str) -> bool:
        return val is None or not isinstance(val, str) or val.strip() in ("", "?", "_")

    norm_domain = None if is_missing(domain) else _normalize_label(domain)
    norm_pred = None if is_missing(predicate) else _normalize_label(predicate)
    norm_range = None if is_missing(range) else _normalize_label(range)

    predicate_descriptions = get_predicate_descriptions()

    if None in (norm_domain, norm_pred, norm_range):
        return [
            {
                "domain": rel["subject"],
                "predicate": rel["predicate"],
                "range": rel["object"]
            }
            for rel in predicate_descriptions
            if (norm_domain is None or _normalize_label(rel["subject"]) == norm_domain)
            and (norm_pred is None or _normalize_label(rel["predicate"]) == norm_pred)
            and (norm_range is None or _normalize_label(rel["object"]) == norm_range)
        ]

    if is_valid_tripple(domain, predicate, range):
        return [{
            "domain": domain,
            "predicate": predicate,
            "range": range
        }]

    for rel in predicate_descriptions:
        matches = (
            (_normalize_label(rel["subject"]) == norm_domain)
            + (_normalize_label(rel["predicate"]) == norm_pred)
            + (_normalize_label(rel["object"]) == norm_range)
        )
        if matches == 2:
            return [{
                "domain": rel["subject"],
                "predicate": rel["predicate"],
                "range": rel["object"]
            }]

    return []
    
def remidiate_label(label: str, label_type: Literal["node", "relationship"], threshold: float = 0.8) -> Optional[str]:
    """Given a potentially invalid label, attempt to remediate it by finding the closest valid label in the schema. Returns the remediated label and the type of the label (node or relationship).
    **If can't be remediated, returns `None`**.
    """
    schema = get_schema()
    valid_labels = []
    if label_type == "node":
        node_types = schema.get("node_types", [])
        valid_labels = [node["type"] for node in node_types]
    elif label_type == "relationship":
        valid_labels = schema.get("relationship_types", [])
    else:
        raise ValueError("Schema is not available for remediation")

    normarized_label = _normalize_label(label)

    if label_type == "relationship":
        relationships = schema.get("relationships", [])
        for rel in relationships:
            same_as = rel.get("same_as", [])
            for synonym in same_as:
                if _normalize_label(synonym) == normarized_label:
                    return rel.get("type")

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
    print("test remidiate_triple", end=" ")
    print(remediate_triple("disease", "associated_with", "drug"))
    print(remediate_triple("drug", "associated_with", "disease"))
    print("test remidiate_label (treats):", remidiate_label("treats", "relationship"))
    print("test remidiate_label (treated_by):", remidiate_label("treated_by", "relationship"))
