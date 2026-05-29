from typing import List, TypedDict
    
class EvaluationMetrics(TypedDict):
    score: float
    precision: float
    recall: float

class EvaluationResult(TypedDict):
    evaluation: EvaluationMetrics
    errors: List[str]