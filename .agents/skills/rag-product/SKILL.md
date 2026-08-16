---
name: rag-product
description: Keeps frontend behavior aligned with the real RAG pipeline, evidence model, grounding rules, and evaluation system.
---

# RAG Product Skill

## Scope
This skill is about the current RAG flagship project only. Do not import architecture or functionality from the separate HackX/AI Interview Agent project.

## Real pipeline
The validated pipeline is conceptually:

User question
→ history-aware standalone-question reformulation
→ dense vector retrieval
→ parent/child hierarchical retrieval
→ BGE cross-encoder reranking
→ grounded context
→ strict context-only answer
→ evidence returned to UI

## Validated engineering decisions
Documented work identified:
- Answer Relevancy baseline ≈ 0.93
- Contextual Precision baseline ≈ 0.62
- Contextual Recall baseline ≈ 0.75
- Faithfulness baseline ≈ 0.71

The diagnostic conclusion was that retrieval quality was the main weakness, leading to:
- BAAI/bge-reranker-base;
- parent/child chunk optimization;
- stronger overlap;
- strict grounding/abstention;
- controlled evaluation.

Treat these as documented baseline findings, not current live metrics.

## Current target retrieval configuration
Use the production backend as source of truth. The documented target is:
- parent: 800 tokens, 150 overlap;
- child: 300 tokens, 60 overlap;
- initial retrieval: k=10;
- reranked evidence: top 3;
- MiniLM dense embeddings;
- BGE cross-encoder reranking.

Do not change these casually.

## Grounding
The backend's grounding behavior is a product feature.
Never imply that the model knows facts outside supplied context.
If the backend abstains, the UI should present that clearly and professionally.

## Evidence
Only display source data actually returned by the backend.
Do not manufacture:
- relevance scores;
- confidence;
- page numbers;
- citations;
- retrieved chunks;
- model/tool traces.

## Streaming
Current chat streaming is represented by real backend events. Keep the transport layer independent from UI rendering.

Future richer event streams may include:
query_received
query_rewritten
retrieval_started
retrieval_completed
reranking_started
reranking_completed
generation_started
token
sources
done

Do not claim these events exist until the backend actually emits them.

## Evaluation
Evaluation uses DeepEval and can use local Ollama or Gemini judges.
The evaluation system is asynchronous.
The frontend must represent queued/running/completed/failed states and poll responsibly.

Historical metrics must be labeled historical/baseline.
Never fabricate a current score.

## Persistence
Chat/session persistence is a backend concern.
Do not invent browser-only persistence as the authoritative source.

## Product opportunity
The strongest differentiator is observability of genuine retrieval/evidence behavior.
Make the real RAG engineering visible without exposing implementation internals unnecessarily.
