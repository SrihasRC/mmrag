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

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF files and extracting multimodal content."""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.uploads_path = self.storage_path / "uploads"
        self.content_path = self.storage_path / "content"
        
        # Create directories if they don't exist
        self.uploads_path.mkdir(parents=True, exist_ok=True)
        self.content_path.mkdir(parents=True, exist_ok=True)
    
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
    
    def extract_pdf_elements(self, file_path: str) -> List:
        """Extract elements from PDF using unstructured library."""
        try:
            logger.info(f"Starting PDF extraction for: {file_path}")
            
            chunks = partition_pdf(
                filename=file_path,
                infer_table_structure=True,            # extract tables
                strategy="hi_res",                     # mandatory to infer tables
                extract_image_block_types=["Image"],   # Add 'Table' to list to extract image of tables
                extract_image_block_to_payload=True,   # if true, will extract base64 for API usage
                chunking_strategy="by_title",          # or 'basic'
                max_characters=10000,                  # defaults to 500
                combine_text_under_n_chars=2000,       # defaults to 0
                new_after_n_chars=6000,
            )
            
            logger.info(f"Extracted {len(chunks)} chunks from PDF")
            return chunks
            
        except Exception as e:
            logger.error(f"Error extracting PDF elements: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    def separate_elements(self, chunks: List) -> Dict[str, List]:
        """Separate extracted elements into tables, texts, and images."""
        tables = []
        texts = []
        
        # Separate tables from texts
        for chunk in chunks:
            if "Table" in str(type(chunk)):
                tables.append(chunk)
            elif "CompositeElement" in str(type(chunk)):
                texts.append(chunk)
        
        # Get images from CompositeElement objects
        images = self._extract_images_base64(chunks)
        
        logger.info(f"Separated elements - Tables: {len(tables)}, Texts: {len(texts)}, Images: {len(images)}")
        
        return {
            "tables": tables,
            "texts": texts,
            "images": images
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
    
    async def process_pdf_file(self, file: UploadFile) -> Dict:
        """Complete PDF processing pipeline."""
        try:
            # Step 1: Save uploaded file
            file_path = await self.save_uploaded_file(file)
            
            # Step 2: Extract elements from PDF
            chunks = self.extract_pdf_elements(file_path)
            
            # Step 3: Separate elements by type
            separated_elements = self.separate_elements(chunks)
            
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
                "summary": {
                    "total_chunks": len(chunks),
                    "tables_count": len(separated_elements["tables"]),
                    "texts_count": len(separated_elements["texts"]),
                    "images_count": len(separated_elements["images"])
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


# Global instance
pdf_processor = PDFProcessor()
