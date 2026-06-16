from typing import Any, Collection, Dict, Iterable, List, Set, Tuple

from .type import EvaluationResult
from .utils import error_eval, f1_score, intersection_over_union, precision, recall
from services.graph import get_graph
from pipeline_state import GraphState
from flatten_json import flatten

def evaluation_node(state: GraphState):
    query_result = state.get("query_result", None)
    expected_nodes = state.get("expected_nodes", None)
    existing_errors = state.get("errors", [])
    if not isinstance(existing_errors, list):
        existing_errors = []

    if query_result is None or query_result == []:
        return {
            "evaluation": None,
            "errors": existing_errors + [("Evaluation", "No query result to evaluate.")],
        }
    
    res = evaluate(query_result, expected_nodes)

    # Merge new errors with existing errors in state
    new_err = res.get("errors", [])
    if not isinstance(new_err, list):
        new_err = [new_err]

    err = existing_errors + [("Evaluation", info) for info in new_err]

    return {"evaluation": res.get("evaluation", None), "errors": err}

# Expected result is `Nodes` in EvaluationSample
def evaluate(query_result, expected_nodes) -> EvaluationResult:
    if not query_result or not expected_nodes:
        return error_eval("Query result or expected result is missing.")

    try:
        if not isinstance(expected_nodes, list) or len(expected_nodes) == 0:
            return error_eval("Expected result nodes are missing or invalid.")

        score, eval_precision, eval_recall = evaluate_sample(
            query_result=query_result, 
            expected_nodes=expected_nodes
        )

        return {
            "evaluation": {
                "score": score,
                "precision": eval_precision,
                "recall": eval_recall,
            },
            "errors": []
        }
    except Exception as e:
        return error_eval(f"Error occurred during evaluation: {str(e)}")        

def evaluate_sample(query_result: List[Dict[str, Any]], expected_nodes: List[Dict[str, Any]]) -> Tuple[float, float, float]:
    if not query_result or not expected_nodes:
        return 0.0, 0.0, 0.0

    if "index" in expected_nodes[0]:
        return evaluate_sample_with_single_index(expected_nodes=expected_nodes, result=query_result)
    if "value" in expected_nodes[0]:
        return evaluate_sample_with_value_result(expected_nodes=expected_nodes, result=query_result)
    return evaluate_sample_with_tuple_in_label(expected_nodes=expected_nodes, result=query_result)

def evaluate_sample_with_single_index(
    expected_nodes: List[Dict[str, Any]], result: List[Dict[str, Any]]
) -> Tuple[float, float, float]:
    ids = [node["index"] for node in expected_nodes if "index" in node]
    expected_names = None
    if "name" in expected_nodes[0]:
        expected_names = [node["name"].strip().lower() for node in expected_nodes 
                          if "name" in node and isinstance(node["name"], str)]
    else: 
        expected_names = {name.strip().lower() for name in query_node_names(ids) 
                          if isinstance(name, str)}
    flattened_result = [flatten(item) for item in result]
    all_scores = _get_scores_per_key(expected_names, flattened_result)
    return max(all_scores.values(), key=lambda s: s[0])

def evaluate_sample_with_value_result(
    expected_nodes: List[Dict[str, Any]], result: List[Dict[str, Any]]
) -> Tuple[float, float, float]:
    expected_values = {
        str(node["value"]).strip().lower()
        for node in expected_nodes
        if "value" in node and node["value"] is not None
    }
    flattened_result = [flatten(item) for item in result]
    all_scores = _get_scores_per_key(expected_values, flattened_result)
    return max(all_scores.values(), key=lambda s: s[0])


def evaluate_sample_with_tuple_in_label(
    expected_nodes: List[Dict[str, Any]], result: List[Dict[str, Any]]
) -> Tuple[float, float, float]:
    tuple_size = max(
        int(key[len("index") :]) # Extract the number after "index"
        for key in expected_nodes[0]
        if key.startswith("index") and key[len("index") :].isdigit()
    ) + 1

    indices = [f"index{i}" for i in range(tuple_size)]
    name_indices = [f"name{i}" for i in range(tuple_size)]
    expected_values_per_pos = {}

    for index_key, name_key in zip(indices, name_indices):
        expected_values_per_pos[index_key] = []
        for node in expected_nodes:
            val = node.get(name_key)
            expected_values_per_pos[index_key].append(
                val.strip().lower() if isinstance(val, str) else ""
            )

    best_result_keys = {}
    for index_key, expected_values in expected_values_per_pos.items(): 
        filtered_expected = [val for val in expected_values if val]
        per_key_scores = _get_scores_per_key(filtered_expected, result)
        best_result_keys[index_key] = max(per_key_scores, key=lambda result_key: per_key_scores[result_key][0])

    expected_tuples = set()
    for row in range(len(expected_nodes)):
        tuple_values = []
        for index_key in indices:
            tuple_values.append(expected_values_per_pos[index_key][row])
        expected_tuples.add(tuple(tuple_values))

    result_tuples = set()
    for row in result:
        tuple_values = []
        for index_key in indices:
            result_key = best_result_keys[index_key]
            tuple_values.append(_normalize_single_value(row.get(result_key)))
        result_tuples.add(tuple(tuple_values))

    return (
        intersection_over_union(result_tuples, expected_tuples),
        precision(result_tuples, expected_tuples),
        recall(result_tuples, expected_tuples),
    )


def query_node_names(ids: Iterable[int]) -> List[str]:
    cypher_query = """
    UNWIND $ids AS id
    MATCH (n)
    WHERE n.index = id
    RETURN n.name AS name
    """
    graph = get_graph()
    results = graph.query(cypher_query, params={"ids": list(ids)})
    return [record["name"] for record in results if "name" in record and record["name"] is not None]


def _get_scores_per_key(
    expected_values: Collection[str], result: List[Dict[str, Any]]
) -> Dict[str, Tuple[float, float, float]]:
    if len(result) == 0:
        return {"INVALID_KEY": (0.0, 0.0, 0.0)}

    query_result_output_keys = list(result[0].keys())
    return {
        key: _compute_score_for_key(expected_values, result, key)
        for key in query_result_output_keys
    }

def _compute_score_for_key(
    expected_values: Collection[str], result_graph_output: List[Dict[str, Any]], key: str
) -> Tuple[float, float, float]:
    if len(result_graph_output) == 0:
        return 0.0, 0.0, 0.0

    entries = {
        _normalize_single_value(item.get(key))
        for item in result_graph_output
        if key in item
    }
    entries = {entry for entry in entries if entry}

    if len(entries) == 0:
        return 0.0, 0.0, 0.0

    expected = {str(value).strip().lower() for value in expected_values}
    if len(expected) == 0:
        return 0.0, 0.0, 0.0

    return (
        f1_score(entries, expected),
        precision(entries, expected),
        recall(entries, expected),
    )


def _normalize_single_value(value: Any) -> str:
    if isinstance(value, dict) and "name" in value:
        value = value["name"]
    if value is None:
        return ""
    return str(value).strip().lower()


if __name__ == "__main__":
    # Example usage
    expected_nodes = [
        {"index": 1, "name": "Hunger"},
        {"index": 2, "name": "Increased thirst"},
        {"index": 3, "name": "Frequent urination"},
        {"index": 4, "name": "Weight loss"}
    ]
    query_result = [
        {"symptom": "Increased thirst"},
        {"symptom": "Frequent urination"},
        {"symptom": "Hunger"},
    ]
    print("Test 01: ")
    print(evaluate_sample_with_single_index(expected_nodes, query_result))

    query_result = [
        {"n" : {"name": "Increased thirst"}},
        {"n" : {"name": "Frequent urination"}},
        {"n" : {"name": "Hunger"}},
        {"n" : {"name": "Weight loss"}},
    ]
    print("Test 02: ")
    print(evaluate_sample_with_single_index(expected_nodes, query_result))

    print("Test 03: ")
    expected_nodes = [
        {"value": "12"}
    ]

    query_result = [
        {"age": 12},
    ]
    print(evaluate_sample_with_value_result(expected_nodes, query_result))

    print("Test 04: ")
    expected_nodes = [
        {"index0": 1, "index1": 2, "name0": "Hunger", "name1": "Increased thirst"},
        {"index0": 3, "index1": 4, "name0": "Frequent urination", "name1": "Weight loss"},
        {"index0": 5, "index1": 6, "name0": "Fatigue", "name1": "Blurred vision"}
    ]

    query_result = [
        {"symptom1": "Hunger", "symptom2": "Increased thirst"},
        {"symptom1": "Frequent urination", "symptom2": "Weight will be loss"},
    ]

    print(evaluate_sample_with_tuple_in_label(expected_nodes, query_result))

    print("Test 05 (Both expected and query results have null): ")
    expected_nodes = [
        {"index0": 1, "index1": 2, "name0": "Drug A", "name1": None},
        {"index0": 3, "index1": 4, "name0": "Drug C", "name1": "alz65"}
    ]

    query_result = [
        {"drug": "Drug A", "target": None},
        {"drug": "Drug C", "target": "alz65"}
    ]

    print(evaluate_sample_with_tuple_in_label(expected_nodes, query_result))

