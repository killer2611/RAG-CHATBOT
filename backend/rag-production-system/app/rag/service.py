from __future__ import annotations

import asyncio
import logging
import sqlite3
from collections import defaultdict
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from app.core.config import Settings
from app.models.schemas import ChatResponse, SourceCitation
from app.rag.models import build_chat_model, build_evaluation_model
from app.rag.prompts import qa_messages, rewrite_messages
from app.rag.retriever import HierarchicalRetriever

logger = logging.getLogger(__name__)


class HistoryStore:
    def __init__(self, settings: Settings) -> None:
        from langchain_community.chat_message_histories.sql import SQLChatMessageHistory

        self._history_cls = SQLChatMessageHistory
        self._db_url = settings.database_url
        self._max_messages = settings.history_max_messages
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _history(self, session_id: str):
        return self._history_cls(
            session_id=session_id,
            connection=self._db_url,
            async_mode=True,
        )

    async def get(self, session_id: str) -> list[BaseMessage]:
        history = self._history(session_id)
        messages = await history.aget_messages()
        return messages[-self._max_messages:]

    async def get_messages(self, session_id: str) -> list[dict]:
        messages = await self.get(session_id)
        result = []
        for msg in messages:
            role = "user" if msg.type == "human" else "assistant" if msg.type == "ai" else "system"
            result.append({"role": role, "content": str(msg.content)})
        return result

    async def list_sessions(self) -> list[dict]:
        db_path_str = self._db_url
        for prefix in ["sqlite+aiosqlite:///", "sqlite:///"]:
            if db_path_str.startswith(prefix):
                db_path_str = db_path_str[len(prefix):]
                break

        path = Path(db_path_str)
        if not path.exists():
            return []

        def _query():
            try:
                with sqlite3.connect(path, timeout=5) as conn:
                    cur = conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='message_store'"
                    )
                    if not cur.fetchone():
                        return []

                    rows = conn.execute(
                        "SELECT session_id, count(*), max(id) "
                        "FROM message_store GROUP BY session_id "
                        "ORDER BY max(id) DESC"
                    ).fetchall()

                    return [
                        {"session_id": str(r[0]), "message_count": int(r[1])}
                        for r in rows
                    ]
            except Exception as exc:
                logger.warning("Failed to query sessions: %s", exc)
                return []

        return await asyncio.to_thread(_query)

    async def append(self, session_id: str, messages: list[BaseMessage]) -> None:
        await self._history(session_id).aadd_messages(messages)

    def lock(self, session_id: str) -> asyncio.Lock:
        return self._locks[session_id]


class RagService:
    def __init__(
        self,
        settings: Settings,
        retriever: HierarchicalRetriever,
        history: HistoryStore,
    ) -> None:
        self.settings = settings
        self.retriever = retriever
        self.history = history

        # Normal chat model. This may be Groq.
        self.llm = build_chat_model(settings)

        # Evaluation model is separate and lazy-loaded.
        # It can NEVER accidentally reuse self.llm.
        self._evaluation_llm = None

    def _get_evaluation_llm(self):
        if self._evaluation_llm is None:
            logger.info(
                "Initializing evaluation generation model: %s",
                self.settings.eval_generation_model,
            )
            self._evaluation_llm = build_evaluation_model(self.settings)
        return self._evaluation_llm

    async def _standalone_question(
        self,
        user_input: str,
        history: list[BaseMessage],
        llm=None,
    ) -> str:
        if not history:
            return user_input

        model = llm or self.llm
        response = await model.ainvoke(
            rewrite_messages(history, user_input)
        )
        return str(response.content).strip()

    def _context(self, retrieved) -> str:
        blocks = []
        for index, item in enumerate(retrieved, start=1):
            doc = item.document
            blocks.append(
                f"[Document {index}] source={doc.metadata.get('source_name', '')} "
                f"page={doc.metadata.get('page', 'n/a')}\n{doc.page_content}"
            )
        return "\n\n".join(blocks)

    async def answer_with_context(
        self,
        session_id: str,
        user_input: str,
        *,
        evaluation: bool = False,
    ):
        if evaluation:
            # HARD SEPARATION:
            # evaluation generation does not use normal chat history
            # and does not use the normal Groq/Gemini/Ollama model.
            llm = self._get_evaluation_llm()

            question = user_input
            retrieved = await asyncio.to_thread(
                self.retriever.retrieve,
                question,
            )

            response = await llm.ainvoke(
                qa_messages(question, self._context(retrieved))
            )

            answer = str(response.content).strip()

            logger.info(
                "Evaluation answer generated via DeepSeek: %s",
                self.settings.eval_generation_model,
            )

            return answer, retrieved

        history = await self.history.get(session_id)
        question = await self._standalone_question(
            user_input,
            history,
            llm=self.llm,
        )
        retrieved = await asyncio.to_thread(
            self.retriever.retrieve,
            question,
        )
        response = await self.llm.ainvoke(
            qa_messages(question, self._context(retrieved))
        )
        return str(response.content).strip(), retrieved

    async def answer(self, session_id: str, user_input: str) -> ChatResponse:
        async with self.history.lock(session_id):
            history = await self.history.get(session_id)
            question = await self._standalone_question(
                user_input,
                history,
                llm=self.llm,
            )
            retrieved = await asyncio.to_thread(
                self.retriever.retrieve,
                question,
            )
            response = await self.llm.ainvoke(
                qa_messages(question, self._context(retrieved))
            )
            answer = str(response.content).strip()

            await self.history.append(
                session_id,
                [
                    HumanMessage(content=user_input),
                    AIMessage(content=answer),
                ],
            )

            sources = [
                SourceCitation(**s)
                for s in self.retriever.sources_for(retrieved)
            ]

            return ChatResponse(
                session_id=session_id,
                answer=answer,
                sources=sources,
            )

    async def stream(self, session_id: str, user_input: str):
        lock = self.history.lock(session_id)
        await lock.acquire()

        try:
            history = await self.history.get(session_id)
            question = await self._standalone_question(
                user_input,
                history,
                llm=self.llm,
            )
            retrieved = await asyncio.to_thread(
                self.retriever.retrieve,
                question,
            )

            sources = [
                SourceCitation(**s)
                for s in self.retriever.sources_for(retrieved)
            ]
            yield {
                "event": "sources",
                "data": [s.model_dump() for s in sources],
            }

            chunks: list[str] = []
            async for chunk in self.llm.astream(
                qa_messages(question, self._context(retrieved))
            ):
                text = str(chunk.content or "")
                if text:
                    chunks.append(text)
                    yield {"event": "token", "data": text}

            answer = "".join(chunks).strip()

            await self.history.append(
                session_id,
                [
                    HumanMessage(content=user_input),
                    AIMessage(content=answer),
                ],
            )

            yield {
                "event": "done",
                "data": {"session_id": session_id},
            }
        finally:
            lock.release()
