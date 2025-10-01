from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
import os
from pathlib import Path

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


# In-memory cache to prevent duplicate processing
processing_cache = set()

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
        
        # Create a unique identifier for this upload to prevent duplicates
        file_content = await file.read()
        file.file.seek(0)  # Reset file pointer
        
        import hashlib
        file_hash = hashlib.md5(file_content).hexdigest()
        upload_key = f"{file.filename}_{file_hash}"
        
        # Check if we're already processing this exact file
        if upload_key in processing_cache:
            logger.warning(f"Duplicate upload detected for {file.filename}, skipping...")
            raise HTTPException(status_code=429, detail="File is already being processed")
        
        try:
            # Mark as processing
            processing_cache.add(upload_key)
            
            # Process the PDF through the complete pipeline
            result = await multimodal_rag_service.process_pdf_complete(file, save_content)
            
            logger.info(f"Successfully processed PDF: {file.filename} -> {result['pdf_id']}")
            return UploadResponse(**result)
            
        finally:
            # Remove from processing cache when done
            processing_cache.discard(upload_key)
        
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
        
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            for doc, score in results
        ]
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Error in vector store search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/debug/{pdf_id}")
async def debug_pdf_content(pdf_id: str):
    """Debug endpoint to check what content is stored for a PDF."""
    try:
        # Get all documents for this PDF from vector store
        all_docs = await vector_store_service.similarity_search(
            query="",  # Empty query to get all
            k=100,
            filter_metadata={"pdf_id": pdf_id}
        )
        
        debug_info = {
            "pdf_id": pdf_id,
            "total_documents": len(all_docs),
            "content_types": {},
            "sample_content": []
        }
        
        for doc in all_docs:
            content_type = doc.metadata.get("content_type", "unknown")
            debug_info["content_types"][content_type] = debug_info["content_types"].get(content_type, 0) + 1
            
            # Add sample content for debugging
            if len(debug_info["sample_content"]) < 10:
                debug_info["sample_content"].append({
                    "content_type": content_type,
                    "content_preview": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "metadata": doc.metadata,
                    "full_length": len(doc.page_content)
                })
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")


@router.get("/pdf/{pdf_id}/file")
async def get_pdf_file(pdf_id: str):
    """Serve the original PDF file for viewing in browser."""
    try:
        # Construct file path - PDF ID is the UUID used as filename
        storage_path = Path("./storage/uploads")
        pdf_file_path = storage_path / f"{pdf_id}.pdf"
        
        # Check if file exists
        if not pdf_file_path.exists():
            logger.error(f"PDF file not found: {pdf_file_path}")
            raise HTTPException(status_code=404, detail=f"PDF file not found for ID: {pdf_id}")
        
        # Return file response with proper headers for PDF viewing
        return FileResponse(
            path=str(pdf_file_path),
            media_type="application/pdf",
            filename=f"{pdf_id}.pdf",
            headers={
                "Content-Disposition": "inline",  # This allows viewing in browser instead of download
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF file {pdf_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving PDF file: {str(e)}")


@router.get("/health")
async def rag_health_check():
    """RAG system health check."""
    try:
        vector_stats = vector_store_service.get_collection_stats()
        
        return {
            "status": "healthy",
            "vector_store": vector_stats,
            "services": {
                "pdf_processor": "active",
                "multimodal_rag": "active",
                "vector_store": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.delete("/clear-all")
async def clear_all_data():
    """Clear all uploaded PDFs and processed data (for testing purposes)."""
    try:
        import shutil
        import os
        
        # Clear storage directories
        storage_path = "./storage"
        for subdir in ["uploads", "content", "vector_db"]:
            dir_path = os.path.join(storage_path, subdir)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.makedirs(dir_path, exist_ok=True)
        
        # Clear processing cache
        global processing_cache
        processing_cache.clear()
        
        # Clear vector store
        vector_store_service.clear_all_documents()
        
        logger.info("Successfully cleared all data")
        
        return {
            "status": "success",
            "message": "All data cleared successfully",
            "cleared": {
                "uploads": True,
                "content": True,
                "vector_db": True,
                "processing_cache": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")
