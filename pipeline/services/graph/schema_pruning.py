import os
import json
from typing import List, Dict, Set, Any


def load_schema_json() -> Dict[str, Any]:
    """Loads the schema JSON file. Looks first in cache, then in data."""
    paths = [
        os.path.join("cache", "schema_cache.json"),
        os.path.join("data", "schema.json")
    ]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Schema JSON file not found in cache or data directories.")


def get_directly_matched_nodes(
    node_props: Dict[str, List[Dict[str, str]]],
    node_types_metadata: List[Dict[str, Any]],
    normalized_keywords: List[str]
) -> Set[str]:
    """Identifies node types that directly match any keyword."""
    matched = set()
    
    # 1. Match by node name
    for node_name in node_props.keys():
        if any(kw in node_name.lower() for kw in normalized_keywords):
            matched.add(node_name)
            
    # 2. Match by property names
    for node_name, props in node_props.items():
        for prop_info in props:
            prop_name = prop_info.get("property", "")
            if any(kw in prop_name.lower() for kw in normalized_keywords):
                matched.add(node_name)
                
    # 3. Match by description in node_types metadata
    for meta in node_types_metadata:
        node_type = meta.get("type", "")
        desc = meta.get("description", "")
        if any(kw in desc.lower() for kw in normalized_keywords):
            matched.add(node_type)
            
    return matched


def get_directly_matched_rels(
    relationships: List[Dict[str, Any]],
    normalized_keywords: List[str]
) -> Set[str]:
    """Identifies relationship types that match the keywords directly."""
    matched = set()
    for rel in relationships:
        rel_type = rel.get("type", "")
        desc = rel.get("description", "")
        if any(kw in rel_type.lower() for kw in normalized_keywords):
            matched.add(rel_type)
        elif desc and any(kw in desc.lower() for kw in normalized_keywords):
            matched.add(rel_type)
    return matched


def get_directly_matched_object_props(
    node_object_props: Dict[str, List[Dict[str, Any]]],
    normalized_keywords: List[str]
) -> List[Dict[str, Any]]:
    """Identifies node object properties that directly match keywords."""
    matched = []
    for start_node, obj_props in node_object_props.items():
        for entry in obj_props:
            label = entry.get("label", "")
            relationship = entry.get("relationship", "")
            description = entry.get("description", "")
            
            if (any(kw in label.lower() for kw in normalized_keywords) or
                any(kw in relationship.lower() for kw in normalized_keywords) or
                any(kw in description.lower() for kw in normalized_keywords) or
                any(kw in start_node.lower() for kw in normalized_keywords)):
                matched.append({
                    "start": start_node,
                    "label": label,
                    "relationship": relationship,
                    "description": description
                })
    return matched


def filter_relationships(
    relationships: List[Dict[str, Any]],
    matched_nodes: Set[str],
    matched_rels: Set[str]
) -> List[Dict[str, Any]]:
    """Filters the relationships list based on matched node and relationship types."""
    kept = []
    for rel in relationships:
        start = rel.get("start", "")
        end = rel.get("end", "")
        rel_type = rel.get("type", "")
        
        # Keep relationship if its type is directly matched, or start/end is directly matched
        if (rel_type in matched_rels or
            start in matched_nodes or
            end in matched_nodes):
            kept.append(rel)
    return kept


def filter_node_object_props(
    node_object_props: Dict[str, List[Dict[str, Any]]],
    kept_nodes: Set[str],
    matched_object_props: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """Filters node object properties to keep only those where start and target nodes are kept."""
    kept = {}
    matched_keys = {(item["start"], item["relationship"], item["label"]) for item in matched_object_props}
    
    for start_node, obj_props in node_object_props.items():
        for entry in obj_props:
            label = entry.get("label", "")
            relationship = entry.get("relationship", "")
            
            if ((start_node in kept_nodes and label in kept_nodes) or
                (start_node, relationship, label) in matched_keys):
                if start_node not in kept:
                    kept[start_node] = []
                kept[start_node].append(entry)
    return kept


def format_node_properties(
    node_name: str,
    props: List[Dict[str, Any]],
    node_types_metadata: List[Dict[str, Any]]
) -> List[str]:
    """Formats properties of a single node type."""
    lines = [f"- **{node_name}**"]
    
    # Check if there are values defined in node_types metadata (e.g. approval_status values)
    meta_values = []
    for meta in node_types_metadata:
        if meta.get("type") == node_name:
            meta_values = meta.get("values", [])
            break
            
    for prop_info in props:
        prop_name = prop_info.get("property", "")
        prop_type = prop_info.get("type", "STRING")
        prop_values = prop_info.get("values", [])
        prop_desc = prop_info.get("description", "")
        
        # Determine the available options/values
        values = prop_values if prop_values else (meta_values if prop_name == "name" else [])
        
        line = f"  - `{prop_name}`: {prop_type}"
        if values:
            val_str = ", ".join(f"'{v}'" for v in values)
            line += f" Available options: [{val_str}]"
        if prop_desc:
            line += f" (Description: {prop_desc})"
            
        lines.append(line)
            
    return lines


def format_object_properties(
    pruned_node_object_props: Dict[str, List[Dict[str, Any]]],
    node_props: Dict[str, List[Dict[str, Any]]],
    node_types_metadata: List[Dict[str, Any]]
) -> List[str]:
    """Formats the object properties section."""
    lines = []
    for start_node, entries in pruned_node_object_props.items():
        for entry in entries:
            relationship = entry.get("relationship", "")
            label = entry.get("label", "")
            desc = entry.get("description", "")
            
            lines.append(f"- **{relationship}**: {start_node} -> {label}")
            if desc:
                lines.append(f"    - Description: {desc}")
                
            # Retrieve and format the properties of the target node (label)
            target_props = node_props.get(label, [])
            for prop_info in target_props:
                prop_name = prop_info.get("property", "")
                prop_type = prop_info.get("type", "STRING")
                prop_values = prop_info.get("values", [])
                prop_desc = prop_info.get("description", "")
                
                # Check for meta values
                meta_values = []
                for meta in node_types_metadata:
                    if meta.get("type") == label:
                        meta_values = meta.get("values", [])
                        break
                        
                values = prop_values if prop_values else (meta_values if prop_name == "name" else [])
                
                prop_line = f"    - `{prop_name}`: {prop_type}"
                if values:
                    val_str = ", ".join(f"'{v}'" for v in values)
                    prop_line += f" Available options: [{val_str}]"
                if prop_desc:
                    prop_line += f" (Description: {prop_desc})"
                    
                lines.append(prop_line)
            lines.append("")
    return lines


def format_relationships(relationships: List[Dict[str, Any]]) -> List[str]:
    """Formats the relationships list."""
    lines = ["The relationships:"]
    for rel in relationships:
        start = rel.get("start", "")
        rel_type = rel.get("type", "")
        end = rel.get("end", "")
        desc = rel.get("description", "")
        
        lines.append(f"(:{start})-[:{rel_type}]->(:{end})")
        if desc:
            lines.append(f"  - Description: {desc}")
    return lines


def format_ontology(relationships: List[Dict[str, Any]], ontology: Dict[str, Any]) -> List[str]:
    """Formats the relationship ontology hierarchy."""
    lines = []
    hierarchy = ontology.get("relationship_hierarchy", {})
    if hierarchy:
        lines.append("Relationship Ontology (Hierarchy):")
        kept_types = {rel.get("type") for rel in relationships}
        has_ontology = False
        for child, parent in hierarchy.items():
            if child in kept_types:
                lines.append(f"- **{child}** is a sub-property of **{parent}**")
                has_ontology = True
        if not has_ontology:
            lines.append("No active relationship hierarchy for the pruned schema.")
    return lines


def load_concepts() -> List[Dict[str, Any]]:
    """Loads concepts from data/concept.json."""
    path = os.path.join("data", "concept.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "name" in data:
            return [data]
    except Exception:
        pass
    return []


def filter_concepts(concepts: List[Dict[str, Any]], normalized_keywords: List[str]) -> List[Dict[str, Any]]:
    """Filters concepts based on keywords matching name, description, alias, or patterns."""
    if not normalized_keywords:
        return concepts
        
    kept = []
    for concept in concepts:
        name = concept.get("name", "").lower()
        desc = concept.get("description", "").lower()
        aliases = [a.lower() for a in concept.get("alias", [])] + [a.lower() for a in concept.get("aliases", [])]
        patterns = [p.lower() for p in concept.get("patterns", [])]
        
        matched = False
        for kw in normalized_keywords:
            if (kw in name or 
                kw in desc or 
                any(kw in a or a in kw for a in aliases) or 
                any(kw in p for p in patterns)):
                matched = True
                break
        if matched:
            kept.append(concept)
    return kept


def format_concepts(concepts: List[Dict[str, Any]]) -> List[str]:
    """Formats the relevant concepts section."""
    lines = []
    if concepts:
        lines.append("Relevant Concepts:")
        for concept in concepts:
            name = concept.get("name", "")
            desc = concept.get("description", "")
            patterns = concept.get("patterns", [])
            
            lines.append(f"- **{name}**: {desc}")
            if patterns:
                lines.append("    - Patterns:")
                for p in patterns:
                    lines.append(f"      - {p}")
    return lines


def singularize(word: str) -> str:
    """Returns the singular form of a word if it is plural."""
    w = word.lower().strip()
    if w.endswith("status"):
        return w
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("sses"):
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w

def get_prune_schema_by_keywords(keywords: List[str]) -> str:
    """Prunes the graph schema by matching keywords directly on the JSON schema
    and generates the formatted schema text output.
    """
    schema = load_schema_json()
    
    node_props = schema.get("node_props", {})
    relationships = schema.get("relationships", [])
    node_types_metadata = schema.get("node_types", [])
    ontology = schema.get("ontology", {})
    node_object_props = schema.get("node_object_props", {})
    concepts = load_concepts()
    
    normalized_keywords = []
    for kw in keywords:
        kw_clean = kw.lower().strip()
        if kw_clean:
            if kw_clean not in normalized_keywords:
                normalized_keywords.append(kw_clean)
            sing = singularize(kw_clean)
            if sing not in normalized_keywords:
                normalized_keywords.append(sing)
    
    # If no keywords are provided, return the full schema formatted
    if not normalized_keywords:
        matched_nodes = set(node_props.keys())
        kept_relationships = relationships
        pruned_node_object_props = node_object_props
        kept_concepts = concepts
    else:
        matched_nodes = get_directly_matched_nodes(node_props, node_types_metadata, normalized_keywords)
        matched_rels = get_directly_matched_rels(relationships, normalized_keywords)
        
        # Match directly matched object props
        matched_obj_props = get_directly_matched_object_props(node_object_props, normalized_keywords)
        for op in matched_obj_props:
            matched_nodes.add(op["start"])
            matched_nodes.add(op["label"])
            matched_rels.add(op["relationship"])
            
        kept_relationships = filter_relationships(relationships, matched_nodes, matched_rels)
        
        # Ensure start/end of kept relationships are also kept in nodes
        for rel in kept_relationships:
            matched_nodes.add(rel.get("start", ""))
            matched_nodes.add(rel.get("end", ""))
            
        pruned_node_object_props = filter_node_object_props(node_object_props, matched_nodes, matched_obj_props)
        kept_concepts = filter_concepts(concepts, normalized_keywords)
        
    # Format sections
    output_lines = []
    
    # 1. Node properties
    output_lines.append("Node properties:")
    for node_name in sorted(matched_nodes):
        if node_name in node_props:
            node_lines = format_node_properties(node_name, node_props[node_name], node_types_metadata)
            output_lines.extend(node_lines)
    output_lines.append("")
    
    # 2. Object properties
    output_lines.append("Object properties:")
    if pruned_node_object_props:
        obj_lines = format_object_properties(pruned_node_object_props, node_props, node_types_metadata)
        output_lines.extend(obj_lines)
    else:
        output_lines.append("")
    output_lines.append("")
    
    # 3. Relationship properties
    output_lines.append("Relationship properties:")
    output_lines.append("")
    
    # 4. The relationships
    output_lines.extend(format_relationships(kept_relationships))
    output_lines.append("")
    
    # 5. Relationship Ontology
    ontology_lines = format_ontology(kept_relationships, ontology)
    if ontology_lines:
        output_lines.extend(ontology_lines)
        output_lines.append("")
        
    # 6. Relevant Concepts
    concept_lines = format_concepts(kept_concepts)
    if concept_lines:
        output_lines.extend(concept_lines)
        output_lines.append("")
        
    return "\n".join(output_lines)


if __name__ == "__main__":
    # Quick debug run
    test_keywords = ["disease", "drugs", "linked to"]
    print(f"--- Pruning test with keywords: {test_keywords} ---")
    result = get_prune_schema_by_keywords(test_keywords)
    print(result)
