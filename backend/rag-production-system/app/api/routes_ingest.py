from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_retriever
from app.core.config import get_settings
from app.models.schemas import DocumentSummary, IngestResponse
from app.rag.loaders import load_file
from app.rag.retriever import HierarchicalRetriever

router = APIRouter(tags=["ingest"])


@router.get("/documents", response_model=list[DocumentSummary])
async def list_documents(retriever: HierarchicalRetriever = Depends(get_retriever)):
    docs = await asyncio.to_thread(retriever.parent_store.list_documents)
    return [DocumentSummary(**d) for d in docs]


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...), retriever: HierarchicalRetriever = Depends(get_retriever)):
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".docx"}:
        raise HTTPException(status_code=415, detail="Only PDF, TXT and DOCX are supported")

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")

    digest = hashlib.sha256(data).hexdigest()
    source_name = Path(file.filename or "upload").name
    stored_path = Path("data/documents") / f"{digest}{suffix}"
    was_existing = stored_path.exists()
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(data)

    try:
        docs = await asyncio.to_thread(load_file, stored_path)
        parents, children = await asyncio.to_thread(
            retriever.ingest, docs, digest, source_name
        )
    except Exception as exc:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    return IngestResponse(
        source_id=digest,
        source_name=source_name,
        documents=len(docs),
        parents=parents,
        children=children,
        status="replaced" if was_existing else "indexed",
    )
