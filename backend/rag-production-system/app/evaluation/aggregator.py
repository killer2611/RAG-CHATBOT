import copy
from typing import Any, Protocol, Literal, Optional

from app.core.config import Settings
from app.evaluation.exceptions import StructuralValidationError
from app.evaluation.verifier_v3 import IntermediateVerificationResult

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

class SecondaryVerifier(Protocol):
    async def verify(self, question: str, expected_answer: str, disputed_claims: list[dict[str, Any]]) -> Literal["accepted", "rejected", "error"]:
        ...

class DefaultSecondaryVerifier:
    def __init__(self, settings: Settings):
        self.llm = ChatOpenAI(
            base_url=settings.eval_sambanova_base_url,
            api_key=settings.eval_sambanova_api_key,
            model=settings.eval_sambanova_model,
            temperature=0.0
        )

    async def verify(self, question: str, expected_answer: str, disputed_claims: list[dict[str, Any]]) -> Literal["accepted", "rejected", "error"]:
        claims_text = ""
        for claim in disputed_claims:
            quotes = " | ".join(claim.get("evidence_quotes", []))
            claims_text += f"Claim: {claim.get('text')}\nEvidence: {quotes}\n"

        prompt = f"""You are a factual accuracy evaluator.

Using ONLY the question, expected answer, and evidence passages provided,
determine whether the disputed claims are sufficiently supported by the
evidence to accept this benchmark case.

Question: {question}
Expected Answer: {expected_answer}

Disputed claims and their evidence passages:
{claims_text}
Respond with exactly one word on a single line:
accepted
or
rejected

No explanation. No other text.
"""
        try:
            response = await self.llm.ainvoke([SystemMessage(content=prompt)])
            text = response.content.strip().lower()
            if text == "accepted":
                return "accepted"
            elif text == "rejected":
                return "rejected"
            else:
                return "error"
        except Exception:
            return "error"

class CaseAggregator:
    """
    Phase 3D-1 CaseAggregator.
    Implements OD #10 Case-level verdict aggregation policy.
    """
    def __init__(self, settings: Settings, secondary_verifier: Optional[SecondaryVerifier] = None):
        self.settings = settings
        self.secondary_verifier = secondary_verifier if secondary_verifier is not None else DefaultSecondaryVerifier(settings)

    async def aggregate(self, intermediate_result: IntermediateVerificationResult) -> IntermediateVerificationResult:
        case_dict = copy.deepcopy(intermediate_result.partial_case_dict)

        answerability = case_dict.get("answerability", "answerable")
        claims = case_dict.get("claims", [])

        verification = {
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

        if answerability == "unanswerable":
            verification["verdict"] = "accepted"
            verification["primary"]["verdict"] = "accepted"
            case_dict["verification"] = verification
            return IntermediateVerificationResult(
                partial_case_dict=case_dict,
                claims_checked=list(intermediate_result.claims_checked),
                unsupported_claims=list(intermediate_result.unsupported_claims)
            )

        eligible_claims = [c for c in claims if c.get("support_status") != "not_applicable"]

        if len(eligible_claims) == 0:
            raise StructuralValidationError("answerable + zero eligible claims")

        contradicted_claims = [c["claim_id"] for c in eligible_claims if c.get("support_status") == "contradicted"]

        if len(contradicted_claims) > 0:
            verification["verdict"] = "rejected"
            verification["primary"]["verdict"] = "rejected"
            case_dict["verification"] = verification
            return IntermediateVerificationResult(
                partial_case_dict=case_dict,
                claims_checked=list(intermediate_result.claims_checked),
                unsupported_claims=list(intermediate_result.unsupported_claims)
            )

        unsupported_claims_data = [c for c in eligible_claims if c.get("support_status") == "unsupported"]
        unsupported_count = len(unsupported_claims_data)
        unsupported_ratio = unsupported_count / len(eligible_claims)

        if unsupported_ratio > self.settings.phase3_unsupported_ratio_threshold:
            verification["verdict"] = "rejected"
            verification["primary"]["verdict"] = "rejected"
            case_dict["verification"] = verification
            return IntermediateVerificationResult(
                partial_case_dict=case_dict,
                claims_checked=list(intermediate_result.claims_checked),
                unsupported_claims=list(intermediate_result.unsupported_claims)
            )

        if unsupported_count == 0:
            verification["verdict"] = "accepted"
            verification["primary"]["verdict"] = "accepted"
            case_dict["verification"] = verification
            return IntermediateVerificationResult(
                partial_case_dict=case_dict,
                claims_checked=list(intermediate_result.claims_checked),
                unsupported_claims=list(intermediate_result.unsupported_claims)
            )

        verification["primary"]["verdict"] = "disputed"

        evidence_list = case_dict.get("evidence", [])
        evidence_map = {e.get("evidence_id"): e.get("quote", "") for e in evidence_list}

        normalized_disputed_claims = []
        for c in unsupported_claims_data:
            claim_id = c.get("claim_id")
            claim_text = c.get("claim", "")
            evidence_ids = c.get("evidence_ids", [])
            evidence_quotes = []
            for eid in evidence_ids:
                if eid in evidence_map:
                    evidence_quotes.append(evidence_map[eid])

            normalized_disputed_claims.append({
                "claim_id": claim_id,
                "text": claim_text,
                "evidence_quotes": evidence_quotes
            })

        secondary_result = await self.secondary_verifier.verify(
            question=case_dict.get("question", ""),
            expected_answer=case_dict.get("expected_answer", ""),
            disputed_claims=normalized_disputed_claims
        )

        if secondary_result == "error":
            verification["verdict"] = "disputed"
            verification["secondary"] = None
        else:
            verification["verdict"] = secondary_result
            verification["secondary"] = {
                "verdict": secondary_result,
                "claims_checked": [c["claim_id"] for c in unsupported_claims_data],
                "unsupported_claims": [],
                "reason": None
            }

        case_dict["verification"] = verification
        return IntermediateVerificationResult(
            partial_case_dict=case_dict,
            claims_checked=list(intermediate_result.claims_checked),
            unsupported_claims=list(intermediate_result.unsupported_claims)
        )
