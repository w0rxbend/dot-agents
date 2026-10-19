# pgvector + Prisma integration example

Requires Node.js 22.12+, PostgreSQL 15+ with pgvector installed, and an OpenAI API key.
Prisma CLI, client, and PostgreSQL adapter are pinned together on stable version 7.10.1.

```sh
npm ci
cp .env.example .env
# Edit DATABASE_URL and OPENAI_API_KEY.
# Enable pgvector before creating the schema (requires database permission):
psql "$DATABASE_URL" -c 'CREATE EXTENSION IF NOT EXISTS vector'
npx prisma db push
npm run generate
npm run build
npm run dev -- "How do I search vectors?"
```

Export DATABASE_URL in your shell for the psql command; Prisma and the example load `.env` automatically.
`prisma db push` creates the example table. Use reviewed migrations for production.

The example embeds documents with 1536 dimensions, inserts them with parameterized SQL,
and performs cosine-distance search using pgvector's `<=>` operator. Vector literals
are serialized as JSON arrays and bound as parameters before casting to `vector`.
The generated client uses the Prisma 7 PostgreSQL adapter and an explicit output directory.

`npm run generate` and `npm run build` need no running database or API credentials
(a placeholder DATABASE_URL suffices for generation). Running the example requires
both services and makes paid embedding requests. Generated files are not committed.
