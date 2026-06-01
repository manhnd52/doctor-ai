from app.kg_connection.models import KnowledgeGraph
from app.auth.models import User
from neo4j import GraphDatabase, Session

class KGSessionManager:
    def __init__(self):
        self._cache = {} # Cache to store active sessions keyed by connection ID

    def get_session(self, connection: KnowledgeGraph) -> Session:
        if not connection:
            raise Exception("No active KG connection found.")
        
        if connection.id in self._cache:
            return self._cache[connection.id]

        session = self._create_kg_session(connection)

        self._cache[connection.id] = session

        return session
    
    def validate(self, connection: KnowledgeGraph) -> dict | None:
        """
        Check connection to the knowledge graph and return the number of nodes and relationships.
        """
        try:
            session = self._create_kg_session(connection)
            print("Testing connection to KG...")
            result = session.run("MATCH (n) WITH count(n) AS nodeCount MATCH ()-[r]->() RETURN nodeCount, count(r) AS relationshipCount")  # Test the connection
            result_data = result.single()
            return result_data
        except Exception as e:
            print(f"Connect info: {connection.uri}, {connection.database_name}, {connection.username}")
            print(f"Failed to connect to KG: {str(e)}")
            return None

    def _create_kg_session(self, connection: KnowledgeGraph):
        driver = GraphDatabase.driver(
            connection.uri,
            auth=(connection.username, connection.password)
        )
        return driver.session(database=connection.database_name)
    
    def close_session(self, connection_id: int):
        session = self._cache.pop(connection_id, None)
        if session:
            session.close()

    
    