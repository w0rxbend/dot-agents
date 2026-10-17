---
name: agent-memory-systems
description: "Design an agent's short-term and persistent memory: which memory types to keep, how to chunk and store them, how to score retrieval (metadata filters, hybrid search, recency, importance), lifecycle and eviction, and how to evaluate recall. Use when an agent must remember across turns or sessions and you need a concrete storage/retrieval design; use context-engineering for in-session context hygiene and using-vector-databases for vector store operations."
source: vibeship-spawner-skills (Apache 2.0)
---

# Agent Memory Systems

Memory failures look like intelligence failures: when an agent "forgets" or contradicts itself, the cause is usually retrieval (the right item was stored but not fetched, or a stale item outranked it), not storage. Design the read path first, then decide what to write.

## 1. Decide whether you need persistent memory

| Need | Simplest adequate design |
|---|---|
| Continuity within one task or session | The conversation itself, plus summarization when it grows (context-engineering) |
| A handful of stable facts per user (name, preferences, settings) | A structured profile row/document, loaded whole into the prompt |
| Project or task state that outlives a session | Files or DB rows the agent reads at start (plan, status, decisions) |
| Recall over many past interactions or a large document corpus | A retrieval store (vector and/or keyword index) with the procedure below |

Do not add a vector store when a profile row or a status file answers the question; they are cheaper, exact and debuggable.

## 2. Separate memory types

| Type | Holds | Store | Read pattern |
|---|---|---|---|
| Working | Current task, recent turns, scratch results | Context window | Always present; summarized when long |
| Semantic | Stable facts and preferences ("user deploys with Helm") | Structured store (KV/relational/document) keyed by subject | Exact lookup by user/project, loaded whole when small |
| Episodic | What happened: past sessions, decisions, outcomes, with timestamps | Append-only log + retrieval index | Similarity + recency, filtered by user/project |
| Procedural | How to do things: instructions, playbooks, learned fixes | Versioned files (rules files, skills) | Loaded by task type, not by similarity |
| Reference | External documents the agent consults | Chunked retrieval index | Hybrid search, filtered by source/version |

Keeping them separate lets each have its own retention, update rule and token budget. A single undifferentiated vector store mixes stale episodes with current facts and outranks the truth.

## 3. Write path: what to store and how

- **Store distilled items, not raw transcripts.** After a session (or at task boundaries), extract candidate memories: facts, preferences, decisions and their reasons, outcomes. Keep the raw log only if you need audit or re-extraction.
- **Attach metadata to every item:** `owner` (user/tenant), `scope` (project, repo), `type`, `created_at`, `source` (message id, document + version), `confidence` or `importance`, and `embedding_model` + version for anything embedded.
- **Detect conflicts on write.** Before inserting a semantic fact, look up existing facts on the same subject. If the new one contradicts an old one, mark the old one `superseded_by` rather than keeping both as equals. Ask the user when the conflict is ambiguous.
- **Never store secrets or credentials,** and minimize personal data. Record what is stored so it can be shown and deleted on request.
- **Agent-written memory is untrusted input** on the next read: an injected instruction stored today is executed tomorrow. Store content as data and render it into prompts as quoted data, not as instructions.

## 4. Chunking (for episodic and reference stores)

1. Split on structure first: headings, paragraphs, functions, messages or turns. Avoid fixed character windows that cut mid-sentence or mid-function.
2. Pick a starting size per content type (for prose, a few hundred tokens with small overlap is a common start), then **measure** retrieval on your eval queries at two or three sizes and keep the best. Do not choose a size without testing it.
3. Make chunks self-describing. A chunk like "It increased 3%" is unretrievable on its own; prepend a short context line before embedding (document title, section, date, entity), for example generated once per chunk by a cheap model ("contextual chunking", described by Anthropic as contextual retrieval).
4. Keep a pointer from each chunk to its parent document and position, so the agent can expand to neighbors when a hit is partial.

## 5. Read path: retrieval and scoring

1. **Filter by metadata first:** owner/tenant, scope, type, and validity (`superseded_by IS NULL`, not expired). Similarity search across tenants is both a quality and a data-leak bug.
2. **Search hybrid:** vector similarity for paraphrase, keyword/BM25 for exact identifiers (error codes, names, file paths). Merge the two lists, e.g. with reciprocal rank fusion.
3. **Re-score** the merged candidates with recency and importance where they matter (episodic memory), then optionally rerank the top candidates with a cross-encoder or LLM reranker.
4. **Budget tokens per memory type** (for example: profile always, up to N episodic items, up to M reference chunks) and drop the lowest-scoring items first. Show provenance (date, source) with each item so the agent can judge freshness.

```python
import math, time

def memory_score(similarity: float, created_at: float, importance: float,
                 half_life_days: float = 30.0, w_sim=0.6, w_rec=0.25, w_imp=0.15) -> float:
    """similarity in [0,1], importance in [0,1], created_at as unix seconds."""
    age_days = (time.time() - created_at) / 86400
    recency = math.exp(-math.log(2) * age_days / half_life_days)   # 1.0 now, 0.5 after one half-life
    return w_sim * similarity + w_rec * recency + w_imp * importance
```

Treat the weights and half-life as parameters to tune on the eval set, not constants. Facts that do not decay (a user's preferred language) belong in the semantic store, not in a recency-weighted index.

## 6. Store choice

| Situation | Choice |
|---|---|
| Already on Postgres, up to millions of vectors | `pgvector` in the same database: transactional with your other data, metadata filters in SQL |
| Need managed scale, multi-tenant namespaces, built-in hybrid search | A dedicated vector database (see using-vector-databases) |
| Mostly exact identifiers and text | Full-text search (Postgres FTS, OpenSearch) before adding embeddings |
| Small per-user fact set | Relational/document rows, no embeddings |

Record the embedding model per item. Changing models requires re-embedding everything that will be compared, because vectors from different models are not comparable; run the old and new index side by side until the re-embed finishes.

## 7. Lifecycle and eviction

- **TTL per type:** working memory ends with the session; episodic items expire or are compacted after a set period; semantic facts live until superseded or deleted.
- **Consolidate:** periodically summarize clusters of old episodes into one dated summary item and delete or archive the originals.
- **Evict by score, not age alone:** low importance, never retrieved, and old go first.
- **Deletion must be real:** a user's "forget this" removes the item, its embeddings and derived summaries, or records why it cannot.

## 8. Evaluate

Build a small labeled set before tuning anything:
- 30-100 queries, each with the memory items that should be returned (including ones that should *not*, such as superseded facts).
- Measure recall@k and precision@k of retrieval alone, then end-to-end answer correctness with the memories injected.
- Include regression cases: a fact updated over time (must return the latest), a cross-tenant query (must return nothing from other tenants), an identifier only keyword search finds.
- Re-run after any change to chunking, embedding model, weights or filters.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Store everything forever | Distill on write; TTL and consolidation per type |
| Chunk size chosen without testing retrieval | Compare sizes on the eval set |
| One memory store for all data types | Separate semantic, episodic, procedural, reference |
| Pure vector search for identifiers | Add keyword search and merge |
| Similarity search before tenant/scope filter | Filter by metadata first |
| Old and new facts with equal weight | Supersede on write; recency scoring for episodes |
| Mixing embeddings from different models | Track `embedding_model`; re-embed on change |

## Done when

- Each memory type has a store, a write rule, a retention rule and a token budget
- Every stored item carries owner, scope, timestamp, source and (if embedded) embedding model
- Retrieval filters by tenant/scope before similarity and handles exact identifiers
- A labeled eval set reports recall@k and end-to-end correctness, including update and cross-tenant cases
- Users can see and delete what is remembered about them
