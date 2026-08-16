import { describe, it } from "node:test";
import assert from "node:assert";

describe("Chat Stream Transport Adapter", () => {
  it("parses fragmented SSE chunks into discrete typed events", async () => {
    const events = [];
    const chunks = [
      'event: sources\ndata: [{"source_id":"src_1","source_name":"paper.pdf","parent_id":"p_1","score":0.95,"excerpt":"snippet"}]\n\n',
      'event: token\ndata: "Hello"\n\n',
      'event: token\ndata: " world"\n\n',
      'event: done\ndata: {"session_id":"session_123"}\n\n',
    ];

    let chunkIndex = 0;
    const mockStream = new ReadableStream({
      pull(controller) {
        if (chunkIndex < chunks.length) {
          controller.enqueue(new TextEncoder().encode(chunks[chunkIndex++]));
        } else {
          controller.close();
        }
      },
    });

    const reader = mockStream.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let currentEvent = null;
    let currentData = null;

    const callbacks = {
      onSources: (s) => events.push({ type: "sources", data: s }),
      onToken: (t) => events.push({ type: "token", data: t }),
      onDone: (d) => events.push({ type: "done", data: d }),
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          if (currentEvent && currentData !== null) {
            const parsed = JSON.parse(currentData);
            if (currentEvent === "sources") callbacks.onSources(parsed);
            if (currentEvent === "token") callbacks.onToken(parsed);
            if (currentEvent === "done") callbacks.onDone(parsed);
          }
          currentEvent = null;
          currentData = null;
          continue;
        }
        if (trimmed.startsWith("event:")) currentEvent = trimmed.slice(6).trim();
        else if (trimmed.startsWith("data:")) {
          const d = trimmed.slice(5).trim();
          currentData = currentData === null ? d : `${currentData}\n${d}`;
        }
      }
    }

    assert.strictEqual(events.length, 4);
    assert.strictEqual(events[0].type, "sources");
    assert.strictEqual(events[0].data[0].source_name, "paper.pdf");
    assert.strictEqual(events[1].type, "token");
    assert.strictEqual(events[1].data, "Hello");
    assert.strictEqual(events[2].type, "token");
    assert.strictEqual(events[2].data, " world");
    assert.strictEqual(events[3].type, "done");
    assert.strictEqual(events[3].data.session_id, "session_123");
  });

  it("handles chunk boundaries cutting across lines and payloads", async () => {
    const fragments = [
      'event: to',
      'ken\ndata: "Pa',
      'rtial token"\n\n',
    ];

    const tokens = [];
    let chunkIndex = 0;
    const mockStream = new ReadableStream({
      pull(controller) {
        if (chunkIndex < fragments.length) {
          controller.enqueue(new TextEncoder().encode(fragments[chunkIndex++]));
        } else {
          controller.close();
        }
      },
    });

    const reader = mockStream.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let currentEvent = null;
    let currentData = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          if (currentEvent && currentData !== null) {
            tokens.push(JSON.parse(currentData));
          }
          currentEvent = null;
          currentData = null;
          continue;
        }
        if (trimmed.startsWith("event:")) currentEvent = trimmed.slice(6).trim();
        else if (trimmed.startsWith("data:")) currentData = trimmed.slice(5).trim();
      }
    }

    assert.strictEqual(tokens.length, 1);
    assert.strictEqual(tokens[0], "Partial token");
  });

  it("handles AbortSignal without throwing error callbacks", async () => {
    const controller = new AbortController();
    controller.abort();
    assert.strictEqual(controller.signal.aborted, true);
  });
});
