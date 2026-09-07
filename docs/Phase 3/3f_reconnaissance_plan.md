# Phase 3F Reconnaissance Plan: Evaluation Integration and Statistical Reporting

## 1. Executive Summary
Phase 3F integrates the completed Phase 3 benchmark artifacts into the existing evaluation infrastructure to produce statistical reports. This reconnaissance confirms that the existing Phase 1/2 `EvaluationRunner` can be safely extended to consume Phase 3 `BenchmarkCase` artifacts via an adapter. While mechanisms (metric execution, raw score collection, deterministic stratification routing) can be built now, critical policies (thresholds, abstention scoring, statistical confidence intervals, and final case verdicts) are blocked by Open Decisions and must be treated as injectable configuration or explicitly marked as pending in the output. NO NEW RUNNER IS NECESSARY.

## 2. Current Verified Baseline
**OBSERVED:**
- Current HEAD is verified.
- Phase 3D (`ArtifactWriter`) and Phase 3E (`CalibrationEngine`) mechanisms are fully implemented.
- `docs/Phase 3/benchmark_case.schema.json` is untouched.
- Existing evaluation infrastructure resides in `app/evaluation/runner.py`, `judges.py`, and `datasets.py`.

## 3. Phase 3F Objective
To extend the existing evaluation system to consume `BenchmarkCase` artifacts, collect raw DeepEval metrics without inventing policy, and produce stratified statistical reports that explicitly represent policy-blocked values (e.g., pass/fail thresholds, CI) as pending.

## 4. Mandatory Phase 1/2 Evaluation Infrastructure Audit
**OBSERVED in `app/evaluation/runner.py` and `datasets.py`:**
- **Consumes:** `list[GoldenCase]` (loaded from JSON via `datasets.py`).
- **Produces:** CSV detailed report (`eval_...csv`) and JSON summary metadata (`eval_..._meta.json`).
- **RAG Invocation:** `RagService.answer_with_context(..., evaluation=True)`.
- **DeepEval Construction:** `LLMTestCase` is built from `question`, `expected_output`, `actual_output`, and `retrieval_context`.
- **Metrics Wired:** `FaithfulnessMetric`, `AnswerRelevancyMetric`, `ContextualPrecisionMetric`, `ContextualRecallMetric`.
- **Thresholds:** Hardcoded from `Settings.eval_threshold`.
- **Aggregation:** Simple arithmetic mean (`df[col].mean()`) in `parse_evaluation_report`.
- **Stratification:** Does not exist.
- **Statistical CI:** Does not exist.

**CONCLUSION:** The existing runner is entirely suitable for 3F. It requires an adapter to handle `BenchmarkCase` inputs, and it requires decoupling the hardcoded threshold into a configuration seam. Do not create a separate runner.

## 5. GoldenCase vs BenchmarkCase Gap Analysis
| FIELD / CONCEPT | PHASE 1/2 REPRESENTATION | PHASE 3 REPRESENTATION | COMPATIBLE? | ADAPTER REQUIRED? | POLICY DEPENDENCY? |
|-----------------|--------------------------|------------------------|-------------|-------------------|--------------------|
| Input text | `GoldenCase.question` | `BenchmarkCase.question` | Yes | Map field | None |
| Reference text | `GoldenCase.expected_output` | `BenchmarkCase.expected_answer` | Yes | Map field | None |
| Source ID | `GoldenCase.source.source_id` | `BenchmarkCase.source.source_id` | Yes | Map field | None |
| Source Name | `GoldenCase.source.source_name` | `BenchmarkCase.source.source_name` | Yes | Map field | None |
| Answerability | Not explicitly represented (assumed all answerable) | `BenchmarkCase.answerability` | Gap | Must route or filter | OD #2 (Abstention) |

**INFERRED:** An adapter layer is sufficient. 

**ADAPTER METADATA CONSTRAINT:** `BenchmarkCase` -> `GoldenCase` is viable for metric execution. The adapter MUST preserve the original `BenchmarkCase` metadata needed for 3F stratification and traceability, including at minimum:
- `case_id`
- `answerability`
- `question_type`
- `topics`
- `source.document_type`
- `retrieval_profile` fields

Do NOT modify the existing `GoldenCase` contract merely to carry this metadata. Preferred mechanism: `GoldenCase` for the existing runner's execution fields + parallel metadata keyed by `case_id`. This keeps Phase 1/2 contracts isolated.

## 6. Existing DeepEval Integration
**OBSERVED in `app/evaluation/judges.py` and `runner.py`:**
- **Currently wired metrics:** Faithfulness, Answer Relevancy, Contextual Precision, Contextual Recall.
- **Judge Configuration:** Cloud-only `GPTModel` (DeepSeek or SambaNova).
- **Invocation Boundary:** `deepeval.evaluate` (concurrent execution throttled to `max_concurrent=1`).
- **Thresholds:** Driven by `self.settings.eval_threshold` (Mechanism exists, values are arbitrary).
- **Cost/Live-Call:** YES. DeepEval metrics invoke the LLM judge, incurring API costs.

## 7. 3F Evaluation Input Contract
**OBSERVED:** To execute evaluation, the runner requires at minimum: `question`, `expected_answer`, and `source` metadata.
**INFERRED:** 3F will accept a valid `BenchmarkCase` JSON artifact, extract these minimal fields to invoke the RAG service, and construct an `LLMTestCase`. The original `BenchmarkCase` remains unmutated.

## 8. Metric Collection Boundary
**INFERRED:** DeepEval returns both raw `score` and a boolean `success`. 
**BOUNDARY:** 3F mechanism must record the raw `score`. 3F MUST NOT reinterpret `metric.success` as benchmark acceptance. 3F MUST NOT feed `threshold=None` results into the existing `passed_cases` aggregation. If a success field must exist for compatibility with an internal runner structure, it must be explicitly marked non-policy-bearing / `None` / pending rather than interpreted as pass/fail. Prefer a separate 3F result representation rather than modifying the meaning of the existing Phase 1/2 success field.

## 9. OD #1 Threshold Boundary
**POLICY-BLOCKED:** Pass/fail thresholds for metrics.
**MECHANISM:** The 3F evaluation path MUST construct all DeepEval metric instances with `threshold=None`. This is NOT a dummy, placeholder, arbitrary, or invented threshold. It is the DeepEval API-native mechanism that causes `BaseMetric.is_successful()` to return `success=None` and therefore prevents any threshold-based pass/fail policy from being applied. 

Phase 1/2 behavior MUST remain unchanged: existing Phase 1/2 evaluation continues using `self.settings.eval_threshold`. 3F MUST NOT reuse threshold-derived pass/fail semantics. 

The existing `parse_evaluation_report()` path MUST NOT be used to derive 3F `passed_cases`, because its `passed_cases` value is computed from the threshold-dependent `success` field. 3F reporting must operate on raw metric scores only. Do not invent any replacement pass/fail field. Do not resolve OD #1.

## 10. OD #2 Abstention Boundary
**POLICY-BLOCKED:** The formula for evaluating correctness when `answerability` != "answerable".
**MECHANISM:** When `BenchmarkCase.answerability == "unanswerable"`, the 3F path must enter an abstention-routing seam. The mechanism must preserve the raw RAG response and emit an explicit `PENDING_POLICY` state without selecting, implementing, or implying which evaluation metrics apply to unanswerable cases. Do NOT state that zero metrics are universally correct. Do NOT invent an abstention formula. Do NOT resolve OD #2.

## 11. OD #3 Statistical Boundary
**POLICY-BLOCKED:** Bootstrap / Confidence Interval methodology.
**MECHANISM:** Explicitly distinguish:
A. Frozen BenchmarkCase schema
B. Internal 3F statistical report
C. Future canonical production reporting/persistence contract

`confidence_interval` belongs ONLY to the internal 3F statistical report structure. It MUST NOT be added to BenchmarkCase. The frozen `benchmark_case.schema.json` has `additionalProperties: false` and contains no `confidence_interval` field. Until OD #3 resolves, the internal report may represent CI as `null` or an explicit pending state such as `PENDING_OD_3`. Do NOT modify the schema. Do NOT implement bootstrap/CI. Do NOT resolve OD #3.

## 12. OD #10 Case-Verdict Boundary
**POLICY-BLOCKED:** The final case-level benchmark verdict.
**MECHANISM:** 3F must evaluate offline/synthetic `BenchmarkCase` inputs provided externally, as the live pipeline halts at aggregation. 3F must not attempt to label the evaluation run itself as "Benchmark Accepted".

## 13. Statistical Reporting / Stratification Audit
**OBSERVED:** Existing `parse_evaluation_report` provides only flat global averages (`average_scores`).
**MECHANISM:** Keep stratification configurable. Do not promote `question_type`, `answerability`, `document_type`, `retrieval_risk`, `evidence_scope`, or any other schema field into a canonical production stratification policy. The mechanism may group by explicitly supplied dimensions. Do not invent aggregation methodology beyond the raw-score mechanism already authorized.

**INTERNAL 3F REPORT CONTRACT:**
It must define at minimum:
- report/case identifier
- raw metric scores
- configured stratification/group information
- aggregate raw-score statistics
- `confidence_interval = null/PENDING_OD_3`
- explicit representation of policy-pending values

This is an INTERNAL mechanism/test contract only. It is NOT the frozen BenchmarkCase schema. It is NOT a public API contract. It is NOT a canonical production persistence contract. Do not invent database persistence. Do not invent a public API.

## 14. Full 12-OD Dependency Matrix
| OD | DESCRIPTION | 3F IMPACT | MECHANISM AVAILABLE? | POLICY BLOCKED? | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|
| 1 | Metric thresholds | DeepEval pass/fail | Yes (collect raw score only) | Yes (threshold values) | `runner.py` uses `settings.eval_threshold` | Unresolved |
| 2 | Abstention accuracy | Unanswerable case eval | Yes (route separately) | Yes (scoring formula) | `BenchmarkCase.answerability` | Unresolved |
| 3 | Bootstrap/CI | Stat uncertainty | Yes (internal 3F report field; not BenchmarkCase schema) | Yes (methodology) | No existing CI in `runner.py` | Unresolved |
| 4 | Cache implementation | 3F evaluation caching | N/A | Yes | `phase3_contract_hardening.md` | Unresolved |
| 5 | Evidence overlap | Indirect dependency (upstream) | N/A | Yes | Schema `evidence_ids` | Unresolved |
| 6 | Secondary verifier | Indirect dependency (upstream) | N/A | Yes | Schema `secondary` | Unresolved |
| 7 | Human review | Indirect dependency (upstream) | N/A | Yes | Schema `human_review` | Unresolved |
| 8 | CLI/API | Exposure of 3F reporting contract | UNKNOWN | Yes | Existing CLI/API takes `test_file` GoldenCase format. Repo does not prove this can expose 3F. | Unresolved |
| 9 | Benchmark versioning | Pipeline drift tracking | Yes (record version in report) | Yes (compatibility policy)| Schema `version` | Unresolved |
| 10 | Case verdict | Live case generation | Yes (offline runner via mocks) | Yes (acceptance criteria)| `CaseAggregator` | Unresolved |
| 11 | Accepted-case count | Benchmark sizing | None | Yes | N/A | Unresolved |
| 12 | Determinism | Cross-run claim stability | Yes (synthetic test reproducible) | Yes (production identity)| Offline execution proves test reproducibility only. | Unresolved |

## 15. Cost / Live-Call Boundary
**OBSERVED:** Invoking `EvaluationRunner.run()` makes live calls to Groq/Gemini/Ollama (RAG generation) and DeepSeek/SambaNova (DeepEval judges). 
**FIREWALL:** 3F mechanism development must mock these boundaries in tests and must not trigger live runs during CI/CD without authorization.

## 16. Testability Matrix
**BUILDABLE TESTS:**
- Adapter: Verify `BenchmarkCase` properly converts to `GoldenCase` interface.
- Stratification: Grouping mocked metric scores by explicit configurable dimensions.
- Abstention Routing: Verify that `answerability == 'unanswerable'` enters the abstention-routing seam, preserves the raw RAG response, and emits `PENDING_POLICY` without selecting, implementing, or implying which evaluation metrics apply to unanswerable cases.
- Reporting Schema: Verify internal deterministic output structure matches requirements.

**BLOCKED TESTS:**
- Live threshold gating.
- Bootstrapped CI calculations.
- Live pipeline E2E (blocked by OD #10).

## 17. UNKNOWN Register
- **UNKNOWN:** Will the final statistical report be persisted in a database (e.g. `eval_runs` table) or remain as CSV/JSON file artifacts?
- **UNKNOWN:** Does `answerability == "unanswerable"` require a completely distinct DeepEval custom metric, or just a simple exact-match logic?
- **UNKNOWN:** Which specific metrics apply to unanswerable cases.
- **UNKNOWN:** Can the existing API/CLI expose the 3F reporting contract without resolving OD #8?

## 18. POLICY-BLOCKED Register
- Pass/Fail evaluation thresholds (OD #1).
- Unanswerable case scoring formula (OD #2).
- Statistical confidence interval calculation (OD #3).
- End-to-End live evaluation triggering (OD #10).
- Production stratification dimension policy.
- Canonical production persistence/reporting contract.

## 19. CONTRACT GAP Register
- The current `GoldenCase` does not support `answerability`. An explicit contract is needed to ensure `EvaluationRunner` can handle or bypass unanswerable cases.

## 20. Mechanisms Safely Buildable Now
1. `BenchmarkCase` to `GoldenCase` adapter.
2. Extension of `EvaluationRunner` to accept adapted cases via an isolated 3F execution/reporting path. The existing Phase 1/2 (`EvaluationRunner` -> CSV detailed report -> `parse_evaluation_report()` -> `passed_cases`) behavior MUST remain unchanged. 3F MUST NOT route its results through the existing `passed_cases` aggregation path. 3F must use `threshold=None` for DeepEval metric construction and operate on raw metric scores. If implementation requires extracting or refactoring shared metric execution code, that refactoring MUST preserve all existing Phase 1/2 behavior and the existing Phase 1/2 regression suite must continue to pass. Do NOT create a second parallel `EvaluationRunner`. Do NOT casually rewrite the existing runner. Do NOT change the meaning of Phase 1/2 success or `passed_cases`. The intended architecture is: existing evaluation infrastructure + isolated 3F execution/reporting path (NOT: existing runner rewritten for Phase 3).
3. Collection of raw `score` fields from DeepEval (separate from pass/fail).
4. Stratification grouping by explicitly configured dimensions (not hardcoded policy).
5. Internal deterministic report structure with explicit `confidence_interval: null` fields. Note: JSON report generation is a mechanism-level test/output format only, not a canonical production reporting contract.

## 21. Explicitly Forbidden Implementation
- Do NOT create a second, parallel `EvaluationRunner`.
- Do NOT invent threshold values or pass/fail labels (OD #1).
- Do NOT invent abstention pass/fail logic or which metrics apply to unanswerable cases (OD #2).
- Do NOT implement bootstrap resampling (OD #3).
- Do NOT hardcode assumed production stratification dimensions.
- Do NOT claim synthetic test reproducibility resolves OD #12.
- Do NOT modify Phase 3D.
- Do NOT bypass `CaseAggregator`.
- Do NOT resolve OD #10.
- Do NOT generate candidates.
- Do NOT invoke live LLM/API execution during mechanism tests.
- Do NOT modify Phase 1/2 semantics.
- Do NOT modify `benchmark_case.schema.json`.
- Do NOT invent a canonical production persistence/reporting policy.

## 22. Proposed Dependency Graph
`ArtifactWriter (3D-3)` -> `mocked BenchmarkCase JSON` -> `Adapter` -> `EvaluationRunner` -> `Raw Scores` -> `Configurable Stratifier` -> `Internal Deterministic Report`

## 23. Recommended Implementation Sequence
1. Implement `BenchmarkCaseToGoldenAdapter`.
2. Update the isolated 3F execution path to handle answerability routing, preserving the raw RAG response and emitting `PENDING_POLICY` without selecting, implementing, or implying which evaluation metrics apply to unanswerable cases.
3. Implement `Stratifier` to group raw metric results based on explicitly passed configurations.
4. Define the internal deterministic report structure with pending OD fields.
5. Create synthetic tests proving mechanism behavior without live API calls.

## 24. Red-Team Questions
- If we use the existing `EvaluationRunner`, are we implicitly accepting its existing hardcoded thresholds (`Settings.eval_threshold`)? *Mitigation: The runner must be refactored to execute metrics and report raw scores independently of the threshold-derived `success` boolean.*
- If we adapt `BenchmarkCase` to `GoldenCase`, do we lose the rich metadata needed for stratification? *Mitigation: The adapter must either subclass `GoldenCase` or the Stratifier must keep a reference to the original `BenchmarkCase` by `case_id`.*

## 25. Final GO / NO-GO
**GO.**
Phase 3F mechanisms (Adapter, Configurable Stratification, Raw Reporting, Routing) are safe to build independently of the blocked policies (OD #1, #2, #3, #10) by reusing the existing Phase 1/2 runner.
