from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from app.services.multimodal_rag import multimodal_rag_service
from app.services.content_storage import content_storage
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["Multimodal RAG"])


# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    pdf_id: Optional[str] = None
    top_k: int = 5


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    pdf_id: Optional[str]
    retrieved_docs_count: int


class ProcessingStatus(BaseModel):
    pdf_id: str
    content_stored: bool
    embeddings_created: bool
    status: str


class UploadResponse(BaseModel):
    pdf_id: str
    processing_summary: Dict[str, Any]
    summaries: Dict[str, List[str]]
    storage_result: Optional[Dict[str, Any]]
    embedding_result: Dict[str, Any]
    status: str


@router.post("/upload", response_model=UploadResponse)
async def upload_and_process_pdf(
    file: UploadFile = File(...),
    save_content: bool = Query(True, description="Whether to save extracted content to storage")
):
    """
    Upload and process a PDF file through the complete multimodal RAG pipeline.
    
    This endpoint:
    1. Extracts text, tables, and images from the PDF
    2. Generates summaries for all content types
    3. Saves content to organized folders (optional)
    4. Creates embeddings and stores them in the vector database
    """
    try:
        logger.info(f"Received PDF upload request: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Process the PDF through the complete pipeline
        result = await multimodal_rag_service.process_pdf_complete(file, save_content)
        
        return UploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PDF upload endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_rag_system(query_request: QueryRequest):
    """
    Query the multimodal RAG system.
    
    Searches through processed PDF content (text, tables, images) and returns
    an answer based on the most relevant retrieved documents.
    """
    try:
        logger.info(f"Received RAG query: {query_request.question}")
        
        result = await multimodal_rag_service.query_rag(
            question=query_request.question,
            pdf_id=query_request.pdf_id,
            top_k=query_request.top_k
        )
        
        return QueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/status/{pdf_id}", response_model=ProcessingStatus)
async def get_processing_status(pdf_id: str):
    """Get the processing status for a specific PDF."""
    try:
        status = multimodal_rag_service.get_processing_status(pdf_id)
        return ProcessingStatus(**status)
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/pdfs")
async def list_processed_pdfs():
    """List all processed PDFs."""
    try:
        pdf_list = content_storage.list_processed_pdfs()
        return {
            "processed_pdfs": pdf_list,
            "count": len(pdf_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing processed PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list PDFs: {str(e)}")


@router.get("/content/{pdf_id}")
async def get_pdf_content(pdf_id: str):
    """Get saved content for a specific PDF."""
    try:
        content = content_storage.get_pdf_content(pdf_id)
        
        # Convert Path objects to strings for JSON serialization
        content["text_files"] = [str(f) for f in content["text_files"]]
        content["table_files"] = [str(f) for f in content["table_files"]]
        content["image_files"] = [str(f) for f in content["image_files"]]
        content["summary_files"] = [str(f) for f in content["summary_files"]]
        
        return content
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No content found for PDF: {pdf_id}")
    except Exception as e:
        logger.error(f"Error getting PDF content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get PDF content: {str(e)}")


@router.delete("/pdf/{pdf_id}")
async def delete_pdf_data(pdf_id: str):
    """Delete all data (content and embeddings) for a specific PDF."""
    try:
        # Delete from vector store
        vector_result = vector_store_service.delete_pdf_documents(pdf_id)
        
        # Note: Content storage deletion would need to be implemented
        # For now, we just delete from vector store
        
        return {
            "pdf_id": pdf_id,
            "vector_store_result": vector_result,
            "status": "deleted"
        }
        
    except Exception as e:
        logger.error(f"Error deleting PDF data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete PDF data: {str(e)}")


@router.get("/vector-store/stats")
async def get_vector_store_stats():
    """Get statistics about the vector store."""
    try:
        stats = vector_store_service.get_collection_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting vector store stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/vector-store/search")
async def search_vector_store(
    query: str,
    k: int = Query(5, description="Number of results to return"),
    pdf_id: Optional[str] = Query(None, description="Filter by PDF ID")
):
    """Direct search in the vector store (for debugging/testing)."""
    try:
        filter_metadata = {"pdf_id": pdf_id} if pdf_id else None
        
        results = await vector_store_service.similarity_search_with_scores(
            query=query,
            k=k,
            filter_metadata=filter_metadata
        )
        
        # Format results for JSON response
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": float(score)
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Error in vector store search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for the RAG system."""
    try:
        # Check vector store health
        vector_health = vector_store_service.health_check()
        
        # Check if services are properly initialized
        services_status = {
            "multimodal_rag_service": "initialized",
            "content_storage": "initialized",
            "vector_store_service": "initialized"
        }
        
        return {
            "status": "healthy" if vector_health["status"] == "healthy" else "degraded",
            "services": services_status,
            "vector_store_health": vector_health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
