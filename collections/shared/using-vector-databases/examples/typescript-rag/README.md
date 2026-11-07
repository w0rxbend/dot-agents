# TypeScript RAG with Hono + Qdrant

Full-stack RAG (Retrieval-Augmented Generation) application using TypeScript, Hono, and Qdrant.

## Stack

- **Backend:** Hono (edge-first framework)
- **Vector DB:** Qdrant
- **Embeddings:** Voyage AI / OpenAI
- **LLM:** OpenAI GPT-4
- **Deployment:** Cloudflare Workers / Vercel

## Files

- `server.ts` - Hono API server
- `rag-chain.ts` - RAG pipeline logic
- `qdrant-client.ts` - Qdrant integration
- `streaming.ts` - SSE streaming responses
- `package.json` - Dependencies

## Setup

```bash
# 1. Install dependencies
npm install

# 2. Start Qdrant (pinned, localhost only, telemetry off)
docker run -p 127.0.0.1:6333:6333 -e QDRANT__TELEMETRY_DISABLED=true qdrant/qdrant:v1.19.2

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run development server
npm run dev
```

## API Endpoints

```bash
# Index documents
curl -X POST http://localhost:3000/api/index \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"text": "...", "metadata": {}}]}'

# RAG query (streaming)
curl http://localhost:3000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is vector search?"}'

# Search only (no LLM)
curl http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "vector databases", "limit": 5}'
```

## Deployment

Deploy only when the user asks; confirm the target first.

### Cloudflare Workers

```bash
WRANGLER_SEND_METRICS=false npm run deploy:cloudflare  # no Wrangler telemetry
```

### Vercel

```bash
VERCEL_TELEMETRY_DISABLED=1 vercel deploy  # no Vercel CLI telemetry
```

See source files for complete implementation.
