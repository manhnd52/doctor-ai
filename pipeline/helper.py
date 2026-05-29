import json
import re
from flatten_json import flatten
import json
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
 
def pretty_print(data, max_depth=4, max_items=15, max_str_len=300):
    def truncate(obj, depth=0):
        if depth > max_depth:
            return "..."

        if isinstance(obj, dict):
            return {
                k: truncate(v, depth + 1)
                for i, (k, v) in enumerate(obj.items())
                if i < max_items
            }

        if isinstance(obj, list):
            return [
                truncate(v, depth + 1)
                for v in obj[:max_items]
            ]

        if isinstance(obj, str):
            return obj[:max_str_len] + ("..." if len(obj) > max_str_len else "")

        return obj

    trimmed = truncate(data)
    print(json.dumps(trimmed, indent=2, ensure_ascii=False))

def pretty_print_flattened(data):
    flattened = None
    if isinstance(data, list):
        flattened = [flatten(item) for item in data]
    elif isinstance(data, dict):
        flattened = flatten(data)
    print(json.dumps(flattened, indent=2, ensure_ascii=False))

def to_flatten(data):
    if isinstance(data, list):
        return [flatten(item) for item in data]
    elif isinstance(data, dict):
        return flatten(data)
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")
    
def normalize_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = text.replace("\\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
    
def convert_messages(rows: list[dict]) -> list[BaseMessage]:
    messages = []

    for row in rows:
        role = row.role.lower()
        if role == "user":
            messages.append(HumanMessage(content=row.content))

        elif role == "assistant":
            messages.append(AIMessage(content=row.content))

    return messages