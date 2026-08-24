from typing import Any, Optional

class StructuralValidationError(Exception):
    """
    Raised when a PartialBenchmarkCandidate fails 3C structural checks.
    """
    pass

class BenchmarkAdmissionError(Exception):
    """
    Raised when a candidate fails a strict semantic admission invariant
    (e.g., missing authoritative corpus position), preventing it from
    becoming benchmark data.
    """
    pass

class UnresolvedPolicyError(Exception):
    """
    Raised when an operation requires an established policy that is currently
    an unresolved open decision (e.g., mixed-claim aggregation logic or
    distractor classification thresholds).
    """
    def __init__(self, message: str, partial_result: Optional[Any] = None):
        super().__init__(message)
        self.partial_result = partial_result
