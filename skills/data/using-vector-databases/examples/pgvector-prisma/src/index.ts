import { insertDocument, similaritySearch, prisma } from "./vector-search.js";

try {
  await insertDocument("Prisma supports pgvector through parameterized SQL.", { source: "example" });
  console.log(await similaritySearch(process.argv[2] ?? "How do I search vectors?"));
} finally {
  await prisma.$disconnect();
}
