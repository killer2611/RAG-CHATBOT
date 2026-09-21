import hashlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.evaluation.generator_v3 import (
    CandidateGenerator,
    BatchCandidateOutput,
    CandidateOutput,
    ClaimOutput,
    STRATEGY_TEMPLATES
)
from app.evaluation.profiler import ProfilerResult
from app.evaluation.provenance import ProvenanceResolver

# Test Data
DUMMY_SOURCE_TEXT = "The sky is blue. Water is wet. Gravity pulls things down."
DUMMY_HASH = hashlib.sha256(DUMMY_SOURCE_TEXT.encode("utf-8")).hexdigest()

@pytest.fixture
def mock_document_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_path = Path(temp_dir)
        doc_path = tmp_path / f"{DUMMY_HASH}.txt"
        doc_path.write_text(DUMMY_SOURCE_TEXT, encoding="utf-8")
        yield tmp_path

@pytest.fixture
def provenance_resolver(mock_document_dir):
    return ProvenanceResolver(document_dir=mock_document_dir)

@pytest.fixture
def profiler_result():
    return ProfilerResult(document_type="technical-research", type_confidence=0.95)

def build_valid_candidate(idx: int, answerability="answerable") -> CandidateOutput:
    return CandidateOutput(
        question=f"Question {idx}",
        expected_answer="The sky is blue.",
        answerability=answerability,
        question_type="factual",
        topics=["Science"],
        proposed_evidence=["The sky is blue."],
        claims=[
            ClaimOutput(
                claim="The sky has a blue color.",
                evidence_indices=[0],
                rationale="Directly stated."
            )
        ]
    )

def build_mock_llm(candidates_per_call: int = 5):
    llm = MagicMock()
    structured_llm = AsyncMock()

    async def mock_ainvoke(*args, **kwargs):
        return BatchCandidateOutput(
            candidates=[build_valid_candidate(i) for i in range(candidates_per_call)]
        )

    structured_llm.ainvoke.side_effect = mock_ainvoke
    llm.with_structured_output.return_value = structured_llm
    return llm

# A. COST & G. BUDGET (HARDENING #3 & CORRECTION 1)
def test_generator_initialization(provenance_resolver):
    llm = MagicMock()
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    llm.with_structured_output.assert_called_once_with(
        BatchCandidateOutput,
        method="json_mode"
    )

@pytest.mark.asyncio
async def test_budget_cost_and_prompt_request(provenance_resolver, profiler_result):
    llm = build_mock_llm(5)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)

    # 5 candidates -> 1 call requesting exactly 5
    await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=5)
    assert generator.structured_llm.ainvoke.call_count == 1
    system_prompt = generator.structured_llm.ainvoke.call_args[0][0][0].content
    assert "Generate exactly 5 candidate cases." in system_prompt
    generator.structured_llm.ainvoke.reset_mock()

    # 7 candidates -> 2 calls (first requests 5, second requests 2)
    llm = build_mock_llm(5)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=7)
    assert generator.structured_llm.ainvoke.call_count == 2
    prompt_1 = generator.structured_llm.ainvoke.call_args_list[0][0][0][0].content
    prompt_2 = generator.structured_llm.ainvoke.call_args_list[1][0][0][0].content
    assert "Generate exactly 5 candidate cases." in prompt_1
    assert "Generate exactly 2 candidate cases." in prompt_2

    # 30 candidates -> 6 calls, each <= 5
    llm = build_mock_llm(5)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=30)
    assert generator.structured_llm.ainvoke.call_count == 6
    for call_obj in generator.structured_llm.ainvoke.call_args_list:
        sys_msg = call_obj[0][0][0].content
        assert "Generate exactly 5 candidate cases." in sys_msg

@pytest.mark.asyncio
async def test_budget_accounting_with_dropped_candidates(provenance_resolver, profiler_result):
    # CORRECTION 1: Mock deliberately returns FEWER candidates than requested.
    # We request 5, but mock returns only 2 valid ones.
    # Total budget = 7. Next batch should request exactly 2 (the remaining generation budget),
    # NOT 7 - 2 = 5 (the remaining accepted cases).
    llm = build_mock_llm(2)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)

    await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=7)

    assert generator.structured_llm.ainvoke.call_count == 2
    prompt_1 = generator.structured_llm.ainvoke.call_args_list[0][0][0][0].content
    prompt_2 = generator.structured_llm.ainvoke.call_args_list[1][0][0][0].content

    assert "Generate exactly 5 candidate cases." in prompt_1
    # Next call must only request 2, since 5 generation attempts were already spent.
    assert "Generate exactly 2 candidate cases." in prompt_2


# B. TOKEN COST GUARD (HARDENING #4)
@pytest.mark.asyncio
async def test_token_cost_sends_full_text_once_per_batch(provenance_resolver, profiler_result):
    llm = build_mock_llm(2)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    # Budget=10 with MAX=5 -> 2 loop iterations
    await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=10)
    assert generator.structured_llm.ainvoke.call_count == 2

    # Assert exactly ONE source text inclusion per batch call
    for call_obj in generator.structured_llm.ainvoke.call_args_list:
        human_msg = call_obj[0][0][1].content
        assert human_msg.startswith("DOCUMENT TEXT:\n")
        assert DUMMY_SOURCE_TEXT in human_msg


# C. DOCUMENT TYPE ROUTING (HARDENING #2)
@pytest.mark.asyncio
async def test_document_type_routing(provenance_resolver):
    llm = build_mock_llm(1)

    # legal
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    res_legal = ProfilerResult(document_type="legal", type_confidence=0.99)
    await generator.generate_candidates(DUMMY_HASH, res_legal, budget=1)
    sys_msg = generator.structured_llm.ainvoke.call_args[0][0][0].content
    assert STRATEGY_TEMPLATES["legal"] in sys_msg

    # tabular
    generator.structured_llm.ainvoke.reset_mock()
    res_tab = ProfilerResult(document_type="tabular", type_confidence=0.99)
    await generator.generate_candidates(DUMMY_HASH, res_tab, budget=1)
    sys_msg = generator.structured_llm.ainvoke.call_args[0][0][0].content
    assert STRATEGY_TEMPLATES["tabular"] in sys_msg


# D. NO SELF GRADING / NON-VERIFYING (HARDENING #1, #7 & CORRECTION 2)
@pytest.mark.asyncio
async def test_3b_is_not_verifier_strict(provenance_resolver, profiler_result, monkeypatch):
    # CORRECTION 2: Explicitly forbid importing deepeval or a verification module
    import sys
    monkeypatch.setitem(sys.modules, "deepeval", None)
    monkeypatch.setitem(sys.modules, "app.evaluation.verifier", None)

    llm = build_mock_llm(1)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)

    # Generate an answerable candidate
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)
    assert len(results) == 1
    case = results[0]

    # 3B does not output support_status for answerable claims (no self grading)
    claim = case.claims[0]
    assert "support_status" not in claim

    # 3B does not perform verification, but outputs a hollow verification stub
    d = case.to_dict()
    assert "verification" in d
    assert d["verification"]["verdict"] is None
    # retrieval_profile IS now present (source-local fields populated by 3B-3)
    assert "retrieval_profile" in d

    # Prove only the generation LLM mock was called exactly once,
    # meaning no hidden LLM verification calls happened.
    assert generator.structured_llm.ainvoke.call_count == 1


@pytest.mark.asyncio
async def test_h12_unanswerable_semantics(provenance_resolver, profiler_result):
    llm = build_mock_llm(1)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)

    # Override mock to return unanswerable
    async def mock_unanswerable(*args, **kwargs):
        return BatchCandidateOutput(
            candidates=[build_valid_candidate(0, answerability="unanswerable")]
        )
    generator.structured_llm.ainvoke.side_effect = mock_unanswerable

    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)
    assert len(results) == 1
    case = results[0]

    claim = case.claims[0]
    # For unanswerable, it explicitly assigns not_applicable to pass H-12 structural checks
    assert claim.get("support_status") == "not_applicable"


# E. INVALID BUDGETS
@pytest.mark.asyncio
async def test_invalid_budgets(provenance_resolver, profiler_result):
    llm = build_mock_llm(5)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)

    with pytest.raises(ValueError, match="budget must be positive"):
        await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=0)

    with pytest.raises(ValueError, match="exceeds hard maximum"):
        await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=31)


# F. UNRESOLVED QUOTE DROPPED (HARDENING #6 compatibility check)
@pytest.mark.asyncio
async def test_unresolved_quote_dropped(provenance_resolver, profiler_result):
    llm = MagicMock()
    structured_llm = AsyncMock()

    bad_prov_candidate = build_valid_candidate(0)
    bad_prov_candidate.proposed_evidence = ["This text is absolutely nowhere in the source document."]

    structured_llm.ainvoke.return_value = BatchCandidateOutput(candidates=[bad_prov_candidate])
    llm.with_structured_output.return_value = structured_llm

    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)

    # Dropped locally because provenance resolution failed
    assert len(results) == 0


# G. CARDINALITY ENFORCEMENT FIREWALL
@pytest.mark.asyncio
async def test_cardinality_firewall_valid_exact(provenance_resolver, profiler_result):
    llm = build_mock_llm(5) # returns 5
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=5)
    # requested=5, returned=5 -> 5 accepted
    assert len(results) == 5
    assert generator.structured_llm.ainvoke.call_count == 1

@pytest.mark.asyncio
async def test_cardinality_firewall_valid_underproduced(provenance_resolver, profiler_result):
    llm = build_mock_llm(2) # returns 2
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=5)
    # requested=5, returned=2 -> 2 accepted, no retry
    assert len(results) == 2
    assert generator.structured_llm.ainvoke.call_count == 1

@pytest.mark.asyncio
async def test_cardinality_firewall_invalid_overproduced(provenance_resolver, profiler_result):
    llm = build_mock_llm(6) # returns 6
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=5)
    # requested=5, returned=6 -> entire batch rejected.
    assert len(results) == 0
    # No compensating call is made because budget tracking counts the 5 generation attempts
    assert generator.structured_llm.ainvoke.call_count == 1

@pytest.mark.asyncio
async def test_cardinality_firewall_invalid_overproduced_small_budget(provenance_resolver, profiler_result):
    llm = build_mock_llm(3) # returns 3
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=2)
    # requested=2, returned=3 -> entire batch rejected.
    assert len(results) == 0
    assert generator.structured_llm.ainvoke.call_count == 1


# H. MULTI-BATCH REGRESSION AND BOUNDARY TESTS
@pytest.mark.asyncio
async def test_cardinality_firewall_multi_batch_regression(provenance_resolver, profiler_result):
    llm = MagicMock()
    structured_llm = AsyncMock()

    # Mock sequence: first call returns 6, second call returns 5.
    async def mock_ainvoke(*args, **kwargs):
        call_num = structured_llm.ainvoke.call_count
        if call_num == 1:
            return BatchCandidateOutput(
                candidates=[build_valid_candidate(i) for i in range(6)]
            )
        else:
            return BatchCandidateOutput(
                candidates=[build_valid_candidate(i) for i in range(5)]
            )

    structured_llm.ainvoke.side_effect = mock_ainvoke
    llm.with_structured_output.return_value = structured_llm

    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=10)

    # Batch 1 (requested=5, returned=6) -> rejected
    # Batch 2 (requested=5, returned=5) -> accepted
    assert len(results) == 5
    assert generator.structured_llm.ainvoke.call_count == 2

    prompt_1 = generator.structured_llm.ainvoke.call_args_list[0][0][0][0].content
    prompt_2 = generator.structured_llm.ainvoke.call_args_list[1][0][0][0].content

    assert "Generate exactly 5 candidate cases." in prompt_1
    assert "Generate exactly 5 candidate cases." in prompt_2


@pytest.mark.asyncio
async def test_provenance_existence_without_semantic_verification(provenance_resolver, profiler_result, monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "deepeval", None)
    monkeypatch.setitem(sys.modules, "app.evaluation.verifier", None)

    spy_resolve = MagicMock(wraps=provenance_resolver.resolve_quote)
    monkeypatch.setattr(provenance_resolver, "resolve_quote", spy_resolve)

    llm = build_mock_llm(1)
    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)

    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)
    assert len(results) == 1
    case = results[0]

    # 1. ProvenanceResolver is called and produces an evidence object
    spy_resolve.assert_called_once()
    assert len(case.evidence) == 1

    # 2. The claim does NOT receive a support_status
    claim = case.claims[0]
    assert "support_status" not in claim

    # 3. Hollow verification stub is produced
    assert "verification" in case.to_dict()
    assert case.to_dict()["verification"]["verdict"] is None

    # 4. No additional LLM calls
    assert generator.structured_llm.ainvoke.call_count == 1


# I. SCHEMA COMPATIBILITY AND VERSIONING
@pytest.mark.asyncio
async def test_version_field_presence_and_schema_validation(provenance_resolver, profiler_result):
    import json
    import jsonschema
    from app.core.config import get_settings

    settings = get_settings()
    original_sv = settings.phase3_schema_version
    original_bv = settings.phase3_benchmark_version
    original_gpv = settings.phase3_generator_prompt_version
    original_vpv = settings.phase3_verifier_prompt_version

    try:
        # 1. Modify configuration to prove the generator doesn't use hardcoded literals
        settings.phase3_schema_version = "9.9-test"
        settings.phase3_benchmark_version = "custom-benchmark-version"
        settings.phase3_generator_prompt_version = "gen-v1"
        settings.phase3_verifier_prompt_version = "ver-v2"

        llm = build_mock_llm(1)
        generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
        results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)

        assert len(results) == 1
        candidate = results[0]

        # 2. Assert version exists and uses the config-backed values
        assert hasattr(candidate, "version")
        version = candidate.version
        assert version["schema_version"] == "9.9-test"
        assert version["benchmark_version"] == "custom-benchmark-version"
        assert version["generator_prompt_version"] == "gen-v1"
        assert version["verifier_prompt_version"] == "ver-v2"

        # 3. Hollow verification block exists; retrieval_profile IS present (source-local fields)
        d = candidate.to_dict()
        assert "verification" in d
        assert d["verification"]["verdict"] is None
        assert "retrieval_profile" in d

        # 4. Validate against frozen schema (after completing downstream fields)
        schema_path = Path("docs/Phase 3/benchmark_case.schema.json")
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

            # To validate the schema properly, we must complete the case as
            # PartialBenchmarkCandidate is intentionally schema-invalid at this boundary.
            completed = dict(d)
            completed["claims"][0]["support_status"] = "supported"
            completed["retrieval_profile"]["corpus_position"] = "start"
            completed["retrieval_profile"]["distractor_profile"] = "none"
            completed["retrieval_profile"]["retrieval_risk"] = "low"
            completed["verification"] = {
                "verdict": "accepted",
                "primary": {
                    "verdict": "accepted",
                    "claims_checked": [completed["claims"][0]["claim_id"]],
                    "unsupported_claims": [],
                    "reason": "Because"
                },
                "secondary": None,
                "human_review": None,
            }

            jsonschema.validate(instance=completed, schema=schema)
    finally:
        # Restore configuration
        settings.phase3_schema_version = original_sv
        settings.phase3_benchmark_version = original_bv
        settings.phase3_generator_prompt_version = original_gpv
        settings.phase3_verifier_prompt_version = original_vpv


# J. ZERO-CLAIM SEMANTICS
@pytest.mark.asyncio
async def test_answerable_zero_claims_rejected(provenance_resolver, profiler_result):
    llm = MagicMock()
    structured_llm = AsyncMock()

    bad_candidate = build_valid_candidate(0, answerability="answerable")
    bad_candidate.claims = [] # Zero claims!

    structured_llm.ainvoke.return_value = BatchCandidateOutput(candidates=[bad_candidate])
    llm.with_structured_output.return_value = structured_llm

    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)

    # Answerable + zero claims -> rejected locally
    assert len(results) == 0

@pytest.mark.asyncio
async def test_unanswerable_zero_claims_accepted(provenance_resolver, profiler_result):
    llm = MagicMock()
    structured_llm = AsyncMock()

    candidate = build_valid_candidate(0, answerability="unanswerable")
    candidate.claims = []

    structured_llm.ainvoke.return_value = BatchCandidateOutput(candidates=[candidate])
    llm.with_structured_output.return_value = structured_llm

    generator = CandidateGenerator(llm=llm, provenance_resolver=provenance_resolver)
    results = await generator.generate_candidates(DUMMY_HASH, profiler_result, budget=1)

    # Unanswerable + zero claims -> accepted if H-12 allows it.
    assert len(results) == 1
