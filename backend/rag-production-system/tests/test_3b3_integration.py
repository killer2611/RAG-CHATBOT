"""
Phase 3B-3 Integration Tests.

Covers:
    A. ProvenanceResolver.get_page_count()
    B. evidence_scope derivation
    C. corpus_position derivation
    D. Corpus-global fields are absent from partial candidates
    E. PartialBenchmarkCandidate typed representation
    F. Staged schema validation (partial != complete BenchmarkCase)
    G. 3B/3C boundary (no verification, no support_status)
    H. Identity continuity (case_id, evidence_id, claim_id)
"""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.evaluation.candidates import PartialBenchmarkCandidate, PartialRetrievalProfile
from app.evaluation.generator_v3 import (
    BatchCandidateOutput,
    CandidateGenerator,
    CandidateOutput,
    ClaimOutput,
)
from app.evaluation.profiler import ProfilerResult
from app.evaluation.provenance import DocumentNotFoundError, ProvenanceResolver

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SINGLE_PAGE_TEXT = "The sky is blue. Water is wet. Gravity pulls things down."
SINGLE_PAGE_HASH = hashlib.sha256(SINGLE_PAGE_TEXT.encode("utf-8")).hexdigest()

# Six-page synthetic document fixture: each "page" is a distinct PDF-like
# section written as a separate LangChain Document.
# We use a plain text file for determinism and rely on the txt loader which
# returns one Document per file.  To test multi-page behaviour, we need the
# loader to return multiple Documents.  We achieve this by creating a
# multi-element fixture that monkey-patches _extract_source_text.
MULTI_PAGE_CONTENT = "\n".join(f"Page {i} content." for i in range(1, 7))
MULTI_PAGE_HASH = hashlib.sha256(MULTI_PAGE_CONTENT.encode("utf-8")).hexdigest()


@pytest.fixture
def single_page_dir():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / f"{SINGLE_PAGE_HASH}.txt"
        p.write_text(SINGLE_PAGE_TEXT, encoding="utf-8")
        yield Path(tmp)


@pytest.fixture
def multi_page_dir():
    with tempfile.TemporaryDirectory() as tmp:
        content_bytes = MULTI_PAGE_CONTENT.encode("utf-8")
        actual_hash = hashlib.sha256(content_bytes).hexdigest()
        p = Path(tmp) / f"{actual_hash}.txt"
        p.write_bytes(content_bytes)
        # expose the actual hash so tests can use it
        yield Path(tmp), actual_hash


@pytest.fixture
def resolver_single(single_page_dir):
    return ProvenanceResolver(document_dir=single_page_dir)


@pytest.fixture
def resolver_multi(multi_page_dir):
    tmp_path, doc_hash = multi_page_dir
    return ProvenanceResolver(document_dir=tmp_path), doc_hash


@pytest.fixture
def profiler_result():
    return ProfilerResult(document_type="technical-research", type_confidence=0.95)


def _build_candidate(
    quote="The sky is blue.",
    answerability="answerable",
    num_quotes=1,
):
    quotes = [quote] * num_quotes
    claims = [
        ClaimOutput(claim="The sky has a blue color.", evidence_indices=[0])
    ] if answerability == "answerable" else []
    return CandidateOutput(
        question="What colour is the sky?",
        expected_answer="Blue.",
        answerability=answerability,
        question_type="factual",
        topics=["Science"],
        proposed_evidence=quotes,
        claims=claims,
    )


def _mock_llm(candidate: CandidateOutput):
    llm = MagicMock()
    structured_llm = AsyncMock()
    structured_llm.ainvoke.return_value = BatchCandidateOutput(candidates=[candidate])
    llm.with_structured_output.return_value = structured_llm
    return llm


# ===========================================================================
# A. ProvenanceResolver.get_page_count()
# ===========================================================================

class TestGetPageCount:
    def test_txt_returns_0(self, resolver_single):
        count = resolver_single.get_page_count(SINGLE_PAGE_HASH)
        # TXT files have no reliable physical page structure, so it returns 0
        assert count == 0

    def test_repeated_calls_are_deterministic(self, resolver_single):
        c1 = resolver_single.get_page_count(SINGLE_PAGE_HASH)
        c2 = resolver_single.get_page_count(SINGLE_PAGE_HASH)
        assert c1 == c2

    def test_missing_document_raises(self, single_page_dir):
        resolver = ProvenanceResolver(document_dir=single_page_dir)
        with pytest.raises(DocumentNotFoundError):
            resolver.get_page_count("0" * 64)

    def test_hash_mismatch_raises(self, single_page_dir):
        """Tamper: write correct file but name it with a wrong hash."""
        wrong_hash = "a" * 64
        path = single_page_dir / f"{wrong_hash}.txt"
        path.write_text("tampered content", encoding="utf-8")
        resolver = ProvenanceResolver(document_dir=single_page_dir)
        with pytest.raises(DocumentNotFoundError):
            resolver.get_page_count(wrong_hash)

    def test_pdf_physical_page_count_with_blank_pages(self, single_page_dir, monkeypatch):
        import hashlib

        # Create a dummy PDF
        pdf_path = single_page_dir / "dummy.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n...")
        pdf_hash = hashlib.sha256(b"%PDF-1.4\n...").hexdigest()

        # Rename it to its hash
        hashed_path = single_page_dir / f"{pdf_hash}.pdf"
        pdf_path.rename(hashed_path)

        resolver = ProvenanceResolver(document_dir=single_page_dir)

        # Mock pypdf to pretend the PDF has 10 physical pages (even if 2 are blank)
        class MockPage:
            pass
        class MockReader:
            def __init__(self, *args, **kwargs):
                self.pages = [MockPage() for _ in range(10)]

        monkeypatch.setattr("pypdf.PdfReader", MockReader)

        count = resolver.get_page_count(pdf_hash)
        assert count == 10


# ===========================================================================
# B. evidence_scope derivation
# ===========================================================================

@pytest.mark.asyncio
async def test_evidence_scope_single_span(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate(quote="The sky is blue.", num_quotes=1))
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1
    rp = results[0].retrieval_profile
    assert rp.evidence_scope == "single_span"


@pytest.mark.asyncio
async def test_evidence_scope_multi_span(resolver_single, profiler_result):
    """Two distinct quoted spans in the same document."""
    candidate = CandidateOutput(
        question="What are two facts?",
        expected_answer="Sky is blue. Water is wet.",
        answerability="answerable",
        question_type="factual",
        topics=["Science"],
        proposed_evidence=["The sky is blue.", "Water is wet."],
        claims=[
            ClaimOutput(claim="Sky colour.", evidence_indices=[0]),
        ],
    )
    llm = _mock_llm(candidate)
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    # The two quotes are distinct, so they get distinct span_hashes.
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1
    assert results[0].retrieval_profile.evidence_scope == "multi_span"


@pytest.mark.asyncio
async def test_evidence_scope_duplicate_quote(resolver_single, profiler_result, monkeypatch):
    """Two identical quotes should resolve to the same span_hash and thus single_span."""
    candidate = CandidateOutput(
        question="What is a fact?",
        expected_answer="Sky is blue.",
        answerability="answerable",
        question_type="factual",
        topics=["Science"],
        # Same quote proposed twice
        proposed_evidence=["The sky is blue.", "The sky is blue."],
        claims=[
            ClaimOutput(claim="Sky colour.", evidence_indices=[0, 1]),
        ],
    )
    llm = _mock_llm(candidate)
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)

    assert len(results) == 1
    rp = results[0].retrieval_profile
    # Because span_hash is identical, it's considered a single distinct canonical span
    assert rp.evidence_scope == "single_span"


# ===========================================================================
# C. corpus_position derivation
# ===========================================================================

class TestCorpusPositionDerivation:
    def _gen(self, resolver):
        return CandidateGenerator(
            llm=MagicMock(), provenance_resolver=resolver
        )

    def _fake_ev(self, page):
        return {"page": page, "quote": "x", "span_hash": "y", "evidence_id": "z", "section": None}

    def test_start_page_returns_start(self, resolver_single):
        gen = self._gen(resolver_single)
        pos = gen._derive_corpus_position([self._fake_ev(1)], total_pages=9, full_text="")
        assert pos == "start"

    def test_middle_page_returns_middle(self, resolver_single):
        gen = self._gen(resolver_single)
        pos = gen._derive_corpus_position([self._fake_ev(5)], total_pages=9, full_text="")
        assert pos == "middle"

    def test_last_page_returns_end(self, resolver_single):
        gen = self._gen(resolver_single)
        pos = gen._derive_corpus_position([self._fake_ev(9)], total_pages=9, full_text="")
        assert pos == "end"

    def test_no_page_metadata_and_quote_not_found_returns_none(self, resolver_single):
        gen = self._gen(resolver_single)
        ev_no_page = {"page": None, "quote": "needle", "span_hash": "y", "evidence_id": "z", "section": None}

        # Text does not contain "needle"
        full_text = "0123456789.........................................................................................."
        pos = gen._derive_corpus_position([ev_no_page], total_pages=9, full_text=full_text)
        assert pos is None

    def test_no_page_metadata_returns_none(self, resolver_single):
        gen = self._gen(resolver_single)
        ev_no_page = {"page": None, "quote": "needle", "span_hash": "y", "evidence_id": "z", "section": None}
        full_text = "0123456789needle...................................................................................."
        pos = gen._derive_corpus_position([ev_no_page], total_pages=9, full_text=full_text)
        assert pos is None

    def test_zero_total_pages_returns_none(self, resolver_single):
        gen = self._gen(resolver_single)
        ev = {"page": 1, "quote": "needle", "span_hash": "y", "evidence_id": "z", "section": None}
        full_text = "................................................................................needle.........."
        # Since total_pages = 0, fallback is prohibited
        pos = gen._derive_corpus_position([ev], total_pages=0, full_text=full_text)
        assert pos is None

    def test_deterministic_across_calls(self, resolver_single):
        gen = self._gen(resolver_single)
        ev = [self._fake_ev(3)]
        p1 = gen._derive_corpus_position(ev, 12, full_text="")
        p2 = gen._derive_corpus_position(ev, 12, full_text="")
        assert p1 == p2


# ===========================================================================
# D. Corpus-global fields are absent
# ===========================================================================

@pytest.mark.asyncio
async def test_corpus_global_fields_absent(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1
    d = results[0].to_dict()
    rp = d["retrieval_profile"]
    assert "distractor_profile" not in rp, "distractor_profile must be absent from 3B output"
    assert "retrieval_risk" not in rp, "retrieval_risk must be absent from 3B output"


# ===========================================================================
# E. PartialBenchmarkCandidate typed representation
# ===========================================================================

@pytest.mark.asyncio
async def test_return_type_is_partial_candidate(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1
    result = results[0]
    assert isinstance(result, PartialBenchmarkCandidate), (
        "generate_candidates must return PartialBenchmarkCandidate objects, not plain dicts"
    )
    assert isinstance(result.retrieval_profile, PartialRetrievalProfile)


@pytest.mark.asyncio
async def test_partial_candidate_not_a_plain_dict(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert not isinstance(results[0], dict), (
        "PartialBenchmarkCandidate must not be returned as a plain dict at the 3B boundary"
    )


# ===========================================================================
# F. Staged schema validation
# ===========================================================================

@pytest.mark.asyncio
async def test_partial_candidate_fails_frozen_schema_validation(resolver_single, profiler_result):
    """
    A PartialBenchmarkCandidate must NOT pass the frozen BenchmarkCase schema.
    This proves the partial/complete distinction is enforced.
    """
    import jsonschema
    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    if not schema_path.exists():
        pytest.skip("Frozen schema not found")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(results[0].to_dict(), schema)


@pytest.mark.asyncio
async def test_completed_case_passes_frozen_schema_validation(resolver_single, profiler_result):
    """
    A completed BenchmarkCase (all required fields populated) must pass the frozen schema.
    This validates the schema is intact and the partial/complete distinction is correct.
    """
    import jsonschema
    schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "Phase 3" / "benchmark_case.schema.json"
    if not schema_path.exists():
        pytest.skip("Frozen schema not found")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1
    partial = results[0]

    # Simulate downstream corpus-enrichment and 3C verification adding the missing fields.
    completed = partial.to_dict()
    completed["claims"][0]["support_status"] = "supported"
    completed["retrieval_profile"]["corpus_position"] = "start"
    completed["retrieval_profile"]["distractor_profile"] = "none"
    completed["retrieval_profile"]["retrieval_risk"] = "low"
    completed["verification"] = {
        "verdict": "accepted",
        "primary": {
            "verdict": "accepted",
            "claims_checked": [completed["claims"][0]["claim_id"]],
        },
        "secondary": None,
        "human_review": None,
    }

    # This must now pass.
    jsonschema.validate(completed, schema)


# ===========================================================================
# G. 3B/3C boundary — no verification, no support_status for answerable
# ===========================================================================

@pytest.mark.asyncio
async def test_no_support_status_for_answerable_claims(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate(answerability="answerable"))
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1
    for claim in results[0].claims:
        assert "support_status" not in claim


@pytest.mark.asyncio
async def test_hollow_verification_block_exists(resolver_single, profiler_result):
    """
    3B must not perform semantic verification, but the verification key must exist
    as an explicitly hollow/stub object on the serialized candidate.
    """
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)

    assert len(results) == 1
    d = results[0].to_dict()

    assert "verification" in d
    v = d["verification"]

    assert v["verdict"] is None
    assert "verified_by" not in v
    assert "unsupported_claims" not in v
    assert "contradictions" not in v
    assert "reason" not in v


@pytest.mark.asyncio
async def test_no_verifier_import_invoked(resolver_single, profiler_result, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "deepeval", None)
    monkeypatch.setitem(sys.modules, "app.evaluation.verifier", None)

    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert len(results) == 1  # succeeds without any verifier


# ===========================================================================
# H. Identity continuity
# ===========================================================================

@pytest.mark.asyncio
async def test_case_id_present(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert results[0].case_id.startswith("case-")


@pytest.mark.asyncio
async def test_evidence_id_present(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert results[0].evidence[0]["evidence_id"].startswith("ev-")


@pytest.mark.asyncio
async def test_claim_id_present(resolver_single, profiler_result):
    llm = _mock_llm(_build_candidate())
    gen = CandidateGenerator(llm=llm, provenance_resolver=resolver_single)
    results = await gen.generate_candidates(SINGLE_PAGE_HASH, profiler_result, budget=1)
    assert results[0].claims[0]["claim_id"].startswith("claim-")
