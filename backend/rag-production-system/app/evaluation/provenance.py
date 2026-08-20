import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from app.rag.loaders import load_file


@dataclass
class ProvenanceResult:
    """
    Represents the canonical evidence span resolved against the ORIGINAL SOURCE TEXT.
    """
    quote: str
    span_hash: str
    source_name: Optional[str]
    page: Optional[int]


class DocumentNotFoundError(Exception):
    pass


class QuoteNotFoundError(Exception):
    pass


class ProvenanceResolver:
    """
    Local, deterministic provenance infrastructure.

    This component implements the provenance boundary:
    ORIGINAL BYTES -> document identity -> ORIGINAL SOURCE TEXT -> exact quote -> span_hash

    It intentionally DOES NOT implement:
    - Truth verification
    - Candidate generation
    - Retrieval evaluation
    """

    def __init__(self, document_dir: str | Path = "data/documents"):
        self.document_dir = Path(document_dir)

    def _find_document_path(self, document_hash: str) -> Path:
        """
        Locates the authoritative original file bytes based on document_hash.
        """
        if not self.document_dir.exists():
            raise DocumentNotFoundError(f"Document directory {self.document_dir} does not exist.")

        for p in self.document_dir.glob(f"{document_hash}.*"):
            if p.is_file():
                actual_bytes = p.read_bytes()
                actual_hash = hashlib.sha256(actual_bytes).hexdigest()
                if actual_hash != document_hash:
                    raise DocumentNotFoundError(
                        f"Document content hash mismatch for {p.name}. "
                        f"Expected {document_hash}, got {actual_hash}."
                    )
                return p

        raise DocumentNotFoundError(f"Document with hash {document_hash} not found in {self.document_dir}.")

    def _extract_source_text(self, document_path: Path) -> list[Document]:
        """
        Re-extracts the original source text from the raw bytes.
        """
        return load_file(document_path)

    def get_source_context(self, document_hash: str) -> tuple[str, str]:
        """
        Public boundary to retrieve the full original source text and name.
        """
        doc_path = self._find_document_path(document_hash)
        pages = self._extract_source_text(doc_path)
        full_text = "\n\n".join(p.page_content for p in pages)
        return full_text, doc_path.name

    def get_page_count(self, document_hash: str) -> int:
        """
        Returns the total number of physical source pages in the authoritative document.

        Uses the same cryptographic identity check and loader path as resolve_quote()
        and get_source_context(). Introduces zero LLM/embedding calls.

        For PDFs, returns the exact physical page count (including unextractable pages).
        For TXT/DOCX, returns 0 as page structure is unavailable.
        """
        doc_path = self._find_document_path(document_hash)

        if doc_path.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(doc_path))
            return len(reader.pages)

        # For TXT/DOCX, page structure is unavailable. Return 0 so
        # the generator falls back to the deterministic string-index.
        return 0

    def resolve_quote(self, document_hash: str, proposed_quote: str) -> ProvenanceResult:
        """
        Resolves a proposed quote against the original source text.

        NOTE ON DUPLICATE QUOTES:
        If the exact same quote appears multiple times in the source document,
        this implementation resolves the first matching occurrence.
        Occurrence-level disambiguation (e.g., offsets) is not part of the current schema.

        NOTE ON NORMALIZATION (OPEN DECISION #5 - NOT RESOLVED):
        This implementation currently enforces strict exact-substring matching.
        It does not implement fuzzy matching, whitespace normalization, or Unicode normalization,
        because the exact evidence-overlap algorithm and normalization policy remains unresolved.
        """
        if not proposed_quote or not proposed_quote.strip():
            raise QuoteNotFoundError("Proposed quote is empty.")

        doc_path = self._find_document_path(document_hash)
        pages = self._extract_source_text(doc_path)

        # provisional exact normalization boundary (subject to Open Decision #5)
        normalized_quote = proposed_quote.strip()

        # 1. Try single page match (preserves precise page metadata)
        for page in pages:
            if normalized_quote in page.page_content:
                # CANONICAL EVIDENCE SPAN BOUNDARY
                # The exact hashing policy for evidence is subject to Open Decision #5.
                # CURRENT PROVISIONAL BEHAVIOR: SHA-256 of the UTF-8 encoded stripped exact quote.
                span_hash = hashlib.sha256(normalized_quote.encode("utf-8")).hexdigest()
                return ProvenanceResult(
                    quote=normalized_quote,
                    span_hash=span_hash,
                    source_name=page.metadata.get("source_name"),
                    page=page.metadata.get("page")
                )

        # 2. Try cross-page match (for PDF text crossing page boundaries)
        # Note: PDF extraction may introduce newlines/spaces between pages.
        # Strict exact matching across pages may fail if the extraction introduces artifacts.
        # This highlights the open nature of Decision #5.
        combined_text = "\n".join(p.page_content for p in pages)
        if normalized_quote in combined_text:
            # CURRENT PROVISIONAL BEHAVIOR: SHA-256 of the UTF-8 encoded stripped exact quote.
            span_hash = hashlib.sha256(normalized_quote.encode("utf-8")).hexdigest()
            return ProvenanceResult(
                quote=normalized_quote,
                span_hash=span_hash,
                source_name=pages[0].metadata.get("source_name") if pages else None,
                page=None  # Quote spans multiple pages
            )

        raise QuoteNotFoundError(
            f"Quote not found in original source document {document_hash}. "
            "Note: Exact substring matching is currently enforced (Open Decision #5)."
        )
