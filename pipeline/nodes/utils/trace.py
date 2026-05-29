import json
import os
import uuid

def build_trace_node():
    def node(state):
        os.makedirs("checkpoints", exist_ok=True)
        file_name = f"checkpoints/{uuid.uuid4().hex}.json"
        with open(file_name, "w") as f:
            json.dump(state, f, indent=2)
        return {}
    return node
