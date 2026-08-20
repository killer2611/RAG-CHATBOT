import logging
import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.evaluation.candidates import PartialBenchmarkCandidate, PartialRetrievalProfile
from app.evaluation.phase3_validation import validate_h12_unanswerable_semantics
from app.evaluation.profiler import ProfilerResult
from app.evaluation.provenance import DocumentNotFoundError, ProvenanceResolver, QuoteNotFoundError

logger = logging.getLogger(__name__)

# STRICT COST FIREWALL BOUNDARIES
MAX_CANDIDATES_PER_BATCH = 5
DEFAULT_CANDIDATE_BUDGET = 20
HARD_MAX_CANDIDATE_BUDGET = 30

class ClaimOutput(BaseModel):
    claim: str
    # HARDENING #1: Removing `support_status` from LLM output so it doesn't self-grade or act as a verifier.
    evidence_indices: List[int] = Field(
        default_factory=list,
        description="Indices mapping to the proposed_evidence array."
    )
    rationale: Optional[str] = None

class CandidateOutput(BaseModel):
    question: str
    expected_answer: str
    answerability: Literal["answerable", "unanswerable"]
    question_type: Literal[
        "factual", "definition", "numeric", "procedural",
        "comparison", "multi_hop", "synthesis", "abstention"
    ]
    topics: Optional[List[str]] = None
    proposed_evidence: List[str] = Field(
        default_factory=list,
        description="Exact quotes from the document supporting the answer or claims."
    )
    claims: List[ClaimOutput] = Field(default_factory=list)

class BatchCandidateOutput(BaseModel):
    candidates: List[CandidateOutput]


# HARDENING #2: Strategy-specific document routing templates.
STRATEGY_TEMPLATES = {
    "legal": "Strategy: Focus on clauses, obligations, rights, definitions, and exceptions. Generate questions probing formal legal conditions.",
    "policy": "Strategy: Focus on rules, conditions, institutional procedures, and eligibility. Generate questions probing governance and compliance.",
    "technical-research": "Strategy: Focus on scientific methodology, terminology, numeric findings, and experiments.",
    "manual": "Strategy: Focus on procedural steps, action sequences, setup, and troubleshooting.",
    "narrative": "Strategy: Focus on factual events, entity relationships, and historical/continuous narrative.",
    "tabular": "Strategy: Focus on numeric data, comparisons, and structured row/column relationships.",
    "general": "Strategy: Use a conservative generic question-answering generation strategy focusing on explicit facts."
}


class CandidateGenerator:
    """
    Phase 3B-2 Candidate Generator.

    Generates Candidate BenchmarkCases.
    Strictly restricted from Verification (3C), Truth Assessment, or Schema Hacking.
    Enforces the candidate batch cost model.
    """
    def __init__(self, llm: BaseChatModel, provenance_resolver: ProvenanceResolver):
        self.llm = llm
        self.structured_llm = llm.with_structured_output(BatchCandidateOutput)
        self.provenance_resolver = provenance_resolver

    async def generate_candidates(
        self,
        document_hash: str,
        profiler_result: ProfilerResult,
        budget: int = DEFAULT_CANDIDATE_BUDGET
    ) -> List[PartialBenchmarkCandidate]:
        """
        Generates structured candidate cases within the strict cost budget.

        HARDENING #4: Explicitly guarding the token-cost implication.
        This implementation sends the COMPLETE extracted source text to EVERY generation batch invocation.
        This means token expenditure scales roughly with: source_context_size * number_of_generation_calls.
        Any future source-context optimization (e.g. chunking/summarization) is a separate future design concern,
        and must not violate the locked 5-candidate batch boundary.
        """
        if budget <= 0:
            raise ValueError(f"Candidate budget must be positive, got {budget}")
        if budget > HARD_MAX_CANDIDATE_BUDGET:
            raise ValueError(f"Candidate budget {budget} exceeds hard maximum {HARD_MAX_CANDIDATE_BUDGET}")

        try:
            # HARDENING #6: Removed private method coupling. Uses public boundary.
            full_text, source_name = self.provenance_resolver.get_source_context(document_hash)
            # 3B-3: Page count is retrieved once per document and passed to all
            # per-candidate processing. Zero additional LLM calls.
            total_pages = self.provenance_resolver.get_page_count(document_hash)
        except DocumentNotFoundError as e:
            raise ValueError(f"Cannot generate candidates: {e}")

        doc_type = profiler_result.document_type
        strategy = STRATEGY_TEMPLATES.get(doc_type, STRATEGY_TEMPLATES["general"])

        system_prompt = f"""You are a Phase 3 Candidate Generator for a RAG Evaluation Benchmark.
The source document is classified as: '{doc_type}'.
{strategy}
Generate evaluation cases based purely on the provided document text.

Rules:
1. 'proposed_evidence' MUST be EXACT quotes from the source text. Do not modify the text.
2. Unanswerable cases should be plausible questions that seem relevant but cannot be answered using the text.
"""

        num_calls = (budget + MAX_CANDIDATES_PER_BATCH - 1) // MAX_CANDIDATES_PER_BATCH
        all_candidate_cases = []
        total_requested = 0

        for _ in range(num_calls):
            # CORRECTION 1: Account for GENERATION ATTEMPTS, not accepted cases.
            requested = min(MAX_CANDIDATES_PER_BATCH, budget - total_requested)
            if requested <= 0:
                break

            total_requested += requested

            prompt = system_prompt + f"\nGenerate exactly {requested} candidate cases."

            try:
                batch_result: BatchCandidateOutput = await self.structured_llm.ainvoke([
                    SystemMessage(content=prompt),
                    HumanMessage(content=f"DOCUMENT TEXT:\n{full_text}")
                ])

                if not batch_result or not batch_result.candidates:
                    continue

                # HARDENING - BATCH CARDINALITY FIREWALL:
                # If the LLM returns more than the requested cardinality, it violated the prompt instruction
                # and the cost firewall boundary. We fail-closed and reject the entire batch rather than truncating it.
                if len(batch_result.candidates) > requested:
                    logger.warning(f"Batch cardinality violation: requested {requested}, but got {len(batch_result.candidates)}. Dropping batch.")
                    continue

                for candidate in batch_result.candidates:
                    case = self._process_candidate(
                        document_hash, source_name, profiler_result,
                        candidate, total_pages, full_text
                    )
                    if case is not None:
                        all_candidate_cases.append(case)

            except Exception as e:
                logger.warning(f"Batch generation failed or structure invalid: {e}")
                continue

        return all_candidate_cases

    def _derive_evidence_scope(
        self, resolved_evidence: list
    ) -> str:
        """
        Derives evidence_scope from the candidate's resolved evidence spans.
        Source-local. Introduces zero LLM calls.

        single_span: exactly one distinct canonical source span (deduplicated by span_hash).
        multi_span:  more than one distinct canonical source span.
        """
        unique_spans = {ev["span_hash"] for ev in resolved_evidence}
        return "single_span" if len(unique_spans) == 1 else "multi_span"

    def _derive_corpus_position(
        self, resolved_evidence: list, total_pages: int, full_text: str
    ) -> Optional[str]:
        """
        Derives the approximate position of the evidence within the source document.
        Source-local. Introduces zero LLM calls.

        Uses the minimum (first-occurring) page of resolved evidence relative to
        the total page count using equal thirds (tertiles):
            start:  page is in the first third
            middle: page is in the middle third
            end:    page is in the last third

        If evidence has no page metadata (cross-page span or plain text), uses the string
        index of the first evidence quote within the full text as a deterministic
        source-grounded fallback. Does not arbitrarily fabricate "middle".

        IMPORTANT: This is a provisional implementation. The exact tertile
        boundary convention is not formally established in the frozen contract.
        OPEN DECISION — NOT RESOLVED (boundary precision / tertile policy).
        """
        pages_with_data = [
            ev["page"] for ev in resolved_evidence
            if ev.get("page") is not None
        ]

        position_ratio: Optional[float] = None

        if pages_with_data and total_pages > 0:
            # Use the first (earliest) page of evidence within the document.
            min_page = min(pages_with_data)
            # Pages from provenance are 1-indexed.
            position_ratio = (min_page - 1) / total_pages
        elif full_text and resolved_evidence:
            # Deterministic source-grounded fallback using string index.
            # Avoids arbitrarily assigning "middle" when page data is unavailable.
            first_idx = -1
            for ev in resolved_evidence:
                idx = full_text.find(ev["quote"])
                if idx != -1:
                    if first_idx == -1 or idx < first_idx:
                        first_idx = idx

            if first_idx != -1 and len(full_text) > 0:
                position_ratio = first_idx / len(full_text)

        if position_ratio is None:
            # Genuinely not derivable (e.g. quote missing from text and no pages).
            # Do NOT silently fabricate "middle". Defer to corpus enrichment.
            return None

        if position_ratio < 1 / 3:
            return "start"
        elif position_ratio < 2 / 3:
            return "middle"
        else:
            return "end"

    def _process_candidate(
        self,
        document_hash: str,
        source_name: str,
        profiler_result: ProfilerResult,
        candidate: CandidateOutput,
        total_pages: int,
        full_text: str,
    ) -> Optional[PartialBenchmarkCandidate]:
        """
        Validates structure, enforces H-12, resolves provenance, and derives
        source-local retrieval_profile fields.
        Returns a typed PartialBenchmarkCandidate if valid, or None if dropped.

        Returns PartialBenchmarkCandidate — NOT a complete BenchmarkCase.
        MUST NOT be passed to the frozen JSON Schema validator.
        """
        # Answerable zero-claim semantics: Local structural quality gate
        if candidate.answerability == "answerable" and not candidate.claims:
            return None

        resolved_evidence = []
        index_to_ev_id = {}

        # 1. Resolve Provenance
        # PROVENANCE EXISTENCE RESOLUTION ONLY:
        # Successful quote resolution means only that the proposed quote was located
        # in the authoritative source under the current provisional matching policy.
        # It does NOT mean the quote semantically supports the claim.
        # Semantic claim-support verification is exclusively a future 3C concern.
        for idx, quote in enumerate(candidate.proposed_evidence):
            try:
                prov_result = self.provenance_resolver.resolve_quote(document_hash, quote)
                # HARDENING #5: UUIDs provide runtime uniqueness, NOT reproducible candidate identity.
                # Candidate determinism remains OPEN DECISION #12.
                ev_id = f"ev-{uuid.uuid4().hex[:8]}"

                ev_obj = {
                    "evidence_id": ev_id,
                    "quote": prov_result.quote,
                    "span_hash": prov_result.span_hash,
                    "page": prov_result.page,
                    "section": None
                }
                resolved_evidence.append(ev_obj)
                index_to_ev_id[idx] = ev_id
            except QuoteNotFoundError:
                return None

        resolved_claims = []
        for c in candidate.claims:
            ev_ids = []
            for ev_idx in c.evidence_indices:
                if ev_idx in index_to_ev_id:
                    ev_ids.append(index_to_ev_id[ev_idx])
                else:
                    return None

            # HARDENING #1: 3B does not perform support verification.
            # We omit support_status for answerable cases as a partial downstream payload.
            # But for H-12 unanswerable cases, we MUST output not_applicable structurally.
            claim_obj = {
                "claim_id": f"claim-{uuid.uuid4().hex[:8]}",
                "claim": c.claim,
                "evidence_ids": ev_ids,
                "rationale": c.rationale
            }
            if candidate.answerability == "unanswerable":
                claim_obj["support_status"] = "not_applicable"

            resolved_claims.append(claim_obj)

        # 3B-3: Derive source-local retrieval_profile fields deterministically.
        # No LLM calls. No corpus-global knowledge required.
        evidence_scope = self._derive_evidence_scope(resolved_evidence)
        corpus_position = self._derive_corpus_position(resolved_evidence, total_pages, full_text)
        # distractor_profile and retrieval_risk are intentionally absent:
        # they require corpus-global context unavailable to 3B.

        partial_rp = PartialRetrievalProfile(
            evidence_scope=evidence_scope,
            corpus_position=corpus_position,
        )

        partial_candidate = PartialBenchmarkCandidate(
            case_id=f"case-{uuid.uuid4().hex[:8]}",
            question=candidate.question,
            expected_answer=candidate.expected_answer,
            answerability=candidate.answerability,
            question_type=candidate.question_type,
            topics=candidate.topics,
            # SOURCE_ID VS DOCUMENT_HASH:
            # document_hash is the canonical cryptographic identity of the authoritative source bytes.
            # For Phase 3 candidate generation, source_id currently carries that same canonical document identity.
            # This does not redefine or alter Phase 1/2 semantics. If a future Phase 3 design requires a distinct
            # source identifier, that must be explicitly designed rather than inferred.
            source={
                "source_name": source_name,
                "source_id": document_hash,
                "document_hash": document_hash,
                "document_type": profiler_result.document_type,
                "type_confidence": profiler_result.type_confidence
            },
            evidence=resolved_evidence,
            claims=resolved_claims,
            # OPEN DECISION #9 - NOT RESOLVED: Benchmark versioning convention.
            # The version block below is strictly provisional structural metadata
            # to satisfy the frozen benchmark_case.schema.json.
            version={
                "schema_version": get_settings().phase3_schema_version,
                "benchmark_version": get_settings().phase3_benchmark_version,
                "generator_prompt_version": get_settings().phase3_generator_prompt_version,
                "verifier_prompt_version": get_settings().phase3_verifier_prompt_version
            },
            retrieval_profile=partial_rp,
            # RETRIEVAL_PROFILE INTENTIONALLY PARTIAL:
            # evidence_scope and corpus_position are populated above (source-local).
            # distractor_profile and retrieval_risk remain ABSENT until corpus-aware enrichment.
        )

        # Validate H-12 against dict representation
        case_dict = partial_candidate.to_dict()
        try:
            validate_h12_unanswerable_semantics(case_dict)
        except ValueError:
            return None

        return partial_candidate
