import json
import logging
from typing import Protocol, List
from pydantic import BaseModel, Field

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import Settings
from app.rag.models import build_evaluation_generation_model

logger = logging.getLogger(__name__)

class ProfilerResult(BaseModel):
    document_type: str = Field(
        ...,
        description="One of: legal, policy, technical-research, manual, narrative, tabular, general"
    )
    type_confidence: float = Field(
        ...,
        description="Confidence score between 0.0 and 1.0"
    )


class DocumentProfiler(Protocol):
    async def profile(self, documents: List[Document]) -> ProfilerResult:
        ...


class LLMDocumentProfiler:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def profile(self, documents: List[Document]) -> ProfilerResult:
        if not documents:
            return ProfilerResult(document_type="general", type_confidence=0.0)

        # Extract up to a reasonable number of characters to avoid token limits
        text_chunks = []
        char_count = 0
        for doc in documents:
            text = doc.page_content.strip()
            if text:
                text_chunks.append(text)
                char_count += len(text)
                if char_count > 10000:
                    break

        full_text = "\n\n".join(text_chunks)[:10000]

        if not full_text.strip():
            return ProfilerResult(document_type="general", type_confidence=0.0)

        system_prompt = """You are a highly analytical document profiler.
Your task is to classify the provided document text into exactly ONE of the following 7 categories:
1. legal: contracts, agreements, statutes, regulations, legal filings, clauses and formal legal obligations.
2. policy: organizational policies, institutional rules, governance policies, compliance policies, procedural policy documents.
3. technical-research: scientific papers, engineering reports, research publications, experiments, technical analyses.
4. manual: user manuals, operating instructions, setup guides, troubleshooting guides.
5. narrative: prose-dominant narrative documents, reports organized as continuous narrative.
6. tabular: documents whose primary information structure is tables, structured datasets/reports.
7. general: insufficient evidence, mixed/general documents, low-confidence classifications.

You must reply with ONLY a valid JSON object containing exactly two keys:
- "document_type": A string (one of: legal, policy, technical-research, manual, narrative, tabular, general).
- "type_confidence": A float between 0.0 and 1.0 representing your confidence in this classification.

Do not output any markdown formatting, reasoning, or extra text. Just the JSON object.
"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"DOCUMENT TEXT:\n{full_text}")
            ])

            content = str(response.content).strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
            doc_type = data.get("document_type", "general")
            confidence = float(data.get("type_confidence", 0.0))

        except Exception as e:
            logger.warning(f"Profiler LLM failed or returned invalid JSON: {e}")
            doc_type = "general"
            confidence = 0.0

        # Validate against taxonomy
        valid_types = {
            "legal", "policy", "technical-research", "manual",
            "narrative", "tabular", "general"
        }
        if doc_type not in valid_types:
            doc_type = "general"

        # Constrain confidence
        confidence = max(0.0, min(1.0, confidence))

        # EXACT CONFIDENCE GATE: strictly less than 0.60
        if confidence < 0.60:
            doc_type = "general"

        return ProfilerResult(document_type=doc_type, type_confidence=confidence)


def build_document_profiler(settings: Settings | None = None) -> DocumentProfiler:
    """Factory to build the Phase 3A profiler using the dedicated evaluation model."""
    llm = build_evaluation_generation_model(settings)
    return LLMDocumentProfiler(llm=llm)
