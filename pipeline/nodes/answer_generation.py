from services.llm_service import get_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

TOKEN_LIMIT = 100000
FIRST_N = 100

def answer_generation_node(state):
    if state.get("question_type") == "LLM":
        model = get_model()
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are a helpful assistant that answers questions based on the user's input. 
            If the user has not provided enough information to answer the question, respond with "I cannot answer that question based on the provided information."
            """),
            ("human", """
                Question:
                {question}

                Answer:
             """)
        ])
        question_val = state.get("question")
        if not question_val and state.get("context"):
            question_val = state["context"][-1].content
        chain = prompt | model | StrOutputParser()
        if question_val:
            answer = chain.invoke({
                "question": question_val
            })
        else:
            answer = "I can't answer that question based on the provided information."
        return {"answer": answer, "steps": ["answer_generation"]}
    
    query_result = state.get("query_result", "")
    if len(str(state.get("query_result", ""))) > TOKEN_LIMIT:
        query_result = reduce_query_result(state["query_result"])
    answer = generate_answer(
        question=state["question"],
        generated_cypher=state.get("cypher", ""),
        query_result=query_result
    )
    return {"answer": answer, "steps": ["answer_generation"]}

def generate_answer(question, generated_cypher, query_result):
    model = get_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are a question answering assistant.

        You are given:
        - a user question
        - a Cypher query used to retrieve data
        - the query result from a knowledge graph

        IMPORTANT:
        - The query result is raw data, NOT a final answer
        - You must interpret and synthesize the answer
        - Do NOT copy the data verbatim

        Instructions:
        - Extract only relevant information
        - Combine it into a natural answer
        - If multiple results exist, summarize them clearly
        - If data is empty or insufficient, say you cannot answer

        Keep the answer concise and accurate.
        """),
        ("human", """
            Question:
            {question}

            Cypher Query:
            {cypher}

            Query Result:
            {data}

            Answer:
         """)
    ])
    chain = prompt | model | StrOutputParser()
    answer = chain.invoke({
        "question": question,
        "cypher": generated_cypher,
        "data": query_result
    })
    return answer

def reduce_query_result(query_result):
    # Implement a simple reduction strategy, e.g., take the first N items or summarize
    if isinstance(query_result, list):
        return query_result[:FIRST_N]  # Take only the first N results for simplicity
    return query_result  

if __name__ == "__main__":
    # Example usage
    question = "What are the symptoms of diabetes?"
    generated_cypher = "MATCH (d:Disease {name: 'diabetes'})-[:HAS_SYMPTOM]->(s:Symptom) RETURN s.name"
    query_result = "Symptoms of diabetes include increased thirst, frequent urination, hunger, fatigue, and blurred vision."
    print(generate_answer(question, generated_cypher, query_result))