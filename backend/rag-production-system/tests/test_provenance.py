import hashlib
import tempfile
from pathlib import Path
import pytest

from langchain_core.documents import Document

from app.evaluation.provenance import (
    ProvenanceResolver,
    QuoteNotFoundError,
    DocumentNotFoundError,
    ProvenanceResult,
)

# Test Data
DUMMY_SOURCE_TEXT = "This is the original source text. It contains a specific quote that we will search for."
DUMMY_HASH = hashlib.sha256(DUMMY_SOURCE_TEXT.encode("utf-8")).hexdigest()

@pytest.fixture
def mock_document_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        # Create a dummy .txt file that simulates an ingested file saved by routes_ingest.py
        # using its document_hash as the filename.
        doc_path = tmp_path / f"{DUMMY_HASH}.txt"
        doc_path.write_text(DUMMY_SOURCE_TEXT, encoding="utf-8")
        yield tmp_path

@pytest.fixture
def resolver(mock_document_dir):
    return ProvenanceResolver(document_dir=mock_document_dir)


# ============================================================================
# P1 & P3: VERIFY DOCUMENT IDENTITY AGAINST RAW BYTES
# ============================================================================
def test_document_identity_from_raw_bytes_success(resolver):
    # The document_hash must match the actual SHA-256 of the raw file bytes
    quote = "original source text"
    result = resolver.resolve_quote(DUMMY_HASH, quote)
    assert result.quote == quote

def test_document_identity_mismatched_bytes_rejected(mock_document_dir, resolver):
    # Create a file whose name suggests a hash, but its contents do not match
    fake_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    fake_path = mock_document_dir / f"{fake_hash}.txt"
    fake_path.write_text("This content does not hash to the fake hash.", encoding="utf-8")

    with pytest.raises(DocumentNotFoundError, match="Document content hash mismatch"):
        resolver.resolve_quote(fake_hash, "some quote")


# ============================================================================
# P2: CHUNK-INDEPENDENCE / RETRIEVED-TEXT BOUNDARY
# ============================================================================
def test_chunk_independence_and_retrieved_text_boundary(resolver):
    # Simulate a hypothetical retrieval system yielding different chunk boundaries.

    # Chunking Strategy A: Broad chunk
    hypothetical_chunk_a = "It contains a specific quote that we will search for. And more text."

    # Chunking Strategy B: Tight chunk
    hypothetical_chunk_b = "a specific quote that we will search for."

    # In both retrieval contexts, a candidate generator extracts the same canonical quote:
    def extract_canonical_quote(chunk: str) -> str:
        target = "specific quote that we will search for."
        if target in chunk:
            return target
        raise ValueError("Failed to extract target quote from chunk")

    quote_from_a = extract_canonical_quote(hypothetical_chunk_a)
    quote_from_b = extract_canonical_quote(hypothetical_chunk_b)

    # We pass only the derived quote and the original document hash to the resolver,
    # NOT the chunk ID, and NOT the retrieved chunk text.
    result_a = resolver.resolve_quote(DUMMY_HASH, quote_from_a)
    result_b = resolver.resolve_quote(DUMMY_HASH, quote_from_b)

    assert result_a.span_hash == result_b.span_hash
    assert result_a.quote == result_b.quote
    assert result_a.span_hash == hashlib.sha256(b"specific quote that we will search for.").hexdigest()
    # This demonstrates that different chunk boundaries cannot affect provenance
    # as long as the derived quote can be resolved against the original source text.


# ============================================================================
# P4 & P5: CROSS-PAGE PROVENANCE TESTS & SOURCE/PAGE METADATA
# ============================================================================
def test_single_page_quote(resolver):
    quote = "specific quote that we will search for."
    result = resolver.resolve_quote(DUMMY_HASH, quote)

    assert isinstance(result, ProvenanceResult)
    assert result.quote == quote
    expected_hash = hashlib.sha256(quote.encode("utf-8")).hexdigest()
    assert result.span_hash == expected_hash
    assert result.source_name == f"{DUMMY_HASH}.txt"
    # For .txt files loaded via load_file, there's no page metadata, so it's None
    assert result.page is None

@pytest.fixture
def mock_multipage_resolver(mock_document_dir, monkeypatch):
    def fake_load_file(path):
        return [
            Document(page_content="This is page one.\nIt contains part of", metadata={"source_name": path.name, "page": 1}),
            Document(page_content=" the quote.\nAnd this is page two.", metadata={"source_name": path.name, "page": 2})
        ]
    monkeypatch.setattr("app.evaluation.provenance.load_file", fake_load_file)
    return ProvenanceResolver(document_dir=mock_document_dir)

def test_cross_page_quote(mock_multipage_resolver):
    # Quote spanning page 1 and page 2
    quote = "part of\n the quote."
    result = mock_multipage_resolver.resolve_quote(DUMMY_HASH, quote)

    assert result.quote == quote
    assert result.page is None  # Cross-page quote correctly returns None
    assert result.source_name == f"{DUMMY_HASH}.txt"

def test_superficially_equivalent_quote_fails(resolver):
    # Contains extra whitespace not present in original.
    # This documents the current STRICT normalization behavior (Open Decision #5).
    resembling_quote = "This is the original  source text."
    with pytest.raises(QuoteNotFoundError, match="Quote not found"):
        resolver.resolve_quote(DUMMY_HASH, resembling_quote)


# ============================================================================
# P6: DUPLICATE-QUOTE BEHAVIOR
# ============================================================================
@pytest.fixture
def mock_duplicate_resolver(mock_document_dir, monkeypatch):
    def fake_load_file(path):
        return [
            Document(page_content="Duplicate quote here.", metadata={"source_name": path.name, "page": 1}),
            Document(page_content="Duplicate quote here.", metadata={"source_name": path.name, "page": 2})
        ]
    monkeypatch.setattr("app.evaluation.provenance.load_file", fake_load_file)
    return ProvenanceResolver(document_dir=mock_document_dir)

def test_duplicate_quote_resolves_to_first_occurrence(mock_duplicate_resolver):
    quote = "Duplicate quote here."
    result = mock_duplicate_resolver.resolve_quote(DUMMY_HASH, quote)

    # Current behavior resolves the first matching occurrence
    assert result.page == 1


# ============================================================================
# ADDITIONAL BASELINE TESTS
# ============================================================================
def test_quote_does_not_exist(resolver):
    quote = "This quote is nowhere to be found in the document."
    with pytest.raises(QuoteNotFoundError, match="Quote not found"):
        resolver.resolve_quote(DUMMY_HASH, quote)

def test_determinism(resolver):
    quote = "original source text"
    results = [resolver.resolve_quote(DUMMY_HASH, quote) for _ in range(5)]
    first_hash = results[0].span_hash
    for r in results:
        assert r.span_hash == first_hash

@pytest.mark.parametrize("empty_quote", ["", "   ", "\n\n"])
def test_empty_malformed_quote(resolver, empty_quote):
    with pytest.raises(QuoteNotFoundError, match="Proposed quote is empty"):
        resolver.resolve_quote(DUMMY_HASH, empty_quote)

def test_document_not_found(resolver):
    fake_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    with pytest.raises(DocumentNotFoundError, match="Document with hash"):
        resolver.resolve_quote(fake_hash, "some quote")
