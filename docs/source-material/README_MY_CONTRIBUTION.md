# RAG Pipeline Evaluation, Retrieval Optimization & Local LLM Benchmarking

> **Contribution:** Retrieval-quality diagnosis, RAG optimization, grounding improvements, and DeepEval/Ollama benchmarking reliability.

This contribution focuses on a part of the RAG system that is easy to underestimate but critical in practice:

**getting the right information into the LLM, in the right order, with enough context, and evaluating that behavior reliably on local hardware.**

The work was driven by measurement rather than guesswork. DeepEval was used to identify where the pipeline was actually failing, after which the retrieval, chunking, grounding, and evaluation stack were tuned to address those failure modes.

---

## 1. What I Worked On

My contribution covered four connected areas:

| Area | What was addressed | Why it mattered |
|---|---|---|
| **RAG quality diagnosis** | Analyzed DeepEval metrics and isolated retrieval as the main bottleneck | Prevented us from incorrectly blaming the LLM |
| **Retrieval ranking** | Added a **BAAI/bge-reranker-base Cross-Encoder** after vector retrieval | Improved the ordering of relevant chunks |
| **Chunking & context continuity** | Reworked parent/child chunk sizes and overlap | Reduced facts being lost at chunk boundaries |
| **Grounded QA + evaluation reliability** | Added strict context-only answering rules and optimized DeepEval/Ollama execution | Reduced hallucination risk and made local benchmarking practical |

The central engineering insight was:

> **A strong LLM cannot compensate for bad retrieval.**

The baseline showed that the model could answer relevantly, but the retrieval layer was feeding it noisy and incomplete evidence. The fixes therefore targeted the retrieval and evaluation pipeline rather than blindly changing the generation model.

---

## 2. Baseline: What the Evaluation Told Us

DeepEval exposed four important dimensions of RAG quality:

| Metric | Baseline | What it tells us | Main finding |
|---|---:|---|---|
| **Answer Relevancy** | **0.93** | Whether the answer directly addresses the question | Generation and prompt adherence were already strong |
| **Contextual Precision** | **0.62** | Whether the most useful chunks are ranked near the top | **Major weakness: irrelevant chunks were outranking the answer** |
| **Contextual Recall** | **0.75** | Whether the retrieved context contains the facts required to answer | Facts were being lost during chunking |
| **Faithfulness** | **0.71** | Whether the answer stays supported by retrieved context | Retrieval gaps/noise increased hallucination risk |

The evidence pointed to a specific conclusion:

**The language model was not the primary problem. Retrieval quality was.**

The baseline had strong Answer Relevancy, while Contextual Precision and Faithfulness were substantially weaker. This meant the system could formulate a good answer when given useful information, but it was not consistently selecting or preserving the right information first.

---

## 3. Fix #1 — Cross-Encoder Reranking

### Problem

The original retrieval stage relied on vector similarity. Embedding search is fast and useful for candidate generation, but semantic similarity alone can still place a merely related chunk above the chunk that contains the exact answer.

That showed up directly in the low Contextual Precision score.

### What I changed

Added:

**`BAAI/bge-reranker-base`**

as a second-stage reranker after initial retrieval.

### Architecture

```text
User Question
     │
     ▼
Embedding / Vector Retrieval
     │
     ▼
Top Candidate Chunks
     │
     ▼
BGE Cross-Encoder Reranker
     │
     ▼
Re-ranked Relevant Chunks
     │
     ▼
LLM
     │
     ▼
Grounded Answer
```

### Why this works

Vector retrieval asks, approximately:

> “How similar are this query embedding and this document embedding?”

A cross-encoder instead evaluates the **query and candidate chunk together**, allowing a stronger interaction-based relevance score.

The reranker therefore acts as a precision layer:

**retrieve broadly → score deeply → put the best evidence first.**

### Expected impact

This directly targets the failure mode behind the **0.62 Contextual Precision** baseline by improving the ordering of retrieved evidence.

---

## 4. Fix #2 — Chunking Strategy Optimization

### Problem

The earlier chunking configuration used an extremely small overlap of **20 characters**.

That is risky when a fact, explanation, or sentence crosses a chunk boundary.

For example:

```text
Chunk A:
"The system authenticates the user using a
multi-factor security mechanism that..."

Chunk B:
"...requires a second verification step."
```

The meaning is split across boundaries.

That can lower Contextual Recall even when the source document itself contains the answer.

### What I changed

The documented configuration was adjusted to:

- **Parent chunks:** 800 tokens
- **Parent overlap:** 150 tokens (~18%)
- **Child chunks:** 250–300 tokens
- **Child overlap:** 50–80 tokens (~20%)

This preserves more context across boundaries while still keeping retrieval units reasonably focused.

### Why parent + child chunks?

The resulting strategy can be understood as:

```text
Large Parent Context
        │
        ├── Child Chunk 1
        ├── Child Chunk 2
        ├── Child Chunk 3
        └── ...
```

The larger parent maintains broader context, while smaller child chunks provide more focused retrieval.

### Engineering objective

The goal was not simply “make chunks bigger.”

The goal was:

> **Preserve enough semantic continuity that important facts survive splitting, while keeping retrieval focused enough to remain useful.**

This directly addresses the **0.75 Contextual Recall** baseline and the documented observation that roughly **25–40% of required facts could be lost at split boundaries**.

---

## 5. Fix #3 — Strict Grounding Guardrail

### Problem

When retrieval misses information, an LLM may attempt to be helpful by filling gaps from its general knowledge.

That creates a dangerous RAG failure mode:

```text
Missing evidence
      ↓
LLM tries to help
      ↓
Unsupported inference
      ↓
Hallucinated answer
```

### What I changed

The QA prompt was tightened so the model must:

1. Answer **only from the supplied context**
2. Avoid assumptions and extrapolation
3. Explicitly say when the provided context is insufficient

The documented guardrail is:

> “Answer ONLY based on the provided context. If the context does not contain the answer, state that you do not have enough information.”

### Why this matters

This turns the LLM from a general-purpose guesser into a more controlled **context-grounded answer generator**.

It does not magically fix retrieval. Instead, it prevents poor retrieval from being silently converted into confident unsupported claims.

This was an important complement to the retrieval fixes.

---

## 6. Fix #4 — Making DeepEval Work on Local Hardware

The evaluation stack itself had a performance problem.

### Why the benchmark was stalling

Two constraints interacted:

#### 1. GPU/CPU layer splitting

The local machine had approximately **6 GB VRAM**, while the evaluated 14B model required about **10 GB** of memory.

The documented behavior was that Ollama offloaded roughly **59%** of the model workload to CPU/system RAM, reducing generation speed to roughly:

**2–5 tokens/sec**

That made multi-metric evaluation extremely slow.

#### 2. Async concurrency overload

DeepEval attempted to execute multiple metric checks concurrently.

Running several expensive local LLM judgments at once created memory contention and could freeze or stall the Ollama process.

### What I changed

#### Sequential evaluation

Configured:

```python
AsyncConfig(
    max_concurrent=1,
    throttle_value=1
)
```

This forces evaluation work through a controlled one-at-a-time execution path.

#### Timeout handling

Added:

```python
os.environ["DEEPEVAL_DISABLE_TIMEOUTS"] = "1"
```

This prevents premature timeout termination during slow local inference.

#### Right-sized evaluation judge

Instead of using the larger local model as the evaluator, the documented setup switched the judge toward a **7B/8B model**, such as:

- `qwen2.5-coder`
- `deepseek-r1:8b`

The documented expectation was that this size could fit within the available 6 GB VRAM and reach roughly **35–45 tokens/sec**, versus the much slower split-execution behavior of the 14B model.

### Resulting principle

> **Benchmark configuration has to respect hardware constraints.**

Rather than scaling hardware just to make evaluation work, the evaluation workload was made compatible with the machine.

The documented result was a reduction from roughly **20+ minute stalled evaluations to a few minutes**.

---

## 7. The Resulting Pipeline

Putting the improvements together:

```text
                    ┌─────────────────┐
                    │   User Query    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Vector Retrieval│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Candidate Chunks│
                    └────────┬────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ BGE Cross-Encoder    │
                  │      Reranker        │
                  └──────────┬───────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Re-ranked Context│
                    └────────┬────────┘
                             │
                             ▼
              ┌────────────────────────────┐
              │ Strict Context-Only QA     │
              │ - no guessing              │
              │ - no extrapolation         │
              │ - admit missing evidence   │
              └──────────────┬─────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Grounded Answer │
                    └─────────────────┘


         ┌─────────────────────────────────────┐
         │             DeepEval                │
         │ Relevancy / Precision / Recall /    │
         │ Faithfulness                         │
         └─────────────────────────────────────┘
                         │
                         ▼
              Controlled local execution
              max_concurrent = 1
```

---

## 8. Why This Contribution Matters

This was more than parameter tuning.

The work introduced a **measurement → diagnosis → targeted fix → re-evaluation** workflow.

### Before

```text
RAG answers look okay
        ↓
Assume the LLM is the problem
        ↓
Try another model
```

### Engineering approach used here

```text
Measure with DeepEval
        ↓
Identify the weak metric
        ↓
Trace the failure to retrieval/chunking
        ↓
Apply targeted fix
        ↓
Make evaluation hardware-aware
        ↓
Re-test
```

That is a much more defensible engineering workflow because every optimization has a reason tied to an observed failure mode.

---

## 9. Key Technical Terms I Worked With

**RAG — Retrieval-Augmented Generation**  
A pipeline where relevant external/document context is retrieved and supplied to an LLM before generation.

**Embedding / Vector Retrieval**  
A fast candidate-generation approach based on semantic similarity between vector representations.

**Cross-Encoder Reranker**  
A model that examines the query and candidate document chunk together and produces a more precise relevance score.

**ParentDocumentRetriever**  
A retrieval strategy that combines focused child chunks with broader parent context.

**Chunk Overlap**  
Shared content between adjacent chunks that helps preserve meaning across boundaries.

**Contextual Precision**  
Measures whether the most relevant retrieved information is ranked highly.

**Contextual Recall**  
Measures whether the information necessary to answer the question was successfully retrieved.

**Faithfulness**  
Measures whether the generated answer is supported by the retrieved context rather than unsupported model knowledge.

**DeepEval**  
An evaluation framework used here to benchmark RAG quality.

**Ollama**  
The local model runtime used for model inference and evaluation.

---

## 10. Contribution Snapshot

### Diagnosis
- Identified retrieval quality—not raw LLM capability—as a core bottleneck.
- Interpreted DeepEval metrics to connect symptoms to pipeline stages.

### Retrieval
- Added **BAAI/bge-reranker-base** cross-encoder reranking.
- Introduced a two-stage retrieval flow: candidate retrieval followed by relevance re-ranking.

### Context Engineering
- Optimized parent/child chunk sizes.
- Increased overlap to roughly the **20% range** to protect context continuity.

### Grounding
- Added strict context-only answer constraints.
- Added an explicit abstention behavior for missing information.

### Evaluation Infrastructure
- Identified local VRAM limits and model offloading as a benchmark bottleneck.
- Controlled DeepEval concurrency with `max_concurrent=1`.
- Disabled premature evaluation timeouts.
- Right-sized the evaluation judge to a 7B/8B class local model.

### Engineering Mindset
- Used evaluation metrics to drive changes.
- Focused on root cause rather than swapping models blindly.
- Optimized both **answer quality** and **benchmark reliability**.

---

## 11. One-Line Contribution Statement

> **I diagnosed the RAG pipeline using DeepEval, identified retrieval precision, context loss, and local evaluation bottlenecks, then improved the system with cross-encoder reranking, overlap-aware parent/child chunking, strict grounding, and hardware-aware DeepEval execution.**

---

## 12. 30-Second Version

> **“I worked primarily on the retrieval and evaluation side of the RAG pipeline. DeepEval showed that Answer Relevancy was already strong at 0.93, but Contextual Precision was only 0.62 and Faithfulness was 0.71. I traced that to noisy ranking, context being lost during chunking, and local evaluation bottlenecks. I added a BGE cross-encoder reranker, optimized parent/child chunk sizes and overlaps, enforced strict context-only answering, and throttled DeepEval to fit the local GPU. So the contribution was essentially turning the RAG pipeline from ‘it can answer’ into a more measurable, retrieval-aware, grounded, and locally testable system.”**

---

## 13. Evidence & Source

This README is based on the supplied technical contribution document describing the DeepEval diagnosis, reranking strategy, chunking changes, grounding guardrails, hardware bottlenecks, and benchmark optimizations.
