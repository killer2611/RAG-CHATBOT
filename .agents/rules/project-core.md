---
name: project-core
description: Non-negotiable engineering and workflow rules for the flagship RAG product.
---

# Project Core Rules

## Mission
Build a flagship-grade frontend around the existing production RAG backend. The backend is the source of truth. This project is a RAG knowledge platform, not the separate AI Interview Agent/HackX project.

## Source-of-truth hierarchy
1. Actual repository code and API contracts.
2. `docs/API_CONTRACT.md`
3. `docs/FRONTEND_ARCHITECTURE.md`
4. `docs/PRODUCT_VISION.md`
5. `backend/AUDIT.md` and backend README.
6. Historical source material under `docs/source-material/`.

Historical notebooks/scripts are evidence and regression references, not production entry points.

## Non-negotiables
- Never invent capabilities, metrics, telemetry, citations, confidence, agent traces, or backend events.
- Never expose secrets.
- Never hard-code API URLs or credentials.
- Do not rewrite stable backend behavior merely to simplify frontend work.
- Prefer additive, backwards-compatible backend changes only when genuinely required.
- Preserve the validated RAG behavior: hierarchical parent/child retrieval, dense retrieval, BGE reranking, history-aware rewriting, strict grounding, persistent state.
- Correctness > usability > performance > aesthetics > decoration.
- Accessibility is a release requirement.
- Mobile is a first-class experience.
- Keep dependencies purposeful and minimal.
- Do not add multiple libraries that solve the same problem.
- Keep components focused; avoid giant components.

## Agent workflow
For every phase:
1. Inspect relevant files.
2. State a concise plan.
3. Implement only that phase.
4. Run relevant validation.
5. Inspect the result.
6. Fix regressions.
7. Report what changed, validation performed, and any blockers.
8. Stop.

Do not silently continue into unrelated phases.

## Token efficiency
- Read only files relevant to the current task.
- Reuse established architecture instead of repeatedly re-deriving it.
- Use Context7 for current library APIs when documentation may have changed.
- Prefer one strong implementation pass over repeated speculative rewrites.
- Use the strongest reasoning/model only for architecture, integration failures, performance/security issues, and difficult debugging.
- Use routine execution for straightforward component work.
- Do not repeatedly explain already-established architecture unless a decision changes.

## Validation gates
After meaningful changes, run the smallest relevant checks:
- TypeScript typecheck
- lint
- unit/component tests
- production build for release-level changes
- browser verification for UI changes

Never declare success from compilation alone.

## Change discipline
Before modifying an existing file:
- understand its role;
- preserve public contracts;
- avoid unrelated formatting churn;
- keep diffs reviewable.

Do not use destructive git commands unless explicitly requested.
