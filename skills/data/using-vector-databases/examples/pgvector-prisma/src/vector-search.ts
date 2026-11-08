import "dotenv/config";
import { randomUUID } from "node:crypto";
import { PrismaClient } from "./generated/prisma/client.js";
import { PrismaPg } from "@prisma/adapter-pg";
import OpenAI from "openai";

export const prisma = new PrismaClient({
  adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL }),
});
const openai = new OpenAI();

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: "text-embedding-3-small", input: text, dimensions: 1536,
  });
  return response.data[0].embedding;
}

export async function insertDocument(content: string, metadata: Record<string, unknown> = {}) {
  const embedding = JSON.stringify(await generateEmbedding(content));
  await prisma.$executeRaw`
    INSERT INTO documents (id, content, embedding, metadata)
    VALUES (${randomUUID()}, ${content}, ${embedding}::vector, ${JSON.stringify(metadata)}::jsonb)
  `;
}

export async function similaritySearch(query: string, limit = 5) {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
    throw new RangeError("limit must be an integer between 1 and 100");
  }
  const embedding = JSON.stringify(await generateEmbedding(query));
  return prisma.$queryRaw<Array<{ id: string; content: string; metadata: unknown; distance: number }>>`
    SELECT id, content, metadata, embedding <=> ${embedding}::vector AS distance
    FROM documents ORDER BY distance LIMIT ${limit}
  `;
}
