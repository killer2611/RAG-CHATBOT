import copy
from typing import Optional

from app.evaluation.exceptions import BenchmarkAdmissionError, UnresolvedPolicyError
from app.evaluation.verifier_v3 import IntermediateVerificationResult

class CorpusEnricher:
    """
    3D-2 establishes the deterministic enrichment mechanism boundary;
    policy-dependent interpretation remains blocked.

    Responsible for checking the admission-critical `corpus_position` invariant.
    Also establishes the mechanism boundary for future `distractor_profile`
    and `retrieval_risk` enrichment. Actual calculation of those fields is not yet
    computed, as classification policy and risk thresholds remain an Open Decision.
    """
    def __init__(self, retriever_interface: Optional[object] = None):
        """
        Establishes mechanism-neutral dependency injection for future retrieval enrichment.
        Does not require a live HierarchicalRetriever immediately, allowing decoupling
        from vector-store instantiation in test/pipeline environments where enrichment
        is currently policy-blocked anyway.
        """
        self.retriever = retriever_interface

    def enrich(self, result: IntermediateVerificationResult) -> IntermediateVerificationResult:
        """
        Enforces corpus position requirements and halts at unresolved retrieval enrichment boundaries.

        Does not mutate the caller's IntermediateVerificationResult object.
        """
        # Deepcopy the case dict to avoid mutating caller-owned objects
        case_dict = copy.deepcopy(result.partial_case_dict)
        retrieval_profile = case_dict.get("retrieval_profile", {})

        # SCOPE A: corpus_position Enforcement
        # If corpus_position is absent or None, it means authoritative structural
        # metadata was unavailable (e.g., TXT/DOCX files). We enforce the locked Option A invariant.
        if not retrieval_profile.get("corpus_position"):
            raise BenchmarkAdmissionError(
                f"Benchmark admission failed for case {case_dict.get('case_id')}: "
                "authoritative corpus_position is required but was unresolved."
            )

        # Re-pack into a safe intermediate result for downstream components
        enriched_result = IntermediateVerificationResult(
            partial_case_dict=case_dict,
            claims_checked=list(result.claims_checked),
            unsupported_claims=list(result.unsupported_claims)
        )

        # SCOPE C/D: distractor_profile and retrieval_risk Enrichment
        # Because we must not invent thresholds or classification logic, we explicitly fail
        # at this policy boundary. We pass the enriched_result so callers can inspect the state.
        raise UnresolvedPolicyError(
            "Retrieval enrichment policy (distractor_profile classification and retrieval_risk thresholds) "
            "remains unresolved. Cannot populate corpus-global schema fields.",
            partial_result=enriched_result
        )
