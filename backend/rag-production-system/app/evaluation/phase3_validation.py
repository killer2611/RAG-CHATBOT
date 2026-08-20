def validate_h12_unanswerable_semantics(benchmark_case: dict) -> None:
    """
    Validates H-12: Unanswerable Claim Semantics.

    If answerability = "unanswerable", EVERY claim.support_status MUST equal "not_applicable".
    Evidence MAY still be present in an unanswerable case.
    """
    if benchmark_case.get("answerability") != "unanswerable":
        return

    claims = benchmark_case.get("claims", [])
    for claim in claims:
        status = claim.get("support_status")
        if status in {"supported", "unsupported", "contradicted"}:
            raise ValueError(
                f"H-12 Violation: Unanswerable case contains claim with forbidden support_status '{status}'. "
                "Only 'not_applicable' is permitted for claims in an unanswerable case."
            )
