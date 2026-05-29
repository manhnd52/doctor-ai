from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class NerService(ABC):
    """Service responsible for extracting entities from text. The actual implementation can be based on any NER model or API."""
    def __init__(self, node_types: List[str], rel_types: Optional[List[str]]):
        self.node_types : Optional[List[str]] = node_types  # example: ["Disease", "Symptom", "Medication",...]
        self.rel_types : Optional[List[str]] = rel_types  # example: ["treats", "causes", "indicates",...]

    @abstractmethod
    def extract(self, text: str) -> List[Dict]:
        """
        Have to return entities list with the given text. Each entity should have a type from `self.node_types` if possible.
        """
        return [
            {
                "text": "mock_entity",
                "category": "Node",
                "type": self.node_types[0] if self.node_types else None
            }
        ]
    


