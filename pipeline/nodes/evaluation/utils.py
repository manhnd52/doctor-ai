from typing import Any, Collection, Set
from .type import EvaluationResult

# Calculate evaluation metrics
def intersection_over_union(result: Set[Any], expected: Collection[Any]) -> float:
    res = len(result.intersection(expected)) / len(result.union(expected))
    return res

def f1_score(result: Set[Any], expected: Collection[Any]) -> float:
    p = precision(result, expected)
    r = recall(result, expected)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)

def precision(result: Set[Any], expected: Collection[Any]) -> float:
    res = len(result.intersection(expected)) / len(result)
    return res


def recall(result: Set[Any], expected: Collection[Any]) -> float:
    res = len(result.intersection(expected)) / len(expected)
    return res
    
def error_eval(message: str) -> EvaluationResult:
    return {
        "evaluation": {
            "score": 0.0,
            "precision": 0.0,
            "recall": 0.0
        },
        "errors": [message]
    }