import os
import uuid
import shutil
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import tempfile
from fastapi import UploadFile, HTTPException
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import CompositeElement, Table
import logging
import re
from enum import Enum

from app.services.semantic_chunker import SemanticChunker, SemanticChunk, analyze_chunks

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    RESUME = "resume"
    ACADEMIC_PAPER = "academic_paper"
    TECHNICAL_DOC = "technical_doc"
    GENERAL = "general"
    SHORT_DOCUMENT = "short_document"


class PDFProcessor:
    """Service for processing PDF files and extracting multimodal content."""
    
    def __init__(self, storage_path: str = "./storage", embeddings_service=None):
        self.storage_path = Path(storage_path)
        self.uploads_path = self.storage_path / "uploads"
        self.content_path = self.storage_path / "content"
        
        # Create directories if they don't exist
        self.uploads_path.mkdir(parents=True, exist_ok=True)
        self.content_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize semantic chunker if embeddings service provided
        self.semantic_chunker = None
        if embeddings_service:
            try:
                self.semantic_chunker = SemanticChunker(embeddings_service)
                logger.info("SemanticChunker initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize SemanticChunker: {e}")
                logger.warning("Will fall back to traditional chunking methods")
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded PDF file and return the file path."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
            
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        unique_filename = f"{file_id}{file_extension}"
        file_path = self.uploads_path / unique_filename
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"File saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(status_code=500, detail="Error saving file")
    
    def detect_document_type(self, file_path: str) -> DocumentType:
        """Detect document type based on content analysis."""
        try:
            # Quick extraction for analysis
            elements = partition_pdf(
                filename=file_path,
                strategy="fast",
                chunking_strategy=None,  # No chunking for analysis
            )
            
            # Combine all text for analysis
            full_text = " ".join([str(el) for el in elements]).lower()
            text_length = len(full_text)
            
            # Patterns for different document types
            resume_patterns = [
                r'\b(experience|education|skills|resume|cv|curriculum vitae)\b',
                r'\b(employment|work experience|professional experience)\b',
                r'\b(bachelor|master|phd|degree|university|college)\b',
                r'\b(email|phone|address|contact)\b'
            ]
            
            academic_patterns = [
                r'\b(abstract|introduction|methodology|conclusion|references)\b',
                r'\b(figure|table|equation|theorem|lemma)\b',
                r'\b(journal|conference|proceedings|arxiv)\b'
            ]
            
            # Count pattern matches
            resume_score = sum(len(re.findall(pattern, full_text)) for pattern in resume_patterns)
            academic_score = sum(len(re.findall(pattern, full_text)) for pattern in academic_patterns)
            
            # Determine document type
            if text_length < 3000:  # Short document
                return DocumentType.SHORT_DOCUMENT
            elif resume_score > 3:  # Strong resume indicators
                return DocumentType.RESUME
            elif academic_score > 3:  # Strong academic indicators
                return DocumentType.ACADEMIC_PAPER
            else:
                return DocumentType.GENERAL
                
        except Exception as e:
            logger.warning(f"Could not detect document type: {str(e)}")
            return DocumentType.GENERAL
    
    def get_adaptive_chunking_params(self, doc_type: DocumentType, total_length: int) -> Dict:
        """Get chunking parameters based on document type and length."""
        if doc_type in [DocumentType.RESUME, DocumentType.SHORT_DOCUMENT] or total_length < 5000:
            # For short documents: minimal chunking, preserve context
            return {
                "chunking_strategy": "basic",
                "max_characters": 15000,  # Much larger chunks
                "combine_text_under_n_chars": 5000,
                "new_after_n_chars": 10000,
                "overlap_chars": 500  # Add overlap
            }
        elif doc_type == DocumentType.ACADEMIC_PAPER:
            # For academic papers: section-based chunking
            return {
                "chunking_strategy": "by_title",
                "max_characters": 8000,
                "combine_text_under_n_chars": 3000,
                "new_after_n_chars": 6000,
                "overlap_chars": 800
            }
        else:
            # For general documents: balanced chunking
            return {
                "chunking_strategy": "by_title",
                "max_characters": 10000,
                "combine_text_under_n_chars": 2000,
                "new_after_n_chars": 6000,
                "overlap_chars": 600
            }
    
    def extract_pdf_elements(self, file_path: str) -> Tuple[List, DocumentType, Dict]:
        """Extract elements from PDF using adaptive chunking strategy."""
        try:
            logger.info(f"Starting PDF extraction for: {file_path}")
            
            # Step 1: Detect document type
            doc_type = self.detect_document_type(file_path)
            logger.info(f"Detected document type: {doc_type.value}")
            
            # Step 2: Get total document length for adaptive parameters
            preview_elements = partition_pdf(
                filename=file_path,
                strategy="fast",
                chunking_strategy=None
            )
            total_length = sum(len(str(el)) for el in preview_elements)
            
            # Step 3: Get adaptive chunking parameters
            chunking_params = self.get_adaptive_chunking_params(doc_type, total_length)
            logger.info(f"Using chunking params: {chunking_params}")
            
            # Step 4: Extract with adaptive parameters
            chunks = partition_pdf(
                filename=file_path,
                infer_table_structure=True,
                strategy="hi_res",
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy=chunking_params["chunking_strategy"],
                max_characters=chunking_params["max_characters"],
                combine_text_under_n_chars=chunking_params["combine_text_under_n_chars"],
                new_after_n_chars=chunking_params["new_after_n_chars"],
            )
            
            logger.info(f"Extracted {len(chunks)} chunks from {doc_type.value} document")
            
            # Step 5: Add overlapping context if needed
            if chunking_params.get("overlap_chars", 0) > 0 and len(chunks) > 1:
                chunks = self._add_overlapping_context(chunks, chunking_params["overlap_chars"])
            
            return chunks, doc_type, chunking_params
            
        except Exception as e:
            logger.error(f"Error extracting PDF elements: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    def extract_pdf_elements_semantic(
        self, 
        file_path: str,
        use_semantic_chunking: bool = True
    ) -> Tuple[List, DocumentType, Dict]:
        """
        Extract PDF with semantic neural chunking.
        
        This method uses embedding-based boundary detection to create
        semantically coherent chunks instead of fixed character counts.
        
        Args:
            file_path: Path to PDF file
            use_semantic_chunking: Whether to use semantic chunking (vs traditional)
            
        Returns:
            Tuple of (elements, document_type, metadata)
        """
        try:
            logger.info(f"Starting semantic PDF extraction for: {file_path}")
            
            # Step 1: Detect document type
            doc_type = self.detect_document_type(file_path)
            logger.info(f"Detected document type: {doc_type.value}")
            
            # Step 2: Extract raw elements WITHOUT chunking
            raw_elements = partition_pdf(
                filename=file_path,
                infer_table_structure=True,
                strategy="hi_res",
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy=None  # NO CHUNKING - we do it ourselves
            )
            
            logger.info(f"Extracted {len(raw_elements)} raw elements from PDF")
            
            # Step 3: Separate text, tables, images
            text_elements = []
            tables = []
            
            for element in raw_elements:
                element_type = str(type(element))
                if "Table" in element_type:
                    tables.append(element)
                elif "CompositeElement" in element_type or "Text" in element_type:
                    # Collect text content
                    if hasattr(element, 'text') and element.text.strip():
                        text_elements.append(element)
            
            logger.info(f"Separated: {len(text_elements)} text elements, {len(tables)} tables")
            
            # Step 4: Apply semantic chunking to TEXT only
            final_text_chunks = []
            
            if use_semantic_chunking and self.semantic_chunker and text_elements:
                try:
                    # Combine text elements
                    combined_text = '\n\n'.join([el.text for el in text_elements])
                    
                    # Apply semantic chunking
                    semantic_chunks = self.semantic_chunker.chunk_document(
                        text=combined_text,
                        doc_type=doc_type.value
                    )
                    
                    # Convert SemanticChunk objects to element-like objects
                    for i, chunk in enumerate(semantic_chunks):
                        # Create a composite element-like object
                        chunk_element = type('SemanticChunkElement', (), {
                            'text': chunk.content,
                            'metadata': type('Metadata', (), {
                                'chunk_id': i,
                                'coherence_score': chunk.coherence_score,
                                'num_sentences': chunk.metadata['num_sentences'],
                                'char_count': chunk.metadata['char_count'],
                                'chunking_method': 'semantic_neural'
                            })()
                        })()
                        final_text_chunks.append(chunk_element)
                    
                    # Log statistics
                    stats = analyze_chunks(semantic_chunks)
                    logger.info(
                        f"Semantic chunking created {len(semantic_chunks)} chunks "
                        f"(avg coherence: {stats.get('avg_coherence', 0):.3f}, "
                        f"avg sentences: {stats.get('avg_sentences', 0):.1f})"
                    )
                    
                except Exception as e:
                    logger.error(f"Semantic chunking failed: {e}, falling back to traditional")
                    # Fallback to original elements
                    final_text_chunks = text_elements
            else:
                # Use original text elements (no semantic chunking)
                final_text_chunks = text_elements
                logger.info("Using traditional chunking (semantic chunking disabled or unavailable)")
            
            # Step 5: Get images from original elements
            images_b64 = self._extract_images_base64(raw_elements)
            
            # Step 6: Combine everything (text chunks + tables + images as separate tracking)
            all_elements = final_text_chunks + tables
            
            metadata = {
                'chunking_method': 'semantic_neural' if (use_semantic_chunking and self.semantic_chunker) else 'traditional',
                'num_text_chunks': len(final_text_chunks),
                'num_tables': len(tables),
                'num_images': len(images_b64),
                'document_type': doc_type.value
            }
            
            logger.info(f"Semantic extraction complete: {metadata}")
            
            return all_elements, doc_type, metadata
            
        except Exception as e:
            logger.error(f"Semantic extraction failed: {str(e)}", exc_info=True)
            # Fallback to original method
            logger.info("Falling back to traditional extraction method")
            return self.extract_pdf_elements(file_path)
    
    def separate_elements(self, chunks: List, doc_type: DocumentType) -> Dict:
        """Separate extracted elements into tables, texts, and images with document context."""
        tables = []
        texts = []
        
        # Separate tables from texts
        for chunk in chunks:
            chunk_type = str(type(chunk))
            if "Table" in chunk_type:
                tables.append(chunk)
            elif "CompositeElement" in chunk_type or "SemanticChunkElement" in chunk_type:
                # Include both traditional CompositeElement and semantic chunks
                texts.append(chunk)
        
        # Get images from CompositeElement objects
        images = self._extract_images_base64(chunks)
        
        logger.info(f"Separated elements for {doc_type.value} - Tables: {len(tables)}, Texts: {len(texts)}, Images: {len(images)}")
        
        return {
            "tables": tables,
            "texts": texts,
            "images": images,
            "document_type": doc_type.value,
            "total_chunks": len(chunks)
        }
    
    def _extract_images_base64(self, chunks: List) -> List[str]:
        """Extract base64 encoded images from chunks."""
        images_b64 = []
        
        for chunk in chunks:
            if "CompositeElement" in str(type(chunk)):
                chunk_els = chunk.metadata.orig_elements
                for el in chunk_els:
                    if "Image" in str(type(el)):
                        if hasattr(el.metadata, 'image_base64') and el.metadata.image_base64:
                            images_b64.append(el.metadata.image_base64)
        
        return images_b64
    
    def get_table_html(self, tables: List) -> List[str]:
        """Extract HTML representation of tables."""
        return [table.metadata.text_as_html for table in tables if hasattr(table.metadata, 'text_as_html')]
    
    def get_text_content(self, texts: List) -> List[str]:
        """Extract text content from text elements."""
        return [text.text for text in texts if hasattr(text, 'text')]
    
    async def process_pdf_file(
        self, 
        file: UploadFile,
        use_semantic_chunking: bool = True
    ) -> Dict:
        """
        Complete PDF processing pipeline.
        
        Args:
            file: Uploaded PDF file
            use_semantic_chunking: Whether to use neural semantic chunking
        """
        try:
            # Step 1: Save uploaded file
            file_path = await self.save_uploaded_file(file)
            
            # Step 2: Extract elements from PDF with adaptive/semantic chunking
            if use_semantic_chunking and self.semantic_chunker:
                logger.info(f"Using semantic chunking for: {file.filename}")
                chunks, doc_type, chunking_params = self.extract_pdf_elements_semantic(
                    file_path,
                    use_semantic_chunking=True
                )
            else:
                logger.info(f"Using traditional chunking for: {file.filename}")
                chunks, doc_type, chunking_params = self.extract_pdf_elements(file_path)
            
            # Step 3: Separate elements by type
            separated_elements = self.separate_elements(chunks, doc_type)
            
            # Step 4: Prepare data for further processing
            tables_html = self.get_table_html(separated_elements["tables"])
            text_content = self.get_text_content(separated_elements["texts"])
            
            result = {
                "file_id": Path(file_path).stem,
                "file_path": file_path,
                "raw_chunks": chunks,
                "separated_elements": separated_elements,
                "tables_html": tables_html,
                "text_content": text_content,
                "images_base64": separated_elements["images"],
                "document_type": doc_type.value,
                "chunking_params": chunking_params,
                "summary": {
                    "total_chunks": len(chunks),
                    "tables_count": len(separated_elements["tables"]),
                    "texts_count": len(separated_elements["texts"]),
                    "images_count": len(separated_elements["images"]),
                    "document_type": doc_type.value,
                    "adaptive_chunking": True
                }
            }
            
            logger.info(f"PDF processing completed successfully for file: {file.filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error in PDF processing pipeline: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
    
    def cleanup_file(self, file_path: str) -> bool:
        """Remove processed file from storage."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
            return False
    
    def get_element_types(self, chunks: List) -> set:
        """Get unique element types from chunks (useful for debugging)."""
        return set([str(type(el)) for el in chunks])
    
    def _add_overlapping_context(self, chunks: List, overlap_chars: int) -> List:
        """Add overlapping context between chunks to maintain continuity."""
        if len(chunks) <= 1:
            return chunks
        
        try:
            enhanced_chunks = []
            
            for i, chunk in enumerate(chunks):
                chunk_text = str(chunk)
                
                # Add context from previous chunk
                if i > 0:
                    prev_text = str(chunks[i-1])
                    if len(prev_text) > overlap_chars:
                        prev_context = prev_text[-overlap_chars:]
                        chunk_text = f"[Previous context: ...{prev_context}] " + chunk_text
                
                # Add context from next chunk
                if i < len(chunks) - 1:
                    next_text = str(chunks[i+1])
                    if len(next_text) > overlap_chars:
                        next_context = next_text[:overlap_chars]
                        chunk_text = chunk_text + f" [Following context: {next_context}...]"
                
                # Create new chunk with enhanced context
                enhanced_chunk = chunk
                if hasattr(chunk, 'text'):
                    enhanced_chunk.text = chunk_text
                
                enhanced_chunks.append(enhanced_chunk)
            
            logger.info(f"Added overlapping context to {len(enhanced_chunks)} chunks")
            return enhanced_chunks
            
        except Exception as e:
            logger.warning(f"Could not add overlapping context: {str(e)}")
            return chunks


# Global instance initialization with embeddings for semantic chunking
def _initialize_pdf_processor():
    """Initialize PDF processor with embeddings service for semantic chunking."""
    try:
        from langchain_cohere import CohereEmbeddings
        from app.config.config import settings
        
        # Create embeddings service
        embeddings = CohereEmbeddings(
            cohere_api_key=settings.COHERE_API_KEY,
            model="embed-english-v3.0"
        )
        
        # Initialize with embeddings
        processor = PDFProcessor(embeddings_service=embeddings)
        logger.info("PDFProcessor initialized with SemanticChunker support")
        return processor
        
    except Exception as e:
        logger.warning(f"Could not initialize with semantic chunking: {e}")
        logger.warning("Falling back to PDFProcessor without semantic chunking")
        return PDFProcessor()


pdf_processor = _initialize_pdf_processor()
