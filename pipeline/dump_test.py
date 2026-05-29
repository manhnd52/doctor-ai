from langchain_core.messages import HumanMessage, AIMessage
from graph_builder import build_graph
from services.graph.utils import init_graph
from dotenv import load_dotenv
import os
import warnings

warnings.filterwarnings(
    "ignore",
    message=r"Pydantic serializer warnings:.*",
    category=UserWarning,
    module=r"pydantic\.main",
)

def main():
    # 1. Load environment variables
    load_dotenv()
    
    # Ensure standard env credentials exist
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")
    
    print(f"Connecting to Neo4j database at: {neo4j_uri} as user: {neo4j_user}...")
    
    # 2. Initialize Neo4j Graph
    init_graph(url=neo4j_uri, username=neo4j_user, password=neo4j_password)
    
    # 3. Compile the full graph (intent_resolving -> classification -> pipeline/LLM -> answer_generation)
    print("Compiling full LangGraph pipeline...")
    app = build_graph(evaluate=False)
    
    # 4. Construct a conversation context with an ambiguous latest query
    context = [
        HumanMessage(content="I’ve been feeling very tired lately and drinking a lot of water."),
        AIMessage(content="Those symptoms could be associated with conditions like diabetes. Common signs include increased thirst, frequent urination, fatigue, and weight loss."),
        HumanMessage(content="If it is that, what should I do next?")
    ]
    
    print("\n--- Prepared Input Context ---")
    print("Conversation History:")
    for msg in context[:-1]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        print(f"  {role}: {msg.content}")
    print(f"Ambiguous Latest Query: {context[-1].content}")
    print("------------------------------\n")
    
    # The state expects context history.
    # We populate both 'question' and 'context' keys.
    initial_state = {
        "question": context[-1].content,
        "context": context
    }
    
    print("Running the pipeline graph...")
    # Invoke the compiled graph
    final_state = app.invoke(initial_state)
    
    print("\n--- Pipeline Execution Output ---")
    print("1. Rewritten Standalone Question (intent_resolving node):")
    print(f"   => {final_state.get('question')}")
    
    print("\n2. Question Classification:")
    print(f"   => {final_state.get('question_type')}")
    
    print("\n3. Generated Cypher Query:")
    print(f"   => {final_state.get('cypher')}")
    
    print("\n4. Query Result from Database:")
    print(f"   => {final_state.get('query_result')}")
    
    print("\n5. Final Generated Answer:")
    print(f"   => {final_state.get('answer')}")
    
    print("\n6. Executed Steps in Graph:")
    print(f"   => {final_state.get('steps')}")
    print("---------------------------------\n")

if __name__ == "__main__":
    main()