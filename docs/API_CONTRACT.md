# API Contract — Frontend Integration

This document describes the current intended backend contract. The actual backend implementation remains authoritative if a field differs.

## Base URL

Configured through frontend environment:

`NEXT_PUBLIC_API_URL`

Never hard-code it.

## GET /health

Purpose:
Backend availability check.

Frontend usage:
System status and startup diagnostics.

## POST /chat

Conceptual request:

```json
{
  "session_id": "string",
  "message": "string",
  "stream": false
}
```

Conceptual response:

```json
{
  "session_id": "string",
  "answer": "string",
  "sources": [
    {
      "source_id": "string",
      "source_name": "string",
      "page": 1,
      "parent_id": "string",
      "score": 0.92,
      "excerpt": "string"
    }
  ]
}
```

The frontend must tolerate optional fields where the backend schema permits them.

## Chat streaming

Current design uses Server-Sent Events.

Known event concepts:
- `token`
- `sources`
- `done`

Potential future events:
- `query_received`
- `query_rewritten`
- `retrieval_started`
- `retrieval_completed`
- `reranking_started`
- `reranking_completed`
- `generation_started`
- `error`

Do not render future events until the backend emits them.

The SSE transport must be isolated from the chat UI.

## POST /ingest

Multipart document upload.

Supported:
- PDF
- TXT
- DOCX

Conceptual response:

```json
{
  "source_id": "string",
  "source_name": "string",
  "documents": 0,
  "parents": 0,
  "children": 0,
  "status": "indexed"
}
```

Frontend states should be honest:
uploading → processing → indexed/failed.

If the backend does not provide intermediate processing events, those middle states are client-side activity indicators, not backend telemetry.

## POST /evaluate

Starts an asynchronous evaluation job.

Conceptual request:

```json
{
  "judge": "ollama",
  "test_file": null
}
```

Possible judges:
- `ollama`
- `gemini`

Conceptual response:
HTTP 202 with a job identifier.

## GET /evaluate/{job_id}

Conceptual response:

```json
{
  "job_id": "string",
  "status": "queued",
  "progress": 0,
  "message": "string",
  "created_at": "datetime",
  "completed_at": null,
  "report_path": null,
  "error": null,
  "metadata": {}
}
```

Terminal states:
- completed
- failed

Frontend polling must stop at terminal state.

## Evaluation report

If a report endpoint becomes available, render actual:
- Answer Relevancy
- Contextual Precision
- Contextual Recall
- Faithfulness
- per-case results

Historical baseline values must be explicitly labeled as baseline.

## Error handling

The API layer should normalize:
- network errors
- HTTP errors
- malformed responses
- stream errors
- aborted requests

Never show raw server stack traces to end users.

## Compatibility
The frontend should adapt to backend evolution through a typed API layer rather than coupling components directly to HTTP details.
