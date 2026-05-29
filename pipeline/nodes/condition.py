from typing import List, Literal

def validate_cypher_condition(
    state,
) -> Literal["end", "cypher_correction", "query_execution"]:
    if state.get("next_action") == "cypher_correction":
        return "cypher_correction"
    elif state.get("next_action") == "query_execution":
        return "query_execution"
    else:
        return "end"