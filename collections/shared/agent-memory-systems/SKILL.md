---
name: agent-memory-systems
description: "Design an agent's short-term and persistent memory: which memory types to keep, how to chunk and store them, how to score retrieval (metadata filters, hybrid search, recency, importance), lifecycle and eviction, and how to evaluate recall. Use when an agent must remember across turns or sessions and you need a concrete storage/retrieval design; use context-engineering for in-session context hygiene and using-vector-databases for vector store operations."
source: vibeship-spawner-skills (Apache 2.0)
---

# Agent Memory Systems

When agent "forgets" or contradicts itself, cause is usually retrieval, not storage: right item stored but not fetched, or stale item outranked it. Design read path first, then decide what to write.

## 1. Decide whether you need persistent memory

| Need | Simplest adequate design |
|---|---|
| Continuity within one task or session | Conversation itself, summarized as it grows (context-engineering) |
| Handful of stable facts per user (name, preferences, settings) | Structured profile row/document, loaded whole into prompt |
| Project or task state outliving session | Files or DB rows agent reads at start (plan, status, decisions) |
| Recall over many past interactions or large document corpus | Retrieval store (vector and/or keyword index) with procedure below |

Do not add vector store when profile row or status file answers the question; they are cheaper, exact and debuggable.

## 2. Separate memory types

| Type | Holds | Store | Read pattern |
|---|---|---|---|
| Working | Current task, recent turns, scratch results | Context window | Always present; summarized when long |
| Semantic | Stable facts and preferences ("user deploys with Helm") | Structured store (KV/relational/document) keyed by subject | Exact lookup by user/project, loaded whole when small |
| Episodic | What happened: past sessions, decisions, outcomes, timestamped | Append-only log + retrieval index | Similarity + recency, filtered by user/project |
| Procedural | How to do things: instructions, playbooks, learned fixes | Versioned files (rules files, skills) | Loaded by task type, not by similarity |
| Reference | External documents agent consults | Chunked retrieval index | Hybrid search, filtered by source/version |

Separate types each get own retention, update rule and token budget. One undifferentiated vector store mixes stale episodes with current facts, and stale items outrank truth.

## 3. Write path: what to store and how

- **Store distilled items, not raw transcripts.** After session or at task boundaries, extract candidate memories: facts, preferences, decisions with reasons, outcomes. Keep raw log only for audit or re-extraction.
- **Attach metadata to every item:** `owner` (user/tenant), `scope` (project, repo), `type`, `created_at`, `source` (message id, document + version), `confidence` or `importance`, and `embedding_model` + version if embedded.
- **Detect conflicts on write.** Before inserting semantic fact, look up existing facts on same subject. If new fact contradicts old, mark old `superseded_by`; do not keep both as equals. Ask user when conflict is ambiguous.
- **Never store secrets or credentials,** and minimize personal data. Record what is stored so it can be shown and deleted on request.
- **Agent-written memory is untrusted input** on next read: instruction injected today executes tomorrow. Store content as data. Render it into prompts as quoted data, not instructions.

## 4. Chunking (for episodic and reference stores)

1. Split on structure first: headings, paragraphs, functions, messages or turns. Avoid fixed character windows cutting mid-sentence or mid-function.
2. Pick starting size per content type (prose: a few hundred tokens with small overlap is common start). Then **measure** retrieval on eval queries at two or three sizes; keep best. Never choose size without testing it.
3. Make chunks self-describing. "It increased 3%" alone is unretrievable. Before embedding, prepend short context line (document title, section, date, entity). One option: cheap model generates it once per chunk ("contextual chunking", described by Anthropic as contextual retrieval).
4. Keep pointer from each chunk to its parent document and position, so agent can expand to neighbors when hit is partial.

## 5. Read path: retrieval and scoring

1. **Filter by metadata first:** owner/tenant, scope, type, and validity (`superseded_by IS NULL`, not expired). Cross-tenant similarity search is both quality bug and data-leak bug.
2. **Search hybrid:** vector similarity for paraphrase, keyword/BM25 for exact identifiers (error codes, names, file paths). Merge both lists, e.g. with reciprocal rank fusion.
3. **Re-score** merged candidates by recency and importance where they matter (episodic memory). Optionally rerank top candidates with cross-encoder or LLM reranker.
4. **Budget tokens per memory type** (for example: profile always, up to N episodic items, up to M reference chunks). Drop lowest-scoring items first. Show provenance (date, source) per item so agent can judge freshness.

```python
import math, time

def memory_score(similarity: float, created_at: float, importance: float,
                 half_life_days: float = 30.0, w_sim=0.6, w_rec=0.25, w_imp=0.15) -> float:
    """similarity in [0,1], importance in [0,1], created_at as unix seconds."""
    age_days = (time.time() - created_at) / 86400
    recency = math.exp(-math.log(2) * age_days / half_life_days)   # 1.0 now, 0.5 after one half-life
    return w_sim * similarity + w_rec * recency + w_imp * importance
```

Weights and half-life are parameters to tune on eval set, not constants. Facts that do not decay (user's preferred language) belong in semantic store, not recency-weighted index.

## 6. Store choice

| Situation | Choice |
|---|---|
| Already on Postgres, up to millions of vectors | `pgvector` in same database: transactional with other data, metadata filters in SQL |
| Need managed scale, multi-tenant namespaces, built-in hybrid search | Dedicated vector database (see using-vector-databases) |
| Mostly exact identifiers and text | Full-text search (Postgres FTS, OpenSearch) before adding embeddings |
| Small per-user fact set | Relational/document rows, no embeddings |

Vectors from different models are not comparable, so changing models means re-embedding everything that will be compared. Run old and new index side by side until re-embed finishes.

## 7. Lifecycle and eviction

- **TTL per type:** working memory ends with session; episodic items expire or get compacted after set period; semantic facts live until superseded or deleted.
- **Consolidate:** periodically summarize clusters of old episodes into one dated summary item; delete or archive originals.
- **Evict by score, not age alone:** low importance, never retrieved, and old go first.
- **Deletion must be real:** user's "forget this" removes item, its embeddings and derived summaries, or records why it cannot.

## 8. Evaluate

Build small labeled set before tuning anything:
- 30-100 queries, each with memory items that should be returned (including ones that should *not*, such as superseded facts).
- Measure recall@k and precision@k of retrieval alone, then end-to-end answer correctness with memories injected.
- Include regression cases: fact updated over time (must return latest), cross-tenant query (must return nothing from other tenants), identifier that only keyword search finds.
- Re-run after any change to chunking, embedding model, weights or filters.

## Done when

- Each memory type has store, write rule, retention rule and token budget
- Every stored item carries owner, scope, timestamp, source and (if embedded) embedding model
- Retrieval filters by tenant/scope before similarity and handles exact identifiers
- Labeled eval set reports recall@k and end-to-end correctness, including update and cross-tenant cases
- Users can see and delete what is remembered about them
