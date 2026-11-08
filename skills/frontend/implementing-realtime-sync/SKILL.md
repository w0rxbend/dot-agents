---
name: implementing-realtime-sync
description: Real-time communication patterns for live updates, collaboration, and presence. Use when building chat applications, collaborative tools, live dashboards, or streaming interfaces (LLM responses, metrics). Covers SSE (server-sent events for one-way streams), WebSocket (bidirectional communication), WebRTC (peer-to-peer video/audio), CRDTs (Yjs, Automerge for conflict-free collaboration), presence patterns, offline sync, and scaling strategies. Supports Python, Rust, Go, and TypeScript.
---

# Real-Time Sync

## When to Use

Use when building:

- **LLM streaming interfaces** - Stream tokens progressively (ai-chat integration)
- **Live dashboards** - Push metrics and updates to clients
- **Collaborative editing** - Multi-user document/spreadsheet editing with CRDTs
- **Chat applications** - Real-time messaging with presence
- **Multiplayer features** - Cursor tracking, live updates, presence awareness
- **Offline-first apps** - Mobile/PWA with sync-on-reconnect

## Protocol Selection Framework

### Decision Tree

```
ONE-WAY (Server → Client only)
├─ LLM streaming, notifications, live feeds
└─ Use SSE (Server-Sent Events)
   ├─ Automatic reconnection (browser-native)
   ├─ Event IDs for resumption
   └─ Simple HTTP implementation

BIDIRECTIONAL (Client ↔ Server)
├─ Chat, games, collaborative editing
└─ Use WebSocket
   ├─ Manual reconnection required
   ├─ Binary + text support
   └─ Lower latency for two-way

COLLABORATIVE EDITING
├─ Multi-user documents/spreadsheets
└─ Use WebSocket + CRDT (Yjs or Automerge)
   ├─ CRDT handles conflict resolution
   ├─ WebSocket for transport
   └─ Offline-first with sync

PEER-TO-PEER MEDIA
├─ Video, screen sharing, voice calls
└─ Use WebRTC
   ├─ WebSocket for signaling
   ├─ Direct P2P connection
   └─ STUN/TURN for NAT traversal
```

### Protocol Comparison

| Protocol | Direction | Reconnection | Complexity | Best For |
|----------|-----------|--------------|------------|----------|
| SSE | Server → Client | Automatic | Low | Live feeds, LLM streaming |
| WebSocket | Bidirectional | Manual | Medium | Chat, games, collaboration |
| WebRTC | P2P | Complex | High | Video, screen share, voice |

## Implementation Patterns

### Pattern 1: LLM Streaming with SSE

**Python (FastAPI):**
```python
import json
from sse_starlette.sse import EventSourceResponse

# GET, because the browser EventSource API can only send GET requests.
# For a POST body (long prompts, chat history), stream with fetch() and a
# ReadableStream reader instead of EventSource.
@app.get("/chat/stream")
async def stream_chat(prompt: str):
    async def generate():
        async for chunk in llm_stream(prompt):
            # JSON-encode: a raw newline inside a token would end the SSE event early
            yield {"event": "token", "data": json.dumps(chunk.content)}
        yield {"event": "done", "data": json.dumps("[DONE]")}
    return EventSourceResponse(generate())
```

**Frontend:**
```typescript
const es = new EventSource(`/chat/stream?prompt=${encodeURIComponent(prompt)}`)
es.addEventListener('token', (e) => appendToken(JSON.parse(e.data)))
es.addEventListener('done', () => es.close())
```

Full implementations, reconnection and event ID resumption: `references/sse.md`.

### Pattern 2: WebSocket Chat

**Python (FastAPI):**
```python
connections: set[WebSocket] = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Iterate over a snapshot: other handlers add/remove connections
            # while we await, and a dead peer must not kill this handler
            for conn in list(connections):
                try:
                    await conn.send_text(data)
                except Exception:
                    connections.discard(conn)
    except WebSocketDisconnect:
        pass
    finally:
        connections.discard(websocket)
```

Multi-language examples, authentication, heartbeats and scaling: `references/websockets.md`.

### Pattern 3: Collaborative Editing with CRDTs

**TypeScript (Yjs):**
```typescript
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'

const doc = new Y.Doc()
const provider = new WebsocketProvider('ws://localhost:1234', 'doc-id', doc)
const ytext = doc.getText('content')

ytext.observe(event => console.log('Changes:', event.changes))
ytext.insert(0, 'Hello collaborative world!')
```

Conflict resolution, Yjs vs Automerge and advanced patterns: `references/crdts.md`.

### Pattern 4: Presence Awareness

**Yjs Awareness API:**
```typescript
const awareness = provider.awareness
awareness.setLocalState({ user: { name: 'Alice' }, cursor: { x: 100, y: 200 } })
awareness.on('change', () => {
  awareness.getStates().forEach((state, clientId) => {
    renderCursor(state.cursor, state.user)
  })
})
```

Cursor tracking, typing indicators and online status: `references/presence-patterns.md`.

### Pattern 5: Offline Sync (Mobile/PWA)

Queue mutations locally. Sync when connection restored.

**TypeScript (Yjs + IndexedDB):**
```typescript
import { IndexeddbPersistence } from 'y-indexeddb'
import { WebsocketProvider } from 'y-websocket'

const doc = new Y.Doc()
const indexeddbProvider = new IndexeddbPersistence('my-doc', doc)
const wsProvider = new WebsocketProvider('wss://api.example.com/sync', 'my-doc', doc)

wsProvider.on('status', (e) => {
  console.log(e.status === 'connected' ? 'Online' : 'Offline')
})
```

Conflict resolution and sync strategies: `references/offline-sync.md`.

## Library Recommendations

### Python

**WebSocket:**
- `websockets 13.x` - AsyncIO-based, production-ready
- `FastAPI WebSocket` - Built-in, dependency injection
- `Flask-SocketIO` - Socket.IO protocol with fallbacks

**SSE:**
- `sse-starlette` - FastAPI/Starlette, async, generator-based
- `Flask-SSE` - Redis backend for pub/sub

### Rust

**WebSocket:**
- `tokio-tungstenite 0.23` - Tokio integration, production-ready
- `axum WebSocket` - Built-in extractors, tower middleware

**SSE:**
- `axum SSE` - Native support, async streams

### Go

**WebSocket:**
- `gorilla/websocket` - Battle-tested, compression support
- `nhooyr/websocket` - Modern API, context support

**SSE:**
- `net/http` (native) - Flusher interface, no dependencies

### TypeScript

**WebSocket:**
- `ws` - Native WebSocket server, lightweight
- `Socket.io 4.x` - Auto-reconnect, fallbacks, rooms
- `Hono WebSocket` - Edge runtime (Cloudflare Workers, Deno)

**SSE:**
- `EventSource` (native) - Browser-native, automatic retry
- Node.js `http` (native) - Server-side, no dependencies

**CRDT:**
- `Yjs` - Mature, TypeScript/Rust, rich text editing
- `Automerge` - Rust/JS, JSON-like data, time-travel

## Reconnection Strategies

**SSE:** Browser EventSource reconnects automatically after fixed delay, resending `Last-Event-ID`. Server's `retry:` field sets delay; any backoff beyond that is browser-specific.
**WebSocket:** Add manual exponential backoff with jitter to prevent thundering herd.

Complete implementation patterns: `references/sse.md` and `references/websockets.md`.

## Security Patterns

**Authentication:** Cookie-based (same-origin) or token in Sec-WebSocket-Protocol header. Cookie auth needs an Origin allowlist check before `accept()` (blocks cross-site WebSocket hijacking). Use `wss://` outside localhost.
**Peer data:** Awareness state and relayed messages come from other clients. Render with `textContent`, never `innerHTML`.
**Rate Limiting:** Per-user message throttling with sliding window.

Authentication and rate limiting implementations: `references/websockets.md`.

## Scaling with Redis Pub/Sub

Scale horizontally: broadcast messages across multiple backend servers with Redis pub/sub.

Complete Redis scaling implementation: `references/websockets.md`.

## Frontend Integration

### React Hooks Pattern

**SSE for LLM Streaming (ai-chat):**
```typescript
useEffect(() => {
  const es = new EventSource(`/api/chat/stream?prompt=${encodeURIComponent(prompt)}`)
  es.addEventListener('token', (e) => setContent(prev => prev + JSON.parse(e.data)))
  es.addEventListener('done', () => es.close())
  return () => es.close()
}, [prompt])
```

**WebSocket for Live Metrics (dashboards):**
```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/metrics')
  ws.onmessage = (e) => setMetrics(JSON.parse(e.data))
  return () => ws.close()
}, [])
```

**Yjs for Collaborative Tables:**
```typescript
useEffect(() => {
  const doc = new Y.Doc()
  const provider = new WebsocketProvider('ws://localhost:1234', docId, doc)
  const yarray = doc.getArray('rows')
  yarray.observe(() => setRows(yarray.toArray()))
  return () => provider.destroy()
}, [docId])
```

## Example Projects

- `examples/llm-streaming-sse/` - FastAPI SSE for LLM streaming (runnable; mock mode without API keys)

WebSocket chat and Yjs collaborative editing code: `references/websockets.md` and `references/crdts.md`.

## Testing Tools

- `scripts/test_websocket_connection.py` - WebSocket connection testing
