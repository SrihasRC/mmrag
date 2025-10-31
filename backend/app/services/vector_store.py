import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain.storage import InMemoryStore
from langchain.retrievers.multi_vector import MultiVectorRetriever

from app.config.config import settings

# Set environment variables for Cohere
os.environ["COHERE_API_KEY"] = settings.COHERE_API_KEY

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing vector embeddings using Cohere and Chroma."""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.vector_db_path = self.storage_path / "vector_db"
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Cohere embeddings
        try:
            self.embeddings = CohereEmbeddings(
                cohere_api_key=settings.COHERE_API_KEY,
                model="embed-english-v3.0"
            )
            logger.info("Cohere embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cohere embeddings: {str(e)}")
            logger.error("Please ensure COHERE_API_KEY is set in your .env file")
            logger.error(f"Current COHERE_API_KEY value: {'***' + settings.COHERE_API_KEY[-4:] if settings.COHERE_API_KEY else 'NOT SET'}")
            raise
        
        # Initialize Chroma vector store
        self.vectorstore = Chroma(
            collection_name="multimodal_rag",
            embedding_function=self.embeddings,
            persist_directory=str(self.vector_db_path)
        )
        
        # Initialize document store for parent documents
        self.docstore = InMemoryStore()
        self.id_key = "doc_id"
        
        # Initialize multi-vector retriever
        self.retriever = MultiVectorRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            id_key=self.id_key,
        )
        
        logger.info("Vector store service initialized with Cohere embeddings")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add documents to the vector store."""
        try:
            if not documents:
                return {"status": "no_documents", "count": 0}
            
            # Convert to LangChain Document objects
            doc_objects = []
            doc_ids = []
            
            for doc_data in documents:
                doc_id = str(uuid.uuid4())
                doc_ids.append(doc_id)
                
                # Create document with metadata
                metadata = doc_data.get("metadata", {})
                metadata[self.id_key] = doc_id
                
                doc = Document(
                    page_content=doc_data["content"],
                    metadata=metadata
                )
                doc_objects.append(doc)
            
            # Add to vector store
            self.retriever.vectorstore.add_documents(doc_objects)
            
            # Add to document store (for multi-vector retrieval)
            for doc_id, doc in zip(doc_ids, doc_objects):
                self.retriever.docstore.mset([(doc_id, doc)])
            
            # Persist the vector store
            self.vectorstore.persist()
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
            return {
                "status": "success",
                "count": len(documents),
                "doc_ids": doc_ids
            }
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    async def similarity_search(self, query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform similarity search in the vector store."""
        try:
            # Build filter for Chroma
            where_filter = None
            if filter_metadata:
                where_filter = filter_metadata
            
            # Perform similarity search
            if where_filter:
                results = self.vectorstore.similarity_search(
                    query=query,
                    k=k,
                    filter=where_filter
                )
            else:
                results = self.vectorstore.similarity_search(
                    query=query,
                    k=k
                )
            
            logger.info(f"Similarity search returned {len(results)} documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    async def similarity_search_with_scores(self, query: str, k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        Perform similarity search with relevance scores.
        
        IMPORTANT: Chroma returns L2 distance, not cosine similarity!
        We convert distance to similarity: similarity = 1 / (1 + distance)
        This ensures scores are in [0, 1] range where higher = more similar.
        """
        try:
            # Build filter for Chroma
            where_filter = None
            if filter_metadata:
                where_filter = filter_metadata
            
            # Perform similarity search with scores (returns L2 distance)
            if where_filter:
                results = self.vectorstore.similarity_search_with_score(
                    query=query,
                    k=k,
                    filter=where_filter
                )
            else:
                results = self.vectorstore.similarity_search_with_score(
                    query=query,
                    k=k
                )
            
            # FIXED: Convert L2 distance to similarity score
            # Chroma returns (document, distance) where lower distance = more similar
            # We convert to (document, similarity) where higher score = more similar
            converted_results = []
            for doc, distance in results:
                # Convert distance to similarity: similarity = 1 / (1 + distance)
                # This maps:
                #   distance=0 → similarity=1.0 (perfect match)
                #   distance=1 → similarity=0.5 (moderate)
                #   distance=∞ → similarity→0 (very different)
                similarity = 1.0 / (1.0 + distance)
                converted_results.append((doc, similarity))
                
            logger.info(f"Similarity search with scores returned {len(converted_results)} documents")
            if converted_results:
                logger.debug(f"Score range: {min(s for _, s in converted_results):.3f} to {max(s for _, s in converted_results):.3f}")
            
            return converted_results
            
        except Exception as e:
            logger.error(f"Error in similarity search with scores: {str(e)}")
            return []
    
    def check_pdf_exists(self, pdf_id: str) -> bool:
        """Check if documents for a PDF exist in the vector store."""
        try:
            # Search for any document with the given pdf_id
            results = self.vectorstore.similarity_search(
                query="test",  # dummy query
                k=1,
                filter={"pdf_id": pdf_id}
            )
            return len(results) > 0
        except Exception as e:
            logger.error(f"Error checking PDF existence: {str(e)}")
            return False
    
    def get_pdf_documents(self, pdf_id: str) -> List[Document]:
        """Get all documents for a specific PDF."""
        try:
            # Get all documents for the PDF (using a broad search)
            results = self.vectorstore.similarity_search(
                query="",  # empty query to get all
                k=1000,  # large number to get all documents
                filter={"pdf_id": pdf_id}
            )
            
            logger.info(f"Found {len(results)} documents for PDF: {pdf_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting PDF documents: {str(e)}")
            return []
    
    def delete_pdf_documents(self, pdf_id: str) -> Dict[str, Any]:
        """Delete all documents for a specific PDF."""
        try:
            # Get all documents for the PDF
            pdf_docs = self.get_pdf_documents(pdf_id)
            
            if not pdf_docs:
                return {"status": "no_documents", "deleted_count": 0}
            
            # Extract document IDs
            doc_ids = []
            for doc in pdf_docs:
                if self.id_key in doc.metadata:
                    doc_ids.append(doc.metadata[self.id_key])
            
            # Delete from vector store
            if doc_ids:
                self.vectorstore.delete(ids=doc_ids)
                
                # Delete from document store
                self.docstore.mdelete(doc_ids)
                
                # Persist changes
                self.vectorstore.persist()
            
            logger.info(f"Deleted {len(doc_ids)} documents for PDF: {pdf_id}")
            
            return {
                "status": "success",
                "deleted_count": len(doc_ids),
                "pdf_id": pdf_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting PDF documents: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            # Get collection info
            collection = self.vectorstore._collection
            count = collection.count()
            
            # Get unique PDF IDs (this is a simplified approach)
            all_docs = self.vectorstore.similarity_search("", k=count) if count > 0 else []
            pdf_ids = set()
            content_types = {}
            
            for doc in all_docs:
                if "pdf_id" in doc.metadata:
                    pdf_ids.add(doc.metadata["pdf_id"])
                
                content_type = doc.metadata.get("content_type", "unknown")
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            return {
                "total_documents": count,
                "unique_pdfs": len(pdf_ids),
                "pdf_ids": list(pdf_ids),
                "content_types": content_types
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "total_documents": 0,
                "unique_pdfs": 0,
                "pdf_ids": [],
                "content_types": {},
                "error": str(e)
            }
    
    def clear_all_documents(self) -> Dict[str, Any]:
        """Clear all documents from the vector store."""
        try:
            # Get all document IDs
            collection = self.vectorstore._collection
            count = collection.count()
            
            if count == 0:
                return {"status": "already_empty", "cleared_count": 0}
            
            # Clear the collection
            collection.delete()
            
            # Clear the document store
            self.docstore.mdelete(list(self.docstore.yield_keys()))
            
            # Persist changes
            self.vectorstore.persist()
            
            logger.info(f"Cleared all {count} documents from vector store")
            
            return {
                "status": "success",
                "cleared_count": count
            }
            
        except Exception as e:
            logger.error(f"Error clearing all documents: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store service."""
        try:
            # Test embedding generation
            test_text = "This is a test document for health check."
            embeddings = self.embeddings.embed_query(test_text)
            
            # Test vector store connection
            stats = self.get_collection_stats()
            
            return {
                "status": "healthy",
                "embedding_dimension": len(embeddings),
                "vector_store_stats": stats,
                "storage_path": str(self.vector_db_path)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global instance
vector_store_service = VectorStoreService()
