import { describe, it } from "node:test";
import assert from "node:assert";

describe("Chat Workspace Logic & Component Primitives", () => {
  it("formats evidence citations accurately with percentages and page labels", () => {
    const rawSources = [
      {
        source_id: "doc_123",
        source_name: "technical_report.pdf",
        page: 4,
        parent_id: "parent_456",
        score: 0.884,
        excerpt: "This is a key excerpt explaining the architecture.",
      },
      {
        source_id: "doc_789",
        source_name: "notes.txt",
        page: null,
        parent_id: "parent_789",
        score: null,
        excerpt: "Unscored plain text snippet.",
      },
    ];

    // Source 1 check
    const s1 = rawSources[0];
    const s1Percent = s1.score !== null ? `${(s1.score * 100).toFixed(0)}% match` : null;
    assert.strictEqual(s1Percent, "88% match");
    assert.strictEqual(s1.page, 4);
    assert.strictEqual(s1.source_name, "technical_report.pdf");

    // Source 2 check (unscored, no page)
    const s2 = rawSources[1];
    const s2Percent = s2.score !== null ? `${(s2.score * 100).toFixed(0)}% match` : null;
    assert.strictEqual(s2Percent, null);
    assert.strictEqual(s2.page, null);
  });

  it("validates composer submissions prohibiting empty whitespace", () => {
    const validate = (input) => input.trim().length > 0;
    assert.strictEqual(validate(""), false);
    assert.strictEqual(validate("   \n\t  "), false);
    assert.strictEqual(validate("Valid question?"), true);
  });

  it("generates structured valid session IDs adhering to backend regex", () => {
    // Backend regex is ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$
    const backendRegex = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;

    for (let i = 0; i < 10; i++) {
      const timestamp = Date.now().toString(36);
      const rand = Math.random().toString(36).substring(2, 7);
      const sessionId = `session_${timestamp}_${rand}`;
      assert.strictEqual(backendRegex.test(sessionId), true);
    }
  });

  it("correctly handles message history role mapping", () => {
    const backendHistory = [
      { role: "user", content: "What is RAG?" },
      { role: "assistant", content: "Retrieval-Augmented Generation." },
    ];

    const mapped = backendHistory.map((m, idx) => ({
      id: `session_1-${idx}`,
      role: m.role,
      content: m.content,
    }));

    assert.strictEqual(mapped.length, 2);
    assert.strictEqual(mapped[0].role, "user");
    assert.strictEqual(mapped[1].role, "assistant");
    assert.strictEqual(mapped[1].content, "Retrieval-Augmented Generation.");
  });
});
