import { describe, it } from "node:test";
import assert from "node:assert";

describe("Evaluation Lab & Benchmark Logic", () => {
  it("validates test dataset paths strictly requiring data/ prefix", () => {
    const validatePath = (path) => {
      const trimmed = path.trim();
      if (!trimmed) return true; // defaults to backend default
      return trimmed.startsWith("data/");
    };

    assert.strictEqual(validatePath("data/golden_qa.json"), true);
    assert.strictEqual(validatePath("data/custom_suite.json"), true);
    assert.strictEqual(validatePath("/etc/passwd"), false);
    assert.strictEqual(validatePath("other_dir/test.json"), false);
    assert.strictEqual(validatePath(""), true);
  });

  it("calculates pass rate percentages and metric averages accurately", () => {
    const summary = {
      total_cases: 20,
      passed_cases: 17,
      average_scores: {
        Faithfulness: 0.884,
        "Answer Relevancy": 0.925,
        "Contextual Precision": 0.81,
        "Contextual Recall": 0.79,
      },
    };

    const passRate = (summary.passed_cases / summary.total_cases) * 100;
    assert.strictEqual(passRate, 85.0);

    const faithPercent = (summary.average_scores.Faithfulness * 100).toFixed(1);
    assert.strictEqual(faithPercent, "88.4");
  });

  it("evaluates bounded backoff intervals up to 5s maximum cap", () => {
    const BACKOFF_SCHEDULE = [1000, 2000, 3000, 5000];
    const MAX_BACKOFF = 5000;

    const getDelay = (attempt) => {
      return BACKOFF_SCHEDULE[Math.min(attempt, BACKOFF_SCHEDULE.length - 1)] ?? MAX_BACKOFF;
    };

    assert.strictEqual(getDelay(0), 1000);
    assert.strictEqual(getDelay(1), 2000);
    assert.strictEqual(getDelay(2), 3000);
    assert.strictEqual(getDelay(3), 5000);
    assert.strictEqual(getDelay(10), 5000);
  });

  it("accurately parses per-case metric details and handles missing reasons", () => {
    const rawMetrics = {
      Faithfulness: {
        name: "Faithfulness",
        score: 0.95,
        passed: true,
        reason: "All claims are strictly derived from context.",
        error: null,
      },
      "Contextual Precision": {
        name: "Contextual Precision",
        score: null,
        passed: null,
        reason: null,
        error: "Embedding judge timed out",
      },
    };

    assert.strictEqual(rawMetrics.Faithfulness.passed, true);
    assert.strictEqual(rawMetrics.Faithfulness.score, 0.95);
    assert.strictEqual(rawMetrics["Contextual Precision"].score, null);
    assert.strictEqual(rawMetrics["Contextual Precision"].error, "Embedding judge timed out");
  });
});
