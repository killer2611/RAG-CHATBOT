# Decision Record: OD #11 — Benchmark Population Floor

## Status

**RESOLVED — v1.0**

Resolved as part of Phase 5c. Provides population semantics required
before `run_benchmark.py` (Phase 5d) can be implemented.

This record does not resolve any other Open Decision.

---

## Context

The Phase 3 pipeline produces candidates through:

```
Phase 3B: candidate generation     (n_generated ≤ 30 per run)
Phase 3C: claim verification       (claim-level support_status)
Phase 3D: case aggregation         (case-level verdict via OD #10)
Phase 3D: artifact writing         (ArtifactWriter.write_case())
```

After Phase 5b, `CaseAggregator` produces one of three verdict states:
`accepted`, `rejected`, or `disputed`. `ArtifactWriter` validates and
writes accepted cases to disk.

Until this decision, no policy existed for:
- which verdicts constitute admission to the benchmark population
- what the minimum viable population size is
- what happens when that minimum is not reached
- how generated candidates, admitted cases, and benchmark population
  are distinguished from each other in code and reporting
- what constitutes an accounting failure vs. a population-floor failure

---

## Definitions

All terms below are authoritative. Implementations must use these
names exactly for counters, fields, and log messages.

**`n_generated`**
Count of candidates emitted by `CandidateGenerator` and entering the
post-generation pipeline classification boundary. Once a candidate
crosses this boundary, it receives exactly one terminal accounting
bucket. A candidate must never: disappear silently; be counted twice;
fall into two buckets simultaneously; or fall outside the accounting
system.

Upper-bounded by the Phase 3B generator cap (30 per run, not changed
by this decision).

**`n_admitted`**
Candidates where all of the following hold:
- `CaseAggregator` produced `verdict == "accepted"`, AND
- `ArtifactWriter.write_case()` completed without raising, AND
- The `case_id` has not been seen earlier in this run (unique)

`n_admitted ≤ n_generated`.

**`n_rejected`**
Candidates explicitly excluded by pipeline policy. Includes:
- `CaseAggregator` produced `verdict == "rejected"` (ADR Rules 2, 3)
- `BenchmarkAdmissionError` raised by `CorpusEnricher` (Option A
  corpus_position policy from Phase 3B-3)

`n_rejected ≤ n_generated`.

**`n_disputed`**
Candidates where `CaseAggregator` produced `verdict == "disputed"`
(secondary verification failed, unavailable, or returned an
unparseable response per OD #10, Correction 1). Excluded from the
benchmark population. NOT counted as rejected (they are a distinct
diagnostic category, not a policy rejection).

`n_disputed ≤ n_generated`.

**`n_pipeline_errors`**
Candidates that raised an unexpected exception during processing,
including but not limited to:
- `StructuralValidationError` from Phase 3C
- `ArtifactWriter.write_case()` raising `ValueError` (schema
  validation failure — indicates upstream defect, not policy)
- Duplicate `case_id` encountered within the same run (integrity
  defect — must never silently overwrite an existing artifact)
- Unhandled exceptions from any pipeline stage

These are tracked with diagnostic information. They represent pipeline
defects, not policy outcomes.

`n_pipeline_errors ≤ n_generated`.

**`benchmark_population`**
The set of `.json` files written by `ArtifactWriter`. Exactly equal
in size to `n_admitted`.

**`admission_rate`**
`n_admitted / n_generated`. A float in [0.0, 1.0].

---

## The Accounting Invariant

```
n_generated =
    n_admitted
  + n_rejected
  + n_disputed
  + n_pipeline_errors
```

This invariant MUST hold after every run. If it does not, the pipeline
has a counting bug. This is not a boundary condition to handle — it is
a pipeline defect to be immediately surfaced.

---

## Decision

### Rule 1 — Admission Criteria

A candidate is admitted to the benchmark population if and only if:

1. `CaseAggregator.aggregate()` set `verification.verdict == "accepted"`, AND
2. `ArtifactWriter.write_case()` completed without raising, AND
3. The `case_id` has not been seen earlier in this run

All other outcomes are excluded:

| Outcome | Counter | Admitted? |
|---------|---------|-----------|
| `verdict == "accepted"` + written + unique | `n_admitted` | ✅ |
| `verdict == "rejected"` | `n_rejected` | ❌ |
| `verdict == "disputed"` | `n_disputed` | ❌ |
| `BenchmarkAdmissionError` | `n_rejected` | ❌ |
| Duplicate `case_id` | `n_pipeline_errors` | ❌ |
| `ArtifactWriter` schema validation failure | `n_pipeline_errors` | ❌ |
| Any unexpected exception | `n_pipeline_errors` | ❌ |

**`disputed` cases are NOT admitted and NOT rejected.**
`disputed` is a distinct diagnostic state: the automated system could
not reach a verdict (secondary verification failed). These cases are
tracked under `n_disputed` so secondary-verification failures are
observable rather than silently absorbed. They require human review
before any admission decision can be made (OD #7, still open).

### Rule 2 — Population Floor by Mode

| Mode | `min_floor` | Intended use |
|------|------------|--------------|
| `smoke` | 5 | Quick development validation |
| `standard` | 10 | Default; general benchmark generation |
| `comprehensive` | 20 | Full evaluation suite |

Default mode: `standard`.

Mode is a per-invocation CLI parameter, not a system-level setting.
It is NOT stored in `Settings`.

### Rule 3 — Run Processing Sequence

Every run MUST execute these steps in order:

```
1. Generate candidates (n_generated ← count)

2. For each candidate, classify into exactly one bucket:
   admitted / rejected / disputed / pipeline_error

3. ACCOUNTING GATE:
   Verify: n_admitted + n_rejected + n_disputed + n_pipeline_errors
           == n_generated

   If FALSE:
     → This is a PIPELINE BUG.
     → Stop immediately.
     → Do NOT write the manifest.
     → Do NOT raise BenchmarkPopulationError.
     → Raise a distinct exception (e.g., AssertionError or a new
       PipelineAccountingError) that clearly names this as an
       implementation defect, not a population-floor failure.

   If TRUE:
     → Proceed to step 4.

4. WRITE MANIFEST:
   Write manifest.json with full statistics regardless of whether the
   floor is met. Mark `population_admitted: true` or
   `population_admitted: false`. See Rule 5.

5. POPULATION FLOOR CHECK:
   If n_admitted < min_floor:
     → Raise BenchmarkPopulationError.
     → Preserve all artifacts already on disk.
     → Preserve the manifest.
     → Do NOT delete anything.

   If n_admitted >= min_floor:
     → Return normally.
```

### Rule 4 — Artifact Preservation

When `BenchmarkPopulationError` is raised, the `.json` files already
written by `ArtifactWriter` remain on disk. They are valid benchmark
cases. The error signals that the run did not produce a complete
admissible benchmark population, not that the individual cases are
invalid.

**"Population failure" ≠ "artifact invalidation."**

The run's manifest (Rule 5, with `population_admitted: false`) is also
preserved. This gives the caller both the individual valid artifacts
and the run-level accounting explaining why the population target
was not met.

The implementation MUST NOT delete artifacts merely because the floor
was missed. No cleanup on failure.

### Rule 5 — Run Manifest Schema

```json
{
  "schema_version": "1",
  "run_id": "<uuid>",
  "timestamp_utc": "<ISO-8601>",
  "mode": "standard",
  "document_path": "<path>",
  "document_hash": "<sha256-of-raw-bytes>",
  "git_commit": "<sha>",
  "model_versions": {
    "generator_model": "<str>",
    "verifier_primary_model": "<str>",
    "verifier_secondary_model": "<str>"
  },
  "population": {
    "n_generated": 10,
    "n_admitted": 7,
    "n_rejected": 2,
    "n_disputed": 1,
    "n_pipeline_errors": 0,
    "admission_rate": 0.7,
    "min_floor": 10,
    "population_admitted": false
  },
  "per_case_verdicts": [
    {
      "case_id": "<str>",
      "verdict": "accepted",
      "artifact_path": "<relative-path>"
    },
    {
      "case_id": "<str>",
      "verdict": "rejected"
    },
    {
      "case_id": "<str>",
      "verdict": "disputed"
    }
  ]
}
```

The manifest is written in step 4 (after the accounting gate, before
the floor check). It is written regardless of whether `population_admitted`
is true or false.

`admission_rate` = `n_admitted / n_generated`. Computed and stored.

The accounting invariant must hold before any manifest is written:
`n_admitted + n_rejected + n_disputed + n_pipeline_errors == n_generated`.
A manifest written with a broken invariant is never acceptable.

### Rule 6 — New Exception: `BenchmarkPopulationError`

Added to `app/evaluation/exceptions.py`:

```python
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
```

### Rule 7 — Terminology Enforcement

These substitutions are forbidden in all code, docstrings, and output:

| Forbidden | Correct |
|-----------|---------|
| "accepted cases" to mean all pipeline output | `n_admitted` or `benchmark_population` |
| "generated cases" to mean admitted cases | `n_generated` |
| Treating `n_disputed` as a subset of `n_rejected` | they are separate counters |
| `admission_rate = n_admitted / n_admitted` | `admission_rate = n_admitted / n_generated` |

---

## Two-Tier Failure Model

```
ACCOUNTING GATE
       │
  invariant?
  ┌────┴────┐
 NO        YES
  │         │
  ▼         ▼
PIPELINE  WRITE MANIFEST
  BUG     (population_admitted: true/false)
  STOP         │
           FLOOR CHECK
           ┌────┴────┐
          YES        NO
           │         │
           ▼         ▼
        RETURN    BenchmarkPopulationError
        SUCCESS        │
                       ▼
                 PRESERVE ARTIFACTS
                 PRESERVE MANIFEST
                 BENCHMARK NOT ADMITTED
```

Accounting failure and population-floor failure are different conditions
with different error types and different behaviors. They must never be
conflated in code or error messages.

---

## Consequences

### What Phase 5c delivers

1. `docs/decisions/OD-11-benchmark-population.md` (this document)
2. `BenchmarkPopulationError` added to `app/evaluation/exceptions.py`

No other files change in Phase 5c.

### What Phase 5d (`run_benchmark.py`) implements

- Accepts `--mode smoke|standard|comprehensive` (default: `standard`)
- Processes candidates through the existing 3A–3D pipeline
- Accumulates four counters per candidate
- Applies the accounting gate, manifest write, and floor check in order
- Raises `BenchmarkPopulationError` when floor not met
- Never deletes artifacts on failure

### What does not change

- `benchmark_case.schema.json` — frozen, SHA unchanged
- `CaseAggregator`, `ArtifactWriter`, `CorpusEnricher` — unchanged
- Generator cap (30 per run) — Phase 3B, not changed here
- OD #1, #2, #3, #4, #5, #7, #8, #9, #12 — all remain open

---

## Alternatives Considered

**Count `disputed` under `n_rejected`:** Rejected. Policy rejection
and secondary-verification failure are operationally different. A
high `n_disputed` rate signals secondary-model reliability issues.
A high `n_rejected` rate signals benchmark construction quality issues.
Conflating them destroys diagnostic value.

**Delete artifacts on population failure:** Rejected. Valid admitted
artifacts are the product of correct pipeline execution. Population
failure means the run produced fewer artifacts than required, not that
the artifacts themselves are wrong. Cleanup on failure would destroy
diagnostic value and is architecturally wrong.

**Configurable floor via Settings:** Rejected. The floor is a per-run
choice, not a system policy. CLI parameter is the right granularity.

**Write manifest only on success:** Rejected. The manifest is the
primary diagnostic artifact for a failed run. Writing it only on
success makes the failure harder to diagnose. Mark `population_admitted`
instead.

---

## Open Decisions Resolved

| OD | Description | Resolution |
|----|-------------|------------|
| OD #11 | Accepted-case count / benchmark population floor | Rules 1–7 above |

## Open Decisions Remaining (unchanged)

| OD | Description |
|----|-------------|
| OD #1 | DeepEval metric thresholds |
| OD #2 | Abstention Accuracy formula |
| OD #3 | Bootstrap / CI methodology |
| OD #4 | Cache implementation |
| OD #5 | Evidence overlap algorithm |
| OD #7 | Human-review interface / disagreement signal |
| OD #8 | CLI/API surface |
| OD #9 | Benchmark versioning convention |
| OD #12 | Candidate determinism policy |

---

## Phase 5c Boundary

Phase 5c delivers exactly:
1. `docs/decisions/OD-11-benchmark-population.md` (this document)
2. `BenchmarkPopulationError` in `app/evaluation/exceptions.py`

Phase 5d (`run_benchmark.py`) implements this policy.
Phase 5d does NOT begin until Phase 5c is committed to `main`.
