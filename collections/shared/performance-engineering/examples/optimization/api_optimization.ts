/**
 * API Performance Optimization Examples
 *
 * Demonstrates: Pagination, batching, and field selection patterns
 */

import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

// ===== PAGINATION: Cursor-Based =====

interface PaginationRequest {
  cursor?: string;
  limit?: number;
}

app.get('/api/products', async (req: Request, res: Response) => {
  const { cursor } = req.query as PaginationRequest;
  const limit = Math.min(Math.max(Number(req.query.limit) || 20, 1), 100);  // bounded integer

  // Cursor-based pagination (efficient for large datasets).
  // Bind request values as parameters; never interpolate them into SQL.
  const products = cursor
    ? await db.query('SELECT * FROM products WHERE id > $1 ORDER BY id LIMIT $2', [cursor, limit])
    : await db.query('SELECT * FROM products ORDER BY id LIMIT $1', [limit]);
  const nextCursor = products[products.length - 1]?.id;

  res.json({
    data: products,
    next_cursor: nextCursor,
    has_more: products.length === limit,
  });
});

// ===== BATCH OPERATIONS =====

app.post('/api/users/batch', async (req: Request, res: Response) => {
  const { ids } = req.body;

  if (!Array.isArray(ids) || ids.length === 0) {
    return res.status(400).json({ error: 'ids must be non-empty array' });
  }

  // Single query for multiple IDs (vs N separate queries)
  const users = await db.query('SELECT * FROM users WHERE id = ANY($1)', [ids]);

  res.json(users);
});

// ===== FIELD SELECTION =====

const ALLOWED_FIELDS = new Set(['id', 'name', 'email', 'created_at']);

app.get('/api/users/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const { fields } = req.query;

  // Allow client to request specific fields. Column names cannot be bound
  // as parameters, so accept only allowlisted ones.
  const fieldList = fields ? (fields as string).split(',') : [...ALLOWED_FIELDS];
  if (fieldList.some((f) => !ALLOWED_FIELDS.has(f))) {
    return res.status(400).json({ error: 'unknown field' });
  }

  const user = await db.query(
    `SELECT ${fieldList.join(', ')} FROM users WHERE id = $1`,
    [id],
  );

  res.json(user);
});

// ===== RESPONSE COMPRESSION =====

import compression from 'compression';

app.use(compression({
  level: 6,              // Compression level (1-9)
  threshold: 1024,       // Only compress > 1KB
}));

// ===== CACHING HEADERS =====

app.get('/api/products/:id', async (req: Request, res: Response) => {
  const { id } = req.params;
  const product = await db.query('SELECT * FROM products WHERE id = $1', [id]);

  // Cache for 5 minutes (browser and CDN)
  res.set({
    'Cache-Control': 'public, max-age=300',
    'ETag': generateETag(product),
  });

  res.json(product);
});

// Helper functions (placeholder)
const db = {
  query: async (sql: string, params: unknown[] = []) => {
    // Database query implementation
    return [];
  },
};

const generateETag = (data: any): string => {
  // ETag generation (hash of data)
  return 'etag';
};
