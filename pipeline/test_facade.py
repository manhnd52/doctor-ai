import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# SETUP CONFIGURATION (Credentials loaded from env with fallbacks)
# ==========================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678")
TEST_QUESTION = "What are the symptoms of diabetes?"
RUN_PIPELINE = True  # Set to False if you only want to test database connection
# ==========================================

# Import the facade under test
from facade import PipelineFacade, Message
import services.graph.utils as graph_utils


def test_neo4j_integration():
    print("==================================================")
    print(" NEO4J INTEGRATION & PIPELINE TEST")
    print("==================================================")
    print(f"Connecting to Neo4j at: {NEO4J_URI}")
    print(f"Username: {NEO4J_USER}")
    print("--------------------------------------------------")

    try:
        # 1. Initialize PipelineFacade with the credentials
        facade = PipelineFacade(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD
        )
        print("[OK] Facade initialized successfully.")

        # 2. Test direct Neo4j connection via a simple Cypher query
        graph = graph_utils.get_graph()
        print("Testing direct query connectivity...")
        start_time = time.perf_counter()
        test_result = graph.query("RETURN 1 AS val")
        elapsed = time.perf_counter() - start_time
        print(f"[OK] Neo4j query executed successfully in {elapsed:.4f}s. Result: {test_result}")
        print("[OK] Neo4j connection is verified and healthy!")

    except Exception as e:
        print(f"[ERROR] Failed to connect or execute test query on Neo4j: {e}")
        return False

    if not RUN_PIPELINE:
        print("\nSkipping full pipeline execution test (RUN_PIPELINE = False).")
        return True

    # 3. Test running standard pipeline execution
    print("\n--------------------------------------------------")
    print(f"Testing standard pipeline execution with: '{TEST_QUESTION}'")
    print("--------------------------------------------------")
    try:
        print("Streaming pipeline nodes:")
        start_time = time.perf_counter()
        step_count = 0
        for chunk in facade.stream_by_node([Message(role="USER", content=TEST_QUESTION)]):
            step_count += 1
            node_name = list(chunk.keys())[0]
            print(f"  [Node {step_count}] Completed: {node_name}")

        elapsed = time.perf_counter() - start_time
        print(f"[OK] Pipeline streamed successfully in {elapsed:.4f}s.")

        print("\nRunning pipeline direct invocation...")
        start_time = time.perf_counter()
        result = facade.run([Message(role="USER", content=TEST_QUESTION)])
        elapsed = time.perf_counter() - start_time
        print(f"[OK] Pipeline run executed successfully in {elapsed:.4f}s.")
        print(f"Final Answer: {result.get('answer', 'No answer key in result')}")

    except Exception as e:
        print(f"[ERROR] Standard pipeline execution encountered an error: {e}")
        return False

    # 4. Test running context-aware pipeline execution (ambiguous query)
    print("\n--------------------------------------------------")
    print("Testing context-aware pipeline execution (Ambiguous Query)")
    print("--------------------------------------------------")
    try:
        context = [
            Message(role="USER", content="What are the symptoms of diabetes?"),
            Message(role="ASSISTANT", content="Symptoms of diabetes include increased thirst, frequent urination, fatigue, and weight loss.")
        ]
        ambiguous_question = "How is it treated?"
        
        print("Conversation History:")
        for msg in context:
            print(f"  {msg.role.capitalize()}: {msg.content}")
        print(f"Latest Ambiguous Query: {ambiguous_question}")
        print("------------------------------")
        
        print("Running pipeline direct invocation with context...")
        start_time = time.perf_counter()
        full_context = context + [Message(role="USER", content=ambiguous_question)]
        result = facade.run(full_context)
        elapsed = time.perf_counter() - start_time
        
        print(f"[OK] Context pipeline run executed successfully in {elapsed:.4f}s.")
        print(f"Rewritten Question: {result.get('question')}")
        print(f"Final Answer: {result.get('answer', 'No answer key in result')}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Context pipeline execution encountered an error: {e}")
        return False


if __name__ == "__main__":
    success = test_neo4j_integration()
    sys.exit(0 if success else 1)
