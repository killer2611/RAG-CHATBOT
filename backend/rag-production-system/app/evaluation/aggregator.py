import copy
from typing import NoReturn
from app.evaluation.exceptions import UnresolvedPolicyError
from app.evaluation.verifier_v3 import IntermediateVerificationResult

class CaseAggregator:
    """
    Phase 3D-1 CaseAggregator.
    This establishes the mechanism boundary.
    The aggregation policy remains blocked by Open Decision #10.

    FUTURE INJECTION BOUNDARY:
    The eventual architecture is designed to permit:
        unresolved/default policy
                ↓
        injected concrete policy implementation
                ↓
        same orchestration mechanism
    without requiring a pipeline redesign.
    """
    def aggregate(self, intermediate_result: IntermediateVerificationResult) -> NoReturn:
        """
        Assembles the structural Phase 3 verification block up to the policy boundary.
        Since OD #10 is unresolved, it MUST raise UnresolvedPolicyError.
        """
        case_dict = copy.deepcopy(intermediate_result.partial_case_dict)

        # Structurally assemble verification.primary
        case_dict["verification"] = {
            "verdict": None,
            "primary": {
                "verdict": None,
                "claims_checked": list(intermediate_result.claims_checked),
                "unsupported_claims": list(intermediate_result.unsupported_claims),
                "reason": None
            },
            "secondary": None,
            "human_review": None
        }

        assembled_result = IntermediateVerificationResult(
            partial_case_dict=case_dict,
            claims_checked=list(intermediate_result.claims_checked),
            unsupported_claims=list(intermediate_result.unsupported_claims)
        )

        raise UnresolvedPolicyError(
            "Case-level aggregation policy remains unresolved (Open Decision #10). Cannot populate verification verdicts.",
            partial_result=assembled_result
        )
