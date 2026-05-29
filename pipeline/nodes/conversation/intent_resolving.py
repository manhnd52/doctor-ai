from services.llm_service import get_model
from helper import convert_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pipeline_state import GraphState

def intent_resolving_node(state : GraphState):
    messages = state.get("context", [])
    question = resolve_real_intent(messages) # From context, resolve real desirse
    return {
        "question": question
    }

def resolve_real_intent(messages: list[BaseMessage]) -> str:
    llm = get_model()

    last_user_message = None
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_user_message = m
            break

    if not last_user_message:
        return ""

    history_messages = []
    found_last = False

    for m in reversed(messages):
        if m == last_user_message and not found_last:
            found_last = True
            continue

        if found_last:
            history_messages.append(m)

    history_messages.reverse()

    history_str = ""

    for m in history_messages:
        role = "USER" if isinstance(m, HumanMessage) else "ASSISTANT"
        history_str += f"{role}: {m.content}\n"

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are a medical query rewriting system.

Your task is to rewrite the user's latest message into a fully standalone,
explicit medical question using the previous conversation context.

If user question is casual, unrelated, you should return the latest user message unchanged.

Rules:
- Preserve the original medical intent exactly.
- Resolve ambiguous references like:
  - "it"
  - "this disease"
  - "that medicine"
  - "those symptoms"
  - "this condition"
- Include the exact disease, symptom, treatment, medication,
  body part, or medical condition referenced earlier.
- Keep medically relevant context only.
- Do NOT answer the question.
- Do NOT add medical advice.
- Do NOT invent symptoms, diseases, or treatments.
- Do NOT change the user's meaning.
- Keep the rewritten question concise but explicit.
- If user message is already standalone, return it unchanged.

Output only the rewritten question.
"""
        ),
        (
            "human",
            """
Conversation history:
{history}

Latest user message:
{question}

Rewritten standalone medical question:
"""
        )
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "history": history_str,
        "question": last_user_message.content
    })

if __name__ == "__main__":
    messages = [
        HumanMessage(content="Hello, how are you?"),
        AIMessage(content="I'm fine, thank you."),
        HumanMessage(content="What are the symptoms of diabetes?"),
        AIMessage(content="Diabetes is a disease that affects how your body uses blood sugar."),
        HumanMessage(content="Hi")
    ]
    result = resolve_real_intent(messages)
    print(result)