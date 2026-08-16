---
name: frontend-performance
description: Protects runtime speed, streaming smoothness, bundle size, rendering efficiency, and resource cleanup in the flagship frontend.
---

# Frontend Performance Skill

## Priority
Performance is a product feature. Visual sophistication must not create a slow or unstable application.

## Architecture
Prefer:
- Server Components by default;
- Client Components only for genuine interactivity;
- lazy loading for heavy visualizations;
- code splitting for charts/WebGL/evaluation tooling;
- stable component boundaries.

## Streaming
During chat streaming:
- avoid rerendering the entire message list;
- isolate the actively streaming message;
- batch/throttle UI updates if token frequency causes jank;
- keep source rendering separate from token rendering;
- support AbortController cancellation.

## Polling
Evaluation job polling must:
- use a bounded backoff;
- stop immediately on terminal states;
- clean up on unmount/navigation;
- never create duplicate intervals.

Suggested progression:
1s → 2s → 3s → 5s → 5s...

## Effects and resources
Clean up:
- intervals;
- timeouts;
- event listeners;
- observers;
- streams;
- abort controllers;
- WebSocket/SSE connections.

Avoid stale closures and duplicate subscriptions.

## State
Use server-state tools for server state.
Use local React state for local component state.
Use global client state only for genuinely cross-cutting UI state.
Do not introduce multiple global state libraries.

## WebGL
If used:
- lazy-load;
- isolate;
- provide fallback;
- respect reduced motion;
- avoid continuous animation when not visible;
- never block primary content.

## Rendering
Watch for:
- unnecessary context providers;
- unstable props;
- giant component trees;
- expensive derived state;
- key misuse;
- hydration mismatch;
- layout shift.

## Assets
Optimize images and icons.
Avoid giant background assets where CSS/SVG suffices.

## Validation
For substantial changes inspect:
- production build;
- bundle behavior;
- console warnings;
- hydration warnings;
- streaming smoothness;
- mobile performance.

Do not pursue premature micro-optimizations that make the code harder to maintain.
