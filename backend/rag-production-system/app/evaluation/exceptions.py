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

class BenchmarkPopulationError(Exception):
    """
    Raised when a benchmark run completes but n_admitted is below the
    required minimum floor for the selected mode.

    This is a population-level run failure, NOT an artifact-validation
    failure. Valid artifacts already written to disk are preserved.

    Attributes:
        n_generated (int): total candidates produced
        n_admitted (int): cases admitted to benchmark population
        n_rejected (int): cases excluded by policy
        n_disputed (int): cases where secondary verification failed
        n_pipeline_errors (int): unexpected pipeline failures
        min_floor (int): required minimum for the selected mode
        mode (str): run mode (smoke, standard, comprehensive)
    """
    def __init__(
        self,
        message: str,
        n_generated: int,
        n_admitted: int,
        n_rejected: int,
        n_disputed: int,
        n_pipeline_errors: int,
        min_floor: int,
        mode: str,
    ):
        super().__init__(message)
        self.n_generated = n_generated
        self.n_admitted = n_admitted
        self.n_rejected = n_rejected
        self.n_disputed = n_disputed
        self.n_pipeline_errors = n_pipeline_errors
        self.min_floor = min_floor
        self.mode = mode
