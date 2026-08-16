from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document


class ParentStore:
    """Small transactional SQLite store for parent Documents.

    The application writes only its own generated JSON payloads here; no untrusted
    LangChain object deserialization is used.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS parents (
                    parent_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )"""
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_parents_source ON parents(source_id)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def replace_source(self, source_id: str, parents: Iterable[tuple[str, Document]]) -> None:
        rows = [
            (parent_id, source_id, doc.page_content, json.dumps(doc.metadata, ensure_ascii=False))
            for parent_id, doc in parents
        ]
        with self._connect() as conn:
            conn.execute("DELETE FROM parents WHERE source_id = ?", (source_id,))
            conn.executemany(
                "INSERT INTO parents(parent_id, source_id, content, metadata_json) VALUES (?, ?, ?, ?)",
                rows,
            )

    def delete_source(self, source_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM parents WHERE source_id = ?", (source_id,))

    def get(self, parent_id: str) -> Document | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT content, metadata_json FROM parents WHERE parent_id = ?",
                (parent_id,),
            ).fetchone()
        if not row:
            return None
        return Document(page_content=row[0], metadata=json.loads(row[1]))

    def get_many(self, parent_ids: list[str]) -> dict[str, Document]:
        if not parent_ids:
            return {}
        placeholders = ",".join("?" for _ in parent_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT parent_id, content, metadata_json FROM parents WHERE parent_id IN ({placeholders})",
                parent_ids,
            ).fetchall()
        return {
            row[0]: Document(page_content=row[1], metadata=json.loads(row[2]))
            for row in rows
        }

    def list_documents(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT source_id, metadata_json, COUNT(*) 
                   FROM parents 
                   GROUP BY source_id"""
            ).fetchall()
        docs = []
        for source_id, metadata_json, parents_count in rows:
            meta = json.loads(metadata_json) if metadata_json else {}
            docs.append({
                "source_id": source_id,
                "source_name": meta.get("source_name", "Unknown"),
                "parents": parents_count,
                "status": "indexed",
            })
        return docs
