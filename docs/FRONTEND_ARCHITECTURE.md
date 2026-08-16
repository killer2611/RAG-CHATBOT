# Frontend Architecture

## High-level architecture

```text
Next.js App Router
        |
        +-- Presentation / Design System
        |
        +-- Client state
        |
        +-- Typed API / Streaming Transport
        |
        v
FastAPI RAG Backend
        |
        +-- Chat
        +-- Ingestion
        +-- Evaluation
        +-- Health
```

## Suggested frontend structure

```text
frontend/
├── app/
│   ├── page.tsx
│   ├── chat/[sessionId]/page.tsx
│   ├── library/page.tsx
│   ├── evaluate/page.tsx
│   ├── system/page.tsx
│   └── settings/page.tsx
├── components/
│   ├── ui/
│   ├── chat/
│   ├── sources/
│   ├── library/
│   ├── evaluation/
│   ├── observability/
│   ├── navigation/
│   └── marketing/
├── lib/
│   ├── api/
│   ├── streaming/
│   ├── hooks/
│   ├── state/
│   └── utils/
└── types/
```

## Core boundaries

### UI
Knows presentation and interaction.

### State
Knows client/server state, not transport details.

### API client
Knows HTTP contracts.

### Streaming adapter
Knows SSE/event decoding.

### Backend
Owns RAG truth, persistence, retrieval, generation, evaluation.

No component should directly implement RAG behavior.

## Chat architecture

```text
Chat UI
  |
  v
chat service / transport
  |
  v
SSE decoder
  |
  +-- token
  +-- sources
  +-- done
  +-- error
  |
  v
normalized chat state
```

Future event types can be added without changing rendering architecture.

## Main screens

### Home
Product story and entry into workspace.

### Chat
Primary product surface. Conversation + evidence.

### Library
Upload and document/index status.

### Evaluation
Launch and monitor asynchronous DeepEval jobs, then visualize real results.

### System
Real health/status signals only.

### Settings
Appearance and user-facing configuration.

## State principles
- Server state belongs in a server-state layer.
- Local interaction state belongs in components/hooks.
- Global client state should be minimal.
- Session identity must be stable and route-safe.
- Do not make browser storage the authoritative chat store.

## Motion
Motion is used to communicate state and hierarchy, not decoration.
Heavy visuals are isolated and lazy-loaded.

## Responsive architecture
Desktop may use three-panel chat.
Tablet may use two-panel chat.
Mobile uses drawers/bottom sheets for secondary information.

## Backend modification policy
Do not change backend behavior unless frontend integration requires it.
Preferred future additive endpoints/events:
- document listing/status
- session listing
- evaluation report retrieval
- richer streaming lifecycle events

Only add them when the current UI genuinely needs them.
