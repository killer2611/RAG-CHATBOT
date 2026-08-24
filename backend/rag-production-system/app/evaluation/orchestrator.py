import copy
from typing import Dict, Any, NoReturn

from app.evaluation.verifier_v3 import Phase3CVerifier
from app.evaluation.exceptions import UnresolvedPolicyError
from app.evaluation.aggregator import CaseAggregator
from app.evaluation.enrichment import CorpusEnricher

class Phase3DOrchestrator:
    """
    Phase 3D Pipeline Orchestrator.
    Connects the 3B -> 3C boundary to 3D infrastructure.
    """
    def __init__(self, verifier: Phase3CVerifier, enricher: CorpusEnricher, aggregator: CaseAggregator):
        self.verifier = verifier
        self.enricher = enricher
        self.aggregator = aggregator

    async def run_pipeline(self, partial_candidate: Dict[str, Any]) -> None:
        """
        1. Accept a PartialBenchmarkCandidate.
        2. Invoke the existing 3C verifier.
        3. Catch the existing UnresolvedPolicyError.
        4. Extract its IntermediateVerificationResult.
        5. Route that result to the CaseAggregator interface.

        TRANSITIONAL CONTROL FLOW:
        The current 3C boundary communicates its intermediate result through
        UnresolvedPolicyError because Open Decision #10 remains unresolved.
        This exception-based transport is explicitly transitional. It is NOT
        the permanent case-level pipeline contract. Once OD #10 is resolved,
        the aggregation layer is expected to produce a normal completed-case
        result. Future callers must not encode the current exception path as
        permanent benchmark admission policy.
        """
        # Ensure we don't mutate caller-owned input
        candidate = copy.deepcopy(partial_candidate)

        try:
            await self.verifier.verify_candidate(candidate)
        except UnresolvedPolicyError as e:
            if getattr(e, 'partial_result', None) is None:
                # Structural/runtime error: Exception lacks expected intermediate result
                raise RuntimeError("UnresolvedPolicyError did not contain IntermediateVerificationResult.") from e

            # Route to CorpusEnricher (computes retrieval/metadata mechanism, enforces admission boundary)
            # Will raise BenchmarkAdmissionError if corpus_position is missing (Admission failure)
            # Will raise UnresolvedPolicyError due to distractor/risk policy (OD blocked)
            try:
                enriched_result = self.enricher.enrich(e.partial_result)
            except UnresolvedPolicyError as enrich_e:
                if getattr(enrich_e, 'partial_result', None) is None:
                    raise RuntimeError("UnresolvedPolicyError from enricher did not contain IntermediateVerificationResult.") from enrich_e

                # Route to CaseAggregator for structural assembly and aggregation policy seam
                return self.aggregator.aggregate(enrich_e.partial_result)

            # If enrich returned normally, pass to aggregator (should not happen while ODs remain unresolved)
            return self.aggregator.aggregate(enriched_result)

        # If verify_candidate returned normally, it violated the 3C always-raise contract.
        raise RuntimeError("Verifier returned normally, violating the 3C always-raise boundary.")
