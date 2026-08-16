---
name: frontend-qa
description: Verifies the flagship frontend through functional, responsive, accessibility, and browser-level testing.
---

# Frontend QA Skill

## Goal
Verify the real product, not merely that TypeScript compiles.

## Critical path
Test:
1. open application;
2. load workspace;
3. upload supported document;
4. observe ingestion result;
5. create/open chat session;
6. send question;
7. receive streamed answer;
8. inspect evidence;
9. start evaluation;
10. observe queued → running → completed/failed.

## UI states
Verify every major surface for:
- loading;
- empty;
- success;
- partial data;
- failure;
- retry;
- disabled;
- streaming;
- cancellation.

## Responsive matrix
Check:
- desktop 1440px+;
- 1280px;
- tablet;
- 430px;
- 390px;
- 360px.

Look for:
- overflow;
- clipped text;
- broken sticky regions;
- inaccessible dialogs;
- unusable evidence panels;
- composer problems.

## Accessibility
Verify:
- keyboard navigation;
- focus visibility;
- semantic controls;
- dialog behavior;
- screen-reader labels;
- contrast;
- reduced motion.

## Browser verification
Use browser/Playwright tooling when available.
Prefer real browser verification over assumptions.

## Regression discipline
After a fix:
- reproduce the original problem;
- verify the fix;
- check adjacent functionality;
- avoid unrelated refactors.

## Evidence discipline
Never approve fake metrics, fake telemetry, fake source scores, fake citations, or fake backend states.

## Completion gate
A phase is complete only when:
- relevant tests pass;
- no new console/hydration errors;
- critical interaction works;
- responsive behavior is acceptable;
- no obvious accessibility regression;
- result has been visually inspected when UI changed.
