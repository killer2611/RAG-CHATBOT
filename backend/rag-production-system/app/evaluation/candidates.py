"""
Phase 3B → 3C Handoff Contract.

Defines PartialBenchmarkCandidate — the typed intermediate object produced
by 3B generation and passed to downstream enrichment and 3C verification.

CRITICAL DISTINCTION:
    PartialBenchmarkCandidate != BenchmarkCase

A PartialBenchmarkCandidate is an INTERMEDIATE Phase 3 object that:
  - has been locally validated (H-12, provenance existence, zero-claim gate);
  - has source-local retrieval fields populated (evidence_scope, corpus_position);
  - is MISSING corpus-global retrieval fields (distractor_profile, retrieval_risk);
  - explicitly includes a hollow/stub verification object that MUST NOT be populated with real verdicts by 3B;
  - MUST NOT be passed to the final frozen BenchmarkCase schema validator.

A completed BenchmarkCase is only produced AFTER:
  1. 3C populates the verification block;
  2. corpus-aware enrichment populates distractor_profile and retrieval_risk;
  3. the final jsonschema.validate(case, frozen_schema) gate passes.

This file must NOT be modified to make partial candidates appear schema-valid.
If fields are genuinely missing, they must remain absent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class PartialRetrievalProfile:
    """
    Source-local retrieval metadata derivable within 3B.

    Partial instantiation of the retrieval_profile schema component.

    OPEN DECISION — NOT RESOLVED: retrieval_risk assignment policy.
    OPEN DECISION — NOT RESOLVED: distractor_profile assignment policy.
    """
    evidence_scope: Literal["single_span", "multi_span"]
    corpus_position: Optional[Literal["start", "middle", "end"]]
    # distractor_profile: intentionally absent until corpus-aware enrichment
    # retrieval_risk: intentionally absent until corpus-aware enrichment


@dataclass
class HollowVerificationStub:
    """
    Explicit structure-only representation of the verification block at the 3B boundary.
    3B is strictly prohibited from populating actual semantic verdicts.
    """
    verdict: None = None


@dataclass
class PartialBenchmarkCandidate:
    """
    Typed intermediate representation of a partial Phase 3 benchmark candidate
    at the 3B → 3C boundary.

    This is NOT a BenchmarkCase. It must not be passed to the frozen
    JSON Schema validator. It is incomplete by design — corpus-global
    retrieval fields remain absent until downstream stages, while the
    verification block is present only as a hollow structure-only stub and
    contains no semantic verdicts.

    Identity fields (case_id, evidence_ids, claim_ids) survive the handoff
    unchanged. They provide runtime uniqueness but NOT reproducible candidate
    identity. OPEN DECISION #12 — NOT RESOLVED.

    The version block carries provisional structural metadata only.
    OPEN DECISION #9 — NOT RESOLVED (benchmark versioning convention).
    """
    case_id: str
    question: str
    expected_answer: str
    answerability: Literal["answerable", "unanswerable"]
    question_type: Literal[
        "factual", "definition", "numeric", "procedural",
        "comparison", "multi_hop", "synthesis", "abstention"
    ]
    topics: Optional[List[str]]
    source: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    claims: List[Dict[str, Any]]
    version: Dict[str, Any]
    retrieval_profile: PartialRetrievalProfile
    verification: HollowVerificationStub = field(default_factory=HollowVerificationStub)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialises the partial candidate to a plain dictionary for downstream
        stages. The returned dict is still PARTIAL — it must not be validated
        against the frozen BenchmarkCase schema until corpus-global fields and
        verification have been appended.
        """
        case_dict = {
            "case_id": self.case_id,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "answerability": self.answerability,
            "question_type": self.question_type,
            "topics": self.topics,
            "source": self.source,
            "evidence": self.evidence,
            "claims": self.claims,
            "version": self.version,
            "verification": {
                "verdict": self.verification.verdict,
            }
        }

        # 3B may genuinely lack sufficient information to derive position (e.g. no pages
        # and fallback string offset fails). If absent, it is explicitly deferred to
        # corpus enrichment, since the frozen schema requires a value but prohibits 'unknown'.
        rp_dict = {
            "evidence_scope": self.retrieval_profile.evidence_scope,
        }
        if self.retrieval_profile.corpus_position is not None:
            rp_dict["corpus_position"] = self.retrieval_profile.corpus_position

        case_dict["retrieval_profile"] = rp_dict
        return case_dict
