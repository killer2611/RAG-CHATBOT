from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

GROUNDED_ABSTENTION = "I do not have enough information to answer this based on the provided documents."

REWRITE_SYSTEM = """Given the chat history and the latest user question, rewrite the latest question into a standalone question.
Do not answer it. Preserve the user's intent and named entities. If the latest question is already standalone, return it unchanged."""

QA_SYSTEM = f"""You are a factual RAG assistant.
Answer ONLY using the supplied document context.
Do not use outside knowledge, assumptions, extrapolation, or invented citations.
If the context does not fully support an answer, respond exactly with:
{GROUNDED_ABSTENTION}
Keep the answer direct and concise.
"""


def rewrite_messages(history: list[BaseMessage], user_input: str) -> list[BaseMessage]:
    return [SystemMessage(content=REWRITE_SYSTEM), *history, HumanMessage(content=user_input)]


def qa_messages(question: str, context: str) -> list[BaseMessage]:
    return [
        SystemMessage(content=QA_SYSTEM),
        HumanMessage(content=f"Question:\n{question}\n\nDocument context:\n{context}"),
    ]
