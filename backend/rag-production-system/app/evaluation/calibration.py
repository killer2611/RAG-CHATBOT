from typing import Dict, List, Any, Optional

class DuplicateClaimError(ValueError):
    """Raised when duplicate claim_ids are found in automated or reference cases."""
    pass

class CalibrationResult:
    """
    Initial Phase 3E Calibration output.
    Explicitly restricted to claim-level support_status agreement.
    """
    def __init__(
        self,
        per_claim_agreement: Dict[str, bool],
        aggregate_agreement: Optional[float],
        unmatched_automated: List[str],
        unmatched_reference: List[str]
    ):
        self.per_claim_agreement = per_claim_agreement
        self.aggregate_agreement = aggregate_agreement
        self.unmatched_automated = unmatched_automated
        self.unmatched_reference = unmatched_reference

class CalibrationEngine:
    """
    Deterministic offline mechanism for Phase 3E calibration.
    Computes EXACTLY TWO metrics: per-claim agreement and aggregate agreement.
    """
    def calibrate(self, automated_case: Dict[str, Any], reference_claims: List[Dict[str, str]]) -> CalibrationResult:
        """
        Compares an automated BenchmarkCase against a synthetic human-reference structure.

        automated_case: A schema-valid BenchmarkCase dictionary.
        reference_claims: A minimal reference structure containing claim_id and support_status.
        """
        auto_claims_list = automated_case.get("claims", [])

        auto_claims = {}
        for c in auto_claims_list:
            if "claim_id" not in c:
                raise ValueError("Automated claim is missing required 'claim_id' field.")
            if "support_status" not in c:
                raise ValueError("Automated claim is missing required 'support_status' field.")
            cid = c["claim_id"]
            if cid in auto_claims:
                raise DuplicateClaimError(f"Duplicate automated claim_id: {cid}")
            auto_claims[cid] = c["support_status"]

        ref_claims = {}
        for r in reference_claims:
            if "claim_id" not in r:
                raise ValueError("Reference claim is missing required 'claim_id' field.")
            if "support_status" not in r:
                raise ValueError("Reference claim is missing required 'support_status' field.")
            cid = r["claim_id"]
            if cid in ref_claims:
                raise DuplicateClaimError(f"Duplicate reference claim_id: {cid}")
            ref_claims[cid] = r["support_status"]

        unmatched_automated = [cid for cid in auto_claims if cid not in ref_claims]
        unmatched_reference = [cid for cid in ref_claims if cid not in auto_claims]

        per_claim_agreement = {}
        matched_pairs = 0
        matched_agreements = 0

        for cid in auto_claims:
            if cid in ref_claims:
                matched_pairs += 1
                is_agreed = auto_claims[cid] == ref_claims[cid]
                per_claim_agreement[cid] = is_agreed
                if is_agreed:
                    matched_agreements += 1

        aggregate_agreement = None
        if matched_pairs > 0:
            aggregate_agreement = matched_agreements / matched_pairs

        return CalibrationResult(
            per_claim_agreement=per_claim_agreement,
            aggregate_agreement=aggregate_agreement,
            unmatched_automated=unmatched_automated,
            unmatched_reference=unmatched_reference
        )