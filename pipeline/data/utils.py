from typing import Any, Dict, List, TypedDict
from .dataset import manual_samples
from helper import pretty_print

class EvaluationSample(TypedDict):
    question: str
    cypher_query: str
    expected_answer: str 
    nodes: List[Dict[str, Any]]

def loadEvaluationSamples() -> List[EvaluationSample]:
    samples = []
    for sample in manual_samples:
        evaluation_sample = EvaluationSample(
            question=sample["question"],
            cypher_query=sample["expected_cypher"],
            expected_answer=sample["expected_answer"],
            nodes=sample["nodes"]
        )
        samples.append(evaluation_sample)
    return samples

def get_sample_with_id(id: int) -> EvaluationSample:
    samples = loadEvaluationSamples()
    if 0 < id <= len(samples):
        return samples[id - 1]  # Adjusting for 1-based indexing
    else:
        raise IndexError("Sample ID out of range.")
    
if __name__ == "__main__":
    samples = loadEvaluationSamples()
    pretty_print(samples[52])