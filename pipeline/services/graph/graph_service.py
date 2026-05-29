from services.graph.utils import search_entity

class GraphService:
    def find_best_match(self, entity_text: str, label):
        return {"name": entity_text}

    def validate(self, cypher: str) -> bool:
        # TODO: EXPLAIN query
        return True

    def run(self, cypher: str):
        # TODO: execute query
        return [{"mock": 1}, {"mock": 2}]