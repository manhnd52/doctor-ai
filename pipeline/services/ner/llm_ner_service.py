
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from services.ner.ner_service import NerService
    
class Entity(BaseModel):
    text: str = Field(
        description="The exact text span from the input sentence that represents the entity."
    )
    label: str = Field(
        description=(
            "The specific knowledge graph type of the entity. "
            "Example: 'Disease', 'Symptom', 'Medication' for nodes; "
        )
    )

class KGQueryIR(BaseModel): # Intermediate Representation for Knowledge Graph Query
    entities: Optional[List[Entity]] = None

class LlmNerService(NerService):
    def __init__(
        self,
        node_types: List[str] = [],
        rel_types: List[str] = [],
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ):
        super().__init__(node_types, rel_types)

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
        ).with_structured_output(KGQueryIR)

        self.prompt = ChatPromptTemplate.from_messages([
            (
            "system",
            "You are a biomedical named entity recognition (NER) specialist."
            "Your task is to extract entities from a medical question to help generate a Knowledge Graph query.\n\n"

            "Rules:\n"
            "* Only use labels from the allowed label list.\n"
            "* Extract entities only if they appear explicitly in the text. Entities MUST be labeled based on their ROLE in the question context, NOT based on their general medical or real-world classification. This means: The same term can have different labels depending on how it is used. Context OVERRIDES ontology.\n"
            "* Avoid duplicates.\n"

            "Allowed Labels:\n{labels}\n\n"

            "Question:\n{text}\n\n"
            )
            ]
        )

    def extract(self, text: str) -> Optional[Dict]:
        chain = self.prompt | self.llm
        response = chain.invoke(
            {
                "text": text,
                "labels": self.node_types,
            }
        )
        if isinstance(response, KGQueryIR):
            return response.model_dump()
        return None

def get_llm_ner_service() -> LlmNerService:
    """
    Factory function to get an instance of LlmNerService. 
    """
    from services.graph.utils import get_schema
    schema = get_schema()    
    ner_service = LlmNerService(node_types=schema["node_types"], rel_types=schema["relationship_types"])

    return ner_service

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    from services.graph.utils import get_schema

    schema = get_schema()    
    ner_service = LlmNerService(node_types=schema["node_types"], rel_types=schema["relationship_types"])
    test_text = "Which drugs have pterygium as side effect?"
    entities = ner_service.extract(test_text)
    print(entities)

