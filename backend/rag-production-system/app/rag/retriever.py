from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder

from app.core.config import Settings
from app.rag.storage import ParentStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    document: Document
    score: float


class HierarchicalRetriever:
    """Persistent child-vector retrieval -> parent expansion -> BGE reranking."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )
        self.vector_store = Chroma(
            collection_name="rag_children",
            persist_directory=str(settings.vector_store_dir),
            embedding_function=self.embeddings,
        )
        self.parent_store = ParentStore(settings.parent_store_db)
        reranker_kwargs = {}
        if settings.reranker_device:
            reranker_kwargs["device"] = settings.reranker_device
        self.reranker = CrossEncoder(settings.reranker_model, **reranker_kwargs)

        # RecursiveCharacterTextSplitter normally operates on characters. The contribution
        # document expresses its tuning in tokens, so use the tiktoken-backed splitter.
        self.parent_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=settings.parent_chunk_size,
            chunk_overlap=settings.parent_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.child_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=settings.child_chunk_size,
            chunk_overlap=settings.child_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @staticmethod
    def _parent_id(source_id: str, parent_index: int, content: str) -> str:
        digest = hashlib.sha256(f"{source_id}:{parent_index}:{content}".encode()).hexdigest()
        return f"p_{digest[:32]}"

    @staticmethod
    def _child_id(parent_id: str, child_index: int, content: str) -> str:
        digest = hashlib.sha256(f"{parent_id}:{child_index}:{content}".encode()).hexdigest()
        return f"c_{digest[:32]}"

    def ingest(self, documents: list[Document], source_id: str, source_name: str) -> tuple[int, int]:
        if not documents:
            raise ValueError("No extractable text found in the uploaded document")

        parents: list[tuple[str, Document]] = []
        children: list[Document] = []
        child_ids: list[str] = []
        for source_doc_index, source_doc in enumerate(documents):
            parent_docs = self.parent_splitter.split_documents([source_doc])
            for parent_index, parent in enumerate(parent_docs):
                parent_id = self._parent_id(
                    source_id,
                    source_doc_index * 100000 + parent_index,
                    parent.page_content,
                )
                parent.metadata.update(
                    {"source_id": source_id, "source_name": source_name, "parent_id": parent_id}
                )
                parents.append((parent_id, parent))
                for child_index, child in enumerate(self.child_splitter.split_documents([parent])):
                    child_id = self._child_id(parent_id, child_index, child.page_content)
                    child.metadata.update(
                        {
                            "source_id": source_id,
                            "source_name": source_name,
                            "parent_id": parent_id,
                            "child_id": child_id,
                            "page": parent.metadata.get("page"),
                        }
                    )
                    children.append(child)
                    child_ids.append(child_id)

        # Best-effort atomic replacement across vector DB + parent store.
        self.vector_store.delete(where={"source_id": source_id})
        self.parent_store.delete_source(source_id)
        try:
            self.parent_store.replace_source(source_id, parents)
            self.vector_store.add_documents(children, ids=child_ids)
        except Exception:
            self.vector_store.delete(where={"source_id": source_id})
            self.parent_store.delete_source(source_id)
            raise

        logger.info(
            "Indexed source=%s parents=%s children=%s",
            source_id,
            len(parents),
            len(children),
        )
        return len(parents), len(children)

    def retrieve(self, query: str) -> list[RetrievedDocument]:
        candidates = self.vector_store.similarity_search(query, k=self.settings.retrieval_k)
        parent_ids: list[str] = []
        for child in candidates:
            pid = child.metadata.get("parent_id")
            if pid and pid not in parent_ids:
                parent_ids.append(pid)
        parent_map = self.parent_store.get_many(parent_ids)
        parents = [parent_map[pid] for pid in parent_ids if pid in parent_map]
        if not parents:
            return []

        pairs = [(query, doc.page_content) for doc in parents]
        scores = [float(score) for score in self.reranker.predict(pairs)]
        ranked = sorted(zip(parents, scores), key=lambda item: item[1], reverse=True)
        return [RetrievedDocument(document=doc, score=float(score)) for doc, score in ranked[: self.settings.rerank_top_n]]

    def sources_for(self, retrieved: Iterable[RetrievedDocument]) -> list[dict]:
        result = []
        for item in retrieved:
            doc = item.document
            result.append(
                {
                    "source_id": doc.metadata.get("source_id", ""),
                    "source_name": doc.metadata.get("source_name", ""),
                    "page": doc.metadata.get("page"),
                    "parent_id": doc.metadata.get("parent_id", ""),
                    "score": item.score,
                    "excerpt": doc.page_content[:500].replace("\n", " "),
                }
            )
        return result
