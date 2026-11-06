"""
FastAPI RAG application with Qdrant vector database.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
from pathlib import Path
from dotenv import load_dotenv

from rag_pipeline import RAGPipeline

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="RAG API", version="1.0.0")

# Initialize RAG pipeline
rag = RAGPipeline(
    qdrant_url=os.getenv("QDRANT_URL", "localhost"),
    qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
    collection_name="documents",
    embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
)

# /ingest reads only files under this directory (no auth on this example API).
INGEST_ROOT = Path(os.getenv("INGEST_ROOT", "data")).resolve()


class IngestRequest(BaseModel):
    file_path: str
    metadata: Optional[Dict] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    filter: Optional[Dict] = None


class GenerateRequest(BaseModel):
    query: str
    limit: int = 5
    filter: Optional[Dict] = None


class SearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict


class GenerateResponse(BaseModel):
    answer: str
    sources: List[SearchResult]


@app.post("/ingest")
async def ingest_document(request: IngestRequest):
    """Ingest a document into the vector database."""
    path = (INGEST_ROOT / request.file_path).resolve()
    if not path.is_relative_to(INGEST_ROOT) or not path.is_file():
        raise HTTPException(status_code=400, detail="file_path must name a file inside INGEST_ROOT")
    try:
        result = rag.ingest_document(
            file_path=str(path),
            metadata=request.metadata or {}
        )
        return {
            "status": "success",
            "message": f"Ingested {result['chunks_created']} chunks",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=List[SearchResult])
async def search(request: SearchRequest):
    """Search for relevant documents."""
    try:
        results = rag.search(
            query=request.query,
            limit=request.limit,
            filter=request.filter
        )
        return [
            SearchResult(
                text=r["text"],
                score=r["score"],
                metadata=r["metadata"]
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate an answer using RAG."""
    try:
        result = rag.generate_answer(
            query=request.query,
            limit=request.limit,
            filter=request.filter
        )
        return GenerateResponse(
            answer=result["answer"],
            sources=[
                SearchResult(
                    text=s["text"],
                    score=s["score"],
                    metadata=s["metadata"]
                )
                for s in result["sources"]
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "collection": rag.collection_name}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=8000)
