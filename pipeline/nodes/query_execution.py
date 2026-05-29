from services.graph import get_graph as get_graph_service
import re

def query_execution_node(state):
    graph = get_graph_service()
    cypher = state.get("cypher", "")
    try:
        result = graph.query(cypher)    
    except Exception as e:
        result = []
        print(f"Error executing Cypher query: {e}")
        print(state)

    return {
        "query_result": result,
        "metrics": {
            **state.get("metrics", {}),
            "result_count": len(result)
        }
    }

