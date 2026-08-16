---
name: flagship-ui
description: Design and implement the premium, original, accessible interface for the flagship RAG knowledge platform.
---

# Flagship UI Skill

## Goal
Create an interface that feels like serious AI infrastructure rather than a generic chatbot template.

Reference quality bar:
- Vercel-level restraint
- Linear-level information hierarchy
- Raycast-level interaction quality
- Perplexity-like evidence clarity
- original visual identity

Use these as quality references, not copies.

## Product story
The interface should make this real system legible:

documents
→ ingestion
→ query
→ history-aware reformulation
→ retrieval
→ reranking
→ grounded generation
→ evidence
→ evaluation

## Visual language
Prefer:
- sophisticated dark-first theme with excellent light mode;
- restrained graphite/slate surfaces;
- crisp typography;
- one controlled accent family;
- mono typography for technical metadata;
- subtle depth;
- high-quality spacing and alignment.

Avoid:
- generic purple AI gradients;
- excessive glassmorphism;
- glowing cards everywhere;
- random blobs;
- fake futuristic HUDs;
- excessive rounded cards;
- stock AI imagery;
- decorative elements with no semantic purpose.

## Motion
Use Motion for React when it improves hierarchy or state communication.
Good uses:
- route transitions;
- evidence expansion;
- streaming states;
- upload/evaluation state;
- active navigation;
- subtle hero motion.

Rules:
- short and responsive for interaction;
- spring-based where appropriate;
- interruptible;
- respect prefers-reduced-motion;
- never let decorative animation block content.

## Hero
A restrained knowledge/retrieval visualization is welcome.
If using Canvas/WebGL/Three.js:
- lazy-load it;
- isolate it from core UI;
- preserve immediate text/content rendering;
- reduce or disable it for mobile/reduced-motion;
- never use it merely because 3D looks impressive.

## Chat
Chat is the flagship product surface.
It must support:
- excellent streaming;
- Markdown/code/tables;
- clear message hierarchy;
- abort/error states;
- source/evidence inspection;
- responsive layouts.

Do not rerender the entire conversation on every token.

## Evidence
Make real source metadata highly visible:
- document;
- page;
- excerpt;
- real retrieval/reranking score if provided.

Never fabricate confidence.

## Advanced views
Retrieval inspector and evaluation lab should feel like professional AI tooling, not generic dashboards.

## Empty/loading/error states
Every major surface gets a deliberate state.
States must tell the user what happened and what to do next.

## Accessibility
Use semantic controls and accessible primitives.
Support keyboard navigation, focus visibility, dialogs, reduced motion, contrast, and screen readers.

## Responsive
Design intentionally for desktop, tablet, and mobile.
Do not simply collapse desktop into a narrow column.
Evidence inspection must remain usable on mobile.

## Design-system discipline
Create reusable tokens and primitives before duplicating styling.
Prefer composition over one-off hacks.
If a screen looks like a generic AI template, redesign it.
