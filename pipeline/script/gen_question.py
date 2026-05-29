import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from services.graph.utils import validate_cypher
from services.llm_service import get_model

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = BASE_DIR / "cache" / "formatted_schema_cache.txt"
DEFAULT_GUIDE_PATH = BASE_DIR / "cache" / "question_guide.txt"
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"


class QuestionCypherItem(BaseModel):
    question: str = Field(description="A useful biomedical question in natural English")
    expected_cypher: str = Field(description="A valid Cypher query for Neo4j that answers the question")


class GenerationOutput(BaseModel):
    items: List[QuestionCypherItem]


SYSTEM_PROMPT = """
You are an expert biomedical KG question and Cypher generation assistant.

Task:
Generate useful, realistic questions and matching Cypher queries for a biomedical knowledge graph.

Hard constraints:
1. Follow the provided QUESTION GUIDE.
2. Use ONLY labels, relationships, and properties from the provided SCHEMA.
3. Do not invent node labels, relationship types, or properties outside schema.
4. Keep question natural, concise, and meaningful for researchers/clinicians.
5. Prefer 1-hop to 3-hop queries. Avoid overly long graph traversals.
6. Return exactly requested number of items.
7. Output must be structured and contain only fields:
   - question
   - expected_cypher

QUESTION GUIDE:
<question_guide>
{question_guide}
</question_guide>

SCHEMA:
<schema>
{schema}
</schema>
""".strip()

HUMAN_PROMPT = """
Generate {count} question-cypher pairs.

Output requirements:
- Each item is independent.
- Questions should cover varied intent types from the guide.
- Cypher should be executable and return useful result columns.
- Use explicit labels where appropriate.
""".strip()


REPAIR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are fixing a Cypher query so it is valid for the given schema.
Use only schema elements. Keep the question intent unchanged.
Return only the fixed Cypher string.

SCHEMA:
<schema>
{schema}
</schema>
""".strip(),
        ),
        (
            "human",
            "Question: {question}\n\nCypher to fix:\n{cypher}\n\nError:\n{error}",
        ),
    ]
)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def generate_pairs(schema_text: str, guide_text: str, count: int) -> List[QuestionCypherItem]:
    model = get_model().with_structured_output(GenerationOutput)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )
    chain = prompt | model
    result = chain.invoke(
        {
            "schema": schema_text,
            "question_guide": guide_text,
            "count": count,
        }
    )

    if isinstance(result, GenerationOutput):
        return result.items
    return []


def repair_cypher(schema_text: str, question: str, cypher: str, error: str) -> str:
    model = get_model()
    chain = REPAIR_PROMPT | model
    response = chain.invoke(
        {
            "schema": schema_text,
            "question": question,
            "cypher": cypher,
            "error": error,
        }
    )
    return (getattr(response, "content", "") or "").strip()


def validate_and_repair(items: List[QuestionCypherItem], schema_text: str, max_repair_rounds: int = 2) -> List[QuestionCypherItem]:
    fixed_items: List[QuestionCypherItem] = []

    for item in items:
        current = item.expected_cypher.strip()
        question = item.question.strip()

        if not current:
            continue

        if validate_cypher(current):
            fixed_items.append(QuestionCypherItem(question=question, expected_cypher=current))
            continue

        last_error = "Validation failed"
        repaired = current
        for _ in range(max_repair_rounds):
            repaired = repair_cypher(schema_text=schema_text, question=question, cypher=repaired, error=last_error)
            if not repaired:
                break
            if validate_cypher(repaired):
                fixed_items.append(QuestionCypherItem(question=question, expected_cypher=repaired))
                break

        # Keep original if still invalid, so user can inspect manually.
        if len(fixed_items) == 0 or fixed_items[-1].question != question:
            fixed_items.append(QuestionCypherItem(question=question, expected_cypher=current))

    return fixed_items


def to_json_list(items: List[QuestionCypherItem]) -> List[dict]:
    return [
        {
            "question": item.question,
            "expected_cypher": item.expected_cypher,
        }
        for item in items
    ]


def save_output(data: List[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate useful question-cypher pairs from schema and guide")
    parser.add_argument("--count", type=int, default=20, help="Number of pairs to generate")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH, help="Path to schema text file")
    parser.add_argument("--guide", type=Path, default=DEFAULT_GUIDE_PATH, help="Path to question guide text file")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON file path")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated Cypher against Neo4j (and try repair)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.count <= 0:
        raise ValueError("--count must be > 0")

    schema_text = read_text(args.schema)
    guide_text = read_text(args.guide)

    items = generate_pairs(schema_text=schema_text, guide_text=guide_text, count=args.count)

    if args.validate:
        items = validate_and_repair(items=items, schema_text=schema_text)

    payload = to_json_list(items)

    output_path = args.output
    if output_path is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = DEFAULT_OUTPUT_DIR / f"generated_question_cypher_{stamp}.json"

    save_output(payload, output_path)

    print(f"Generated {len(payload)} items")
    print(f"Output: {output_path}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
