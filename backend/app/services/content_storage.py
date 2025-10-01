import os
import json
import base64
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ContentStorageService:
    """Service for storing extracted PDF content in organized folders."""
    
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.content_path = self.storage_path / "content"
        
        # Create base directories
        self.content_path.mkdir(parents=True, exist_ok=True)
    
    def create_pdf_folder(self, pdf_id: str) -> Path:
        """Create a folder structure for a specific PDF."""
        pdf_folder = self.content_path / pdf_id
        
        # Create subfolders
        subfolders = ["texts", "tables", "images", "summaries", "metadata"]
        for folder in subfolders:
            (pdf_folder / folder).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created folder structure for PDF: {pdf_id}")
        return pdf_folder
    
    def save_text_chunks(self, pdf_id: str, text_chunks: List[str]) -> List[str]:
        """Save text chunks to individual files."""
        pdf_folder = self.create_pdf_folder(pdf_id)
        text_folder = pdf_folder / "texts"
        
        saved_files = []
        for i, chunk in enumerate(text_chunks):
            filename = f"text_chunk_{i:03d}.txt"
            file_path = text_folder / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
            
            saved_files.append(str(file_path))
        
        logger.info(f"Saved {len(text_chunks)} text chunks for PDF: {pdf_id}")
        return saved_files
    
    def save_tables(self, pdf_id: str, tables_html: List[str]) -> List[str]:
        """Save table HTML to individual files."""
        pdf_folder = self.create_pdf_folder(pdf_id)
        tables_folder = pdf_folder / "tables"
        
        saved_files = []
        for i, table_html in enumerate(tables_html):
            filename = f"table_{i:03d}.html"
            file_path = tables_folder / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(table_html)
            
            saved_files.append(str(file_path))
        
        logger.info(f"Saved {len(tables_html)} tables for PDF: {pdf_id}")
        return saved_files
    
    def save_images(self, pdf_id: str, images_base64: List[str]) -> List[str]:
        """Save base64 images to individual files."""
        pdf_folder = self.create_pdf_folder(pdf_id)
        images_folder = pdf_folder / "images"
        
        saved_files = []
        for i, image_b64 in enumerate(images_base64):
            # Save as both base64 text and decoded image
            filename_b64 = f"image_{i:03d}.b64"
            filename_img = f"image_{i:03d}.jpg"
            
            file_path_b64 = images_folder / filename_b64
            file_path_img = images_folder / filename_img
            
            # Save base64 text
            with open(file_path_b64, 'w', encoding='utf-8') as f:
                f.write(image_b64)
            
            # Save decoded image
            try:
                image_data = base64.b64decode(image_b64)
                with open(file_path_img, 'wb') as f:
                    f.write(image_data)
                saved_files.append(str(file_path_img))
            except Exception as e:
                logger.error(f"Error decoding image {i}: {str(e)}")
                saved_files.append(str(file_path_b64))
        
        logger.info(f"Saved {len(images_base64)} images for PDF: {pdf_id}")
        return saved_files
    
    def save_summaries(self, pdf_id: str, summaries: Dict[str, List[str]]) -> Dict[str, str]:
        """Save summaries for different content types."""
        pdf_folder = self.create_pdf_folder(pdf_id)
        summaries_folder = pdf_folder / "summaries"
        
        saved_files = {}
        
        for content_type, summary_list in summaries.items():
            filename = f"{content_type}_summaries.json"
            file_path = summaries_folder / filename
            
            # Save as JSON with metadata
            summary_data = {
                "content_type": content_type,
                "count": len(summary_list),
                "summaries": [
                    {
                        "index": i,
                        "summary": summary
                    }
                    for i, summary in enumerate(summary_list)
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            saved_files[content_type] = str(file_path)
        
        logger.info(f"Saved summaries for PDF: {pdf_id}")
        return saved_files
    
    def save_metadata(self, pdf_id: str, metadata: Dict[str, Any]) -> str:
        """Save processing metadata."""
        pdf_folder = self.create_pdf_folder(pdf_id)
        metadata_folder = pdf_folder / "metadata"
        
        filename = "processing_metadata.json"
        file_path = metadata_folder / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata for PDF: {pdf_id}")
        return str(file_path)
    
    def save_complete_processing_result(self, pdf_id: str, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Save complete processing result with organized file structure."""
        try:
            # Extract data from processing result
            text_content = processing_result.get("text_content", [])
            tables_html = processing_result.get("tables_html", [])
            images_base64 = processing_result.get("images_base64", [])
            
            # Save all content types
            saved_files = {
                "text_files": self.save_text_chunks(pdf_id, text_content),
                "table_files": self.save_tables(pdf_id, tables_html),
                "image_files": self.save_images(pdf_id, images_base64),
            }
            
            # Save metadata
            file_metadata = processing_result.get("file_metadata", {})
            metadata = {
                "pdf_id": pdf_id,
                "original_filename": file_metadata.get("original_filename", processing_result.get("file_path", "")),
                "file_size": file_metadata.get("file_size", 0),
                "upload_date": file_metadata.get("upload_date", processing_result.get("processing_timestamp", "")),
                "processing_summary": processing_result.get("summary", {}),
                "saved_files": saved_files,
                "total_files_saved": sum(len(files) for files in saved_files.values())
            }
            
            metadata_file = self.save_metadata(pdf_id, metadata)
            
            result = {
                "pdf_id": pdf_id,
                "saved_files": saved_files,
                "metadata_file": metadata_file,
                "storage_path": str(self.content_path / pdf_id)
            }
            
            logger.info(f"Complete processing result saved for PDF: {pdf_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error saving processing result for PDF {pdf_id}: {str(e)}")
            raise
    
    def get_pdf_content(self, pdf_id: str) -> Dict[str, Any]:
        """Retrieve saved content for a PDF."""
        pdf_folder = self.content_path / pdf_id
        
        if not pdf_folder.exists():
            raise FileNotFoundError(f"No content found for PDF: {pdf_id}")
        
        # Load metadata
        metadata_file = pdf_folder / "metadata" / "processing_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Get file lists
        content = {
            "pdf_id": pdf_id,
            "metadata": metadata,
            "original_filename": metadata.get("original_filename", f"Document {pdf_id[:8]}"),
            "file_size": metadata.get("file_size", 0),
            "upload_date": metadata.get("upload_date", ""),
            "text_files": list((pdf_folder / "texts").glob("*.txt")) if (pdf_folder / "texts").exists() else [],
            "table_files": list((pdf_folder / "tables").glob("*.html")) if (pdf_folder / "tables").exists() else [],
            "image_files": list((pdf_folder / "images").glob("*.jpg")) if (pdf_folder / "images").exists() else [],
            "summary_files": list((pdf_folder / "summaries").glob("*.json")) if (pdf_folder / "summaries").exists() else []
        }
        
        return content
    
    def list_processed_pdfs(self) -> List[str]:
        """Get list of all processed PDF IDs."""
        if not self.content_path.exists():
            return []
        
        return [folder.name for folder in self.content_path.iterdir() if folder.is_dir()]


# Global instance
content_storage = ContentStorageService()
