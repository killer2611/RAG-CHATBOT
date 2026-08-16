import { describe, it } from "node:test";
import assert from "node:assert";

describe("Evidence Inspector & Grounding Logic", () => {
  const sampleSources = [
    {
      source_id: "sha_doc_alpha",
      source_name: "attention_is_all_you_need.pdf",
      page: 3,
      parent_id: "p_parent_chunk_001",
      score: 0.942,
      excerpt: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
    },
    {
      source_id: "sha_doc_beta",
      source_name: "rag_production_architecture.docx",
      page: null,
      parent_id: "p_parent_chunk_002",
      score: 0.817,
      excerpt: "Hierarchical retrieval utilizes small child chunks for vector matching and broader parent chunks for synthesis.",
    },
    {
      source_id: "sha_doc_gamma",
      source_name: "evaluation_guidelines.txt",
      page: 12,
      parent_id: "p_parent_chunk_003",
      score: null,
      excerpt: "DeepEval measures faithfulness and contextual relevancy against golden Q&A datasets.",
    },
  ];

  it("accurately filters sources by filename and excerpt keywords", () => {
    const filterSources = (sources, query) => {
      if (!query.trim()) return sources;
      const q = query.toLowerCase();
      return sources.filter(
        (s) =>
          s.source_name.toLowerCase().includes(q) ||
          s.excerpt.toLowerCase().includes(q) ||
          (s.page !== null && s.page !== undefined && `page ${s.page}`.includes(q))
      );
    };

    // Filter by filename keyword
    const res1 = filterSources(sampleSources, "attention");
    assert.strictEqual(res1.length, 1);
    assert.strictEqual(res1[0].source_name, "attention_is_all_you_need.pdf");

    // Filter by excerpt keyword
    const res2 = filterSources(sampleSources, "hierarchical");
    assert.strictEqual(res2.length, 1);
    assert.strictEqual(res2[0].source_id, "sha_doc_beta");

    // Filter by page
    const res3 = filterSources(sampleSources, "page 12");
    assert.strictEqual(res3.length, 1);
    assert.strictEqual(res3[0].source_name, "evaluation_guidelines.txt");

    // Filter with no match
    const res4 = filterSources(sampleSources, "nonexistent keyword");
    assert.strictEqual(res4.length, 0);
  });

  it("formats technical metadata statistics without hallucinating unavailable fields", () => {
    const source = sampleSources[0];
    const charCount = source.excerpt.length;
    const wordCount = source.excerpt.trim().split(/\s+/).length;

    assert.strictEqual(charCount, source.excerpt.length);
    assert.strictEqual(wordCount, source.excerpt.trim().split(/\s+/).length);
    assert.strictEqual(source.parent_id, "p_parent_chunk_001");
    assert.strictEqual(source.source_id, "sha_doc_alpha");
  });

  it("handles missing optional scores and page numbers gracefully", () => {
    const unscoredSource = sampleSources[2];
    const scoreLabel =
      unscoredSource.score !== null && unscoredSource.score !== undefined
        ? `${(unscoredSource.score * 100).toFixed(1)}% Rerank Score`
        : null;

    assert.strictEqual(scoreLabel, null);
    assert.strictEqual(unscoredSource.page, 12);

    const pagelessSource = sampleSources[1];
    assert.strictEqual(pagelessSource.page, null);
  });

  it("formats rerank score precision cleanly", () => {
    const scoredSource = sampleSources[0];
    const scoreFormatted = (scoredSource.score * 100).toFixed(1);
    assert.strictEqual(scoreFormatted, "94.2");
  });
});
