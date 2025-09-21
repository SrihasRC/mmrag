from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.config import settings
from app.api.multimodal_rag import router as rag_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multimodal RAG API",
    description="FastAPI backend for multimodal RAG with PDF processing, text/table/image extraction, and Cohere embeddings",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag_router)

@app.get("/")
async def read_root():
    return {
        "message": "Multimodal RAG API",
        "version": "1.0.0",
        "description": "Upload PDFs and query using multimodal RAG with Cohere embeddings"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multimodal-rag-api"}