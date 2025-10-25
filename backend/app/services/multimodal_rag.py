import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import numpy as np
from fastapi import HTTPException

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from app.services.pdf_processor import pdf_processor
from app.services.content_storage import content_storage
from app.services.vector_store import vector_store_service
from app.config.config import settings

# Set environment variables for the services
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

logger = logging.getLogger(__name__)


class MultimodalRAGService:
    """Service for multimodal RAG processing including summarization and retrieval."""
    
    def __init__(self):
        self.text_summarizer = self._create_text_summarizer()
        self.image_summarizer = self._create_image_summarizer()
        self.qa_chain = self._create_qa_chain()
        self._last_groq_request = 0
        self._last_gemini_request = 0
    
    def _create_text_summarizer(self):
        """Create chain for summarizing text and tables with detail preservation."""
        prompt_text = """
        You are an assistant tasked with creating detailed, informative summaries that preserve all important information.
        
        Document Type: {doc_type}
        Document Context: {doc_context}
        
        Content to summarize: {element}
        
        Instructions:
        - For resumes: Include ALL names, numbers, percentages, GPAs, companies, projects, skills, and dates
        - For academic papers: Preserve technical details, figures, and specific findings
        - For any document: Keep specific details like scores, percentages, names, locations, technologies
        - DO NOT omit numerical data, proper nouns, or specific technical terms
        - Create a comprehensive summary that someone could use to answer detailed questions
        
        Provide a detailed summary that preserves all key information:
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        model = ChatGroq(temperature=0.1, model="llama-3.1-8b-instant")  # Lower temperature for consistency
        return prompt | model | StrOutputParser()
    
    async def _rate_limit_groq(self, min_delay: float = 2.0):
        """Ensure minimum delay between Groq API calls."""
        import time
        import asyncio
        
        current_time = time.time()
        time_since_last = current_time - self._last_groq_request
        
        if time_since_last < min_delay:
            delay = min_delay - time_since_last
            logger.info(f"Rate limiting: waiting {delay:.1f}s before next Groq request")
            await asyncio.sleep(delay)
        
        self._last_groq_request = time.time()
    
    async def _rate_limit_gemini(self, min_delay: float = 3.0):
        """Ensure minimum delay between Gemini API calls."""
        import time
        import asyncio
        
        current_time = time.time()
        time_since_last = current_time - self._last_gemini_request
        
        if time_since_last < min_delay:
            delay = min_delay - time_since_last
            logger.info(f"Rate limiting: waiting {delay:.1f}s before next Gemini request")
            await asyncio.sleep(delay)
        
        self._last_gemini_request = time.time()
    
    def _create_image_summarizer(self):
        """Create chain for summarizing images using Gemini 2.5 Flash with context."""
        # Updated to handle context parameter
        prompt_template = """Describe the image in detail. 
        
        {context}
        
        Focus on details that would be relevant for answering questions about this document.
        Be specific about graphs, charts, diagrams, and any text visible in the image."""
        
        messages = [
            (
                "user",
                [
                    {"type": "text", "text": prompt_template},
                    {
                        "type": "image_url", 
                        "image_url": {"url": "data:image/jpeg;base64,{image}"},
                    },
                ],
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Using Gemini 2.5 Flash for image analysis
        return prompt | ChatGoogleGenerativeAI(model="gemini-2.5-flash") | StrOutputParser()
    
    def _create_qa_chain(self):
        """Create chain for question answering."""
        def build_prompt(inputs):
            question = inputs["question"]
            context = inputs["context"]
            
            # Build context from retrieved documents with metadata
            context_text = ""
            document_sources = set()
            if context:
                for i, doc in enumerate(context):
                    pdf_id = doc.metadata.get("pdf_id", "unknown")
                    document_sources.add(pdf_id)
                    context_text += f"Document {i+1} (Source: {pdf_id}):\n{doc.page_content}\n\n"
            
            # Create system message that's aware of multiple documents
            num_sources = len(document_sources)
            system_content = (
                "You are a helpful assistant that answers questions based on the provided context. "
                f"You have been provided with information from {num_sources} different source document(s). "
                "When answering, consider information from ALL provided documents. "
                "If comparing or contrasting information, explicitly reference the different sources. "
                "Use the context to provide accurate and detailed answers. If the context doesn't "
                "contain enough information to answer the question, say so."
            )
            
            messages = [
                SystemMessage(content=system_content),
                HumanMessage(
                    content=f"Context from {num_sources} document source(s):\n\n{context_text}\n\nQuestion: {question}"
                )
            ]
            return messages
        
        return (
            {
                "context": lambda x: x["context"],
                "question": lambda x: x["question"],
            }
            | RunnableLambda(build_prompt)
            | ChatGoogleGenerativeAI(model="gemini-2.5-flash")
            | StrOutputParser()
        )
    
    def _create_document_context(self, processing_result: Dict, doc_type: str) -> str:
        """Create a brief document context for better summarization."""
        try:
            separated_elements = processing_result.get("separated_elements", {})
            total_texts = len(separated_elements.get('texts', []))
            total_tables = len(separated_elements.get('tables', []))
            total_images = len(separated_elements.get('images', []))
            
            # Get first few sentences for context
            context_text = ""
            text_content = processing_result.get("text_content", [])
            if text_content:
                # Get first 200 chars as context
                context_text = text_content[0][:200].strip() + "..." if text_content[0] else ""
            
            context = f"""
            Document Overview:
            - Type: {doc_type}
            - Structure: {total_texts} text sections, {total_tables} tables, {total_images} images
            - Opening content: {context_text}
            """
            
            return context.strip()
        except Exception as e:
            logger.warning(f"Could not create document context: {str(e)}")
            return f"Document type: {doc_type}"
    
    def _should_preserve_raw_content(self, doc_type: str, total_length: int) -> bool:
        """Determine if we should preserve raw content alongside summaries."""
        # For short documents like resumes, preserve raw content
        if doc_type in ["resume", "short_document"] or total_length < 8000:
            return True
        return False
    
    async def _enhance_context_for_multi_pdfs(self, retrieved_docs: List, question: str, pdf_ids: Optional[List[str]] = None) -> List:
        """Enhance context for multiple PDFs by ensuring relevant content from all selected documents."""
        if not retrieved_docs:
            return retrieved_docs
        
        try:
            enhanced_docs = list(retrieved_docs)
            
            if pdf_ids and len(pdf_ids) > 1:
                # Check which PDFs are represented in the retrieved docs
                represented_pdfs = {doc.metadata.get("pdf_id") for doc in retrieved_docs}
                missing_pdfs = set(pdf_ids) - represented_pdfs
                
                # For PDFs that don't have any retrieved documents, get some relevant content
                for missing_pdf_id in missing_pdfs:
                    try:
                        # Get relevant documents from this PDF using the same query
                        additional_docs = await vector_store_service.similarity_search(
                            query=question,
                            k=3,  # Get a few relevant documents from this PDF
                            filter_metadata={"pdf_id": missing_pdf_id}
                        )
                        
                        if additional_docs:
                            logger.info(f"Adding {len(additional_docs)} relevant documents from missing PDF {missing_pdf_id}")
                            enhanced_docs.extend(additional_docs)
                        else:
                            # If no relevant docs found with the query, get the first few chunks
                            # This ensures we have some content from each selected PDF
                            fallback_docs = await vector_store_service.similarity_search(
                                query="",  # Empty query
                                k=2,  # Just get a couple of documents
                                filter_metadata={"pdf_id": missing_pdf_id}
                            )
                            if fallback_docs:
                                logger.info(f"Adding {len(fallback_docs)} fallback documents from PDF {missing_pdf_id}")
                                enhanced_docs.extend(fallback_docs)
                                
                    except Exception as e:
                        logger.warning(f"Could not enhance context for missing PDF {missing_pdf_id}: {str(e)}")
                        continue
            
            return enhanced_docs
            
        except Exception as e:
            logger.error(f"Error enhancing context for multiple PDFs: {str(e)}")
            return retrieved_docs

    async def _enhance_context_for_query(self, retrieved_docs: List, question: str, pdf_id: Optional[str] = None) -> List:
        """Enhance context by adding related chunks for better coherence."""
        if not retrieved_docs:
            return retrieved_docs
        
        try:
            # For documents with few chunks (like resumes), get more context
            if pdf_id:
                # Get document statistics to determine if it's a short document
                all_docs_for_pdf = await vector_store_service.similarity_search(
                    query="",  # Empty query to get all docs
                    k=50,  # Get many documents
                    filter_metadata={"pdf_id": pdf_id}
                )
                
                # If it's a short document (< 5 chunks), include more context
                if len(all_docs_for_pdf) <= 5:
                    logger.info(f"Short document detected ({len(all_docs_for_pdf)} chunks). Including full context.")
                    # For short documents, return more comprehensive context
                    enhanced_docs = all_docs_for_pdf[:8]  # Get more chunks
                    
                    # Sort by chunk_index if available for better flow
                    try:
                        enhanced_docs.sort(key=lambda x: x.metadata.get("chunk_index", 0))
                    except:
                        pass
                        
                    return enhanced_docs
            
            # For longer documents, enhance with neighboring chunks
            enhanced_docs = list(retrieved_docs)
            
            # Try to get neighboring chunks for better context
            for doc in retrieved_docs[:3]:  # Only for top 3 results
                try:
                    chunk_index = doc.metadata.get("chunk_index", -1)
                    doc_pdf_id = doc.metadata.get("pdf_id")
                    
                    if chunk_index >= 0 and doc_pdf_id:
                        # Try to get previous and next chunk
                        for neighbor_index in [chunk_index - 1, chunk_index + 1]:
                            if neighbor_index >= 0:
                                neighbor_docs = await vector_store_service.similarity_search(
                                    query=question,
                                    k=20,
                                    filter_metadata={
                                        "pdf_id": doc_pdf_id,
                                        "chunk_index": neighbor_index
                                    }
                                )
                                
                                # Add if not already present
                                for neighbor in neighbor_docs:
                                    if neighbor not in enhanced_docs:
                                        enhanced_docs.append(neighbor)
                                        
                except Exception as e:
                    logger.warning(f"Could not get neighboring chunks: {str(e)}")
                    continue
            
            # Limit to reasonable size and sort by relevance
            enhanced_docs = enhanced_docs[:10]
            logger.info(f"Enhanced context from {len(retrieved_docs)} to {len(enhanced_docs)} documents")
            
            return enhanced_docs
            
        except Exception as e:
            logger.warning(f"Error enhancing context: {str(e)}")
            return retrieved_docs  # Fallback to original docs
    
    async def process_pdf_complete(
        self, 
        file, 
        save_content: bool = True,
        use_semantic_chunking: bool = True
    ) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline with summarization and vector storage.
        
        Args:
            file: Uploaded PDF file
            save_content: Whether to save extracted content
            use_semantic_chunking: Whether to use neural semantic chunking
        """
        try:
            # Get file metadata before processing
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            file_size = len(file_content)
            
            # Step 1: Process PDF and extract elements
            logger.info(
                f"Starting complete PDF processing for: {file.filename} ({file_size} bytes), "
                f"semantic_chunking={use_semantic_chunking}"
            )
            processing_result = await pdf_processor.process_pdf_file(
                file,
                use_semantic_chunking=use_semantic_chunking
            )
            
            pdf_id = processing_result["file_id"]
            
            # Add file metadata to processing result
            processing_result["file_metadata"] = {
                "original_filename": file.filename,
                "file_size": file_size,
                "upload_date": processing_result.get("processing_timestamp", "")
            }
            
            # Step 2: Generate summaries
            logger.info(f"Generating summaries for PDF: {pdf_id}")
            summaries = await self._generate_all_summaries(processing_result)
            
            # Step 3: Save content to organized folders (if requested)
            storage_result = None
            if save_content:
                logger.info(f"Saving content to storage for PDF: {pdf_id}")
                storage_result = content_storage.save_complete_processing_result(pdf_id, processing_result)
                
                # Also save summaries
                content_storage.save_summaries(pdf_id, summaries)
            
            # Step 4: Create and store embeddings
            logger.info(f"Creating embeddings for PDF: {pdf_id}")
            embedding_result = await self._create_and_store_embeddings(pdf_id, processing_result, summaries)
            
            # Step 5: Compile final result
            result = {
                "pdf_id": pdf_id,
                "processing_summary": processing_result["summary"],
                "summaries": summaries,
                "storage_result": storage_result,
                "embedding_result": embedding_result,
                "status": "completed"
            }
            
            logger.info(f"Complete PDF processing finished for: {file.filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error in complete PDF processing: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")
    
    async def _generate_all_summaries(self, processing_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate summaries for all content types with document context awareness."""
        summaries = {}
        
        # Get document context
        doc_type = processing_result.get("document_type", "general")
        doc_context = self._create_document_context(processing_result, doc_type)
        
        # Check if we should preserve raw content for short documents
        total_length = sum(len(text) for text in processing_result.get("text_content", []))
        preserve_raw = self._should_preserve_raw_content(doc_type, total_length)
        
        logger.info(f"Generating context-aware summaries for {doc_type} document (preserve_raw: {preserve_raw})")
        
        # Summarize text content with context
        text_content = processing_result.get("text_content", [])
        if text_content:
            logger.info(f"Summarizing {len(text_content)} text chunks with document context")
            text_summaries = await self._summarize_text_batch(text_content, doc_type, doc_context)
            
            # For short documents, combine summaries with raw content for better retrieval
            if preserve_raw:
                enhanced_summaries = []
                for i, (summary, raw_text) in enumerate(zip(text_summaries, text_content)):
                    # Combine summary with key raw excerpts
                    enhanced_summary = f"{summary}\n\nKey details from original: {raw_text[:500]}..."
                    enhanced_summaries.append(enhanced_summary)
                summaries["text"] = enhanced_summaries
            else:
                summaries["text"] = text_summaries
        
        # Summarize tables with context
        tables_html = processing_result.get("tables_html", [])
        if tables_html:
            logger.info(f"Summarizing {len(tables_html)} tables with document context")
            summaries["tables"] = await self._summarize_text_batch(tables_html, doc_type, doc_context)
        
        # Summarize images with context
        images_base64 = processing_result.get("images_base64", [])
        if images_base64:
            logger.info(f"Summarizing {len(images_base64)} images with document context")
            summaries["images"] = await self._summarize_images_batch(images_base64, doc_type, doc_context)
        
        return summaries
    
    async def _summarize_text_batch(self, text_list: List[str], doc_type: str = "general", doc_context: str = "") -> List[str]:
        """Summarize a batch of text/table content with document context."""
        import asyncio
        
        try:
            # Create context-aware inputs
            context_inputs = [
                {
                    "element": text,
                    "doc_type": doc_type,
                    "doc_context": doc_context
                }
                for text in text_list
            ]
            
            # Use sequential processing with proper rate limiting
            summaries = []
            for i, input_data in enumerate(context_inputs):
                try:
                    # Rate limit Groq requests
                    await self._rate_limit_groq()
                    
                    summary = await self.text_summarizer.ainvoke(input_data)
                    summaries.append(summary)
                    logger.info(f"Completed text summarization {i+1}/{len(context_inputs)}")
                    
                except Exception as e:
                    logger.warning(f"Failed to summarize chunk {i+1}: {str(e)}")
                    summaries.append(f"Summarization failed for chunk {i+1}")
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error in context-aware text summarization: {str(e)}")
            # Fallback to simple summarization without context
            try:
                simple_inputs = [{"element": text, "doc_type": doc_type, "doc_context": ""} for text in text_list]
                summaries = []
                for i, input_data in enumerate(simple_inputs):
                    await self._rate_limit_groq()
                    summary = await self.text_summarizer.ainvoke(input_data)
                    summaries.append(summary)
                return summaries
            except:
                return [f"Error summarizing content: {str(e)}" for _ in text_list]
    
    async def _summarize_images_batch(self, images_base64: List[str], doc_type: str = "general", doc_context: str = "") -> List[str]:
        """Summarize a batch of images with document context."""
        try:
            # Create context-aware image prompt
            context_prompt = f"""
            Document Type: {doc_type}
            Context: {doc_context}
            
            Describe this image in detail, considering its role in a {doc_type} document.
            Focus on relevant details that would help answer questions about this document.
            """
            
            # Process images sequentially with proper rate limiting
            summaries = []
            for i, img in enumerate(images_base64):
                try:
                    # Rate limit Gemini requests  
                    await self._rate_limit_gemini()
                    
                    formatted_input = {"image": img, "context": context_prompt}
                    summary = await self.image_summarizer.ainvoke(formatted_input)
                    summaries.append(summary)
                    logger.info(f"Completed image summarization {i+1}/{len(images_base64)}")
                    
                except Exception as e:
                    logger.warning(f"Failed to summarize image {i+1}: {str(e)}")
                    summaries.append(f"Image summarization failed for image {i+1}")
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error in context-aware image summarization: {str(e)}")
            # Fallback to simple image summarization
            try:
                summaries = []
                for i, img in enumerate(images_base64):
                    await self._rate_limit_gemini()
                    simple_input = {"image": img}
                    summary = await self.image_summarizer.ainvoke(simple_input)
                    summaries.append(summary)
                return summaries
            except:
                return [f"Error summarizing image: {str(e)}" for _ in images_base64]
    
    async def _create_and_store_embeddings(self, pdf_id: str, processing_result: Dict[str, Any], summaries: Dict[str, List[str]]) -> Dict[str, Any]:
        """Create embeddings and store in vector database."""
        try:
            # Prepare documents for embedding
            documents = []
            
            # Add text summaries
            for i, summary in enumerate(summaries.get("text", [])):
                documents.append({
                    "content": summary,
                    "metadata": {
                        "pdf_id": pdf_id,
                        "content_type": "text",
                        "chunk_index": i,
                        "source": f"{pdf_id}_text_{i}"
                    }
                })
            
            # Add table summaries
            for i, summary in enumerate(summaries.get("tables", [])):
                documents.append({
                    "content": summary,
                    "metadata": {
                        "pdf_id": pdf_id,
                        "content_type": "table",
                        "chunk_index": i,
                        "source": f"{pdf_id}_table_{i}"
                    }
                })
            
            # Add image summaries
            for i, summary in enumerate(summaries.get("images", [])):
                documents.append({
                    "content": summary,
                    "metadata": {
                        "pdf_id": pdf_id,
                        "content_type": "image",
                        "chunk_index": i,
                        "source": f"{pdf_id}_image_{i}"
                    }
                })
            
            # Store in vector database
            if documents:
                vector_result = await vector_store_service.add_documents(documents)
                logger.info(f"Stored {len(documents)} documents in vector database for PDF: {pdf_id}")
                return vector_result
            else:
                logger.warning(f"No documents to store for PDF: {pdf_id}")
                return {"status": "no_documents", "count": 0}
                
        except Exception as e:
            logger.error(f"Error creating embeddings for PDF {pdf_id}: {str(e)}")
            raise
    
    async def query_rag(self, question: str, pdf_ids: Optional[List[str]] = None, pdf_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """Query the RAG system with enhanced document-level context awareness. Supports multiple PDFs."""
        try:
            logger.info(f"Processing RAG query: {question}")
            
            # Handle backward compatibility and multiple PDF IDs
            target_pdf_ids = pdf_ids or ([pdf_id] if pdf_id else None)
            
            # Retrieve relevant documents
            filter_metadata = None
            if target_pdf_ids:
                if len(target_pdf_ids) == 1:
                    filter_metadata = {"pdf_id": target_pdf_ids[0]}
                else:
                    # For multiple PDFs, ChromaDB uses different syntax
                    # We'll need to modify the vector store service to handle this
                    # For now, let's search without filter and filter results later
                    filter_metadata = None
            
            if target_pdf_ids and len(target_pdf_ids) > 1:
                # For multiple PDFs, search without filter and then filter results
                all_docs = await vector_store_service.similarity_search(
                    query=question,
                    k=top_k * 3,  # Get more results to ensure we have enough after filtering
                    filter_metadata=None
                )
                # Filter results to only include documents from target PDFs
                retrieved_docs = [doc for doc in all_docs if doc.metadata.get("pdf_id") in target_pdf_ids][:top_k]
            else:
                # Single PDF or no filter
                retrieved_docs = await vector_store_service.similarity_search(
                    query=question,
                    k=top_k,
                    filter_metadata=filter_metadata
                )
            
            if not retrieved_docs:
                return {
                    "question": question,
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": [],
                    "pdf_id": target_pdf_ids[0] if target_pdf_ids else None,
                    "retrieved_docs_count": 0
                }
            
            # For short documents or resumes, get additional context
            enhanced_context = await self._enhance_context_for_multi_pdfs(retrieved_docs, question, target_pdf_ids)
            
            # Generate answer using QA chain with enhanced context
            qa_input = {
                "question": question,
                "context": enhanced_context
            }
            
            answer = await self._run_qa_chain(qa_input)
            
            # Prepare references using original text chunks from storage
            references = []
            for doc in retrieved_docs:
                doc_pdf_id = doc.metadata.get("pdf_id", "unknown")
                chunk_index = doc.metadata.get("chunk_index", 0)
                
                # Get original text chunk from storage instead of summary
                snippet = doc.page_content[:800] if doc.page_content else "No content available"
                try:
                    if doc_pdf_id != "unknown":
                        original_content = content_storage.get_text_chunk(doc_pdf_id, chunk_index)
                        if original_content and original_content != "Text chunk not found":
                            snippet = original_content  # Don't truncate - show full content
                except Exception as e:
                    logger.warning(f"Could not load original text chunk for {doc_pdf_id}:{chunk_index}, using fallback")
                
                references.append({
                    "documentId": doc_pdf_id,
                    "pageNumber": doc.metadata.get("page_number", 1),
                    "snippet": snippet,
                    "relevanceScore": getattr(doc, 'similarity_score', 0.8),
                    "contentType": doc.metadata.get("content_type", "text")
                })
            
            result = {
                "question": question,
                "answer": answer,
                "references": references,  # Frontend expects this
                "sources": [],  # Keep for backward compatibility
                "pdf_id": target_pdf_ids[0] if target_pdf_ids else None,
                "retrieved_docs_count": len(retrieved_docs)
            }
            
            # Provide feedback to adaptive threshold (RL component)
            # Heuristic: If we got good retrieval (multiple docs with high scores), it's useful
            if retrieved_docs:
                avg_score = np.mean([getattr(doc, 'similarity_score', 0.8) for doc in retrieved_docs])
                chunk_was_useful = avg_score > 0.6 and len(retrieved_docs) >= top_k // 2
                
                # Provide feedback to semantic chunker's adaptive threshold
                try:
                    from app.services.pdf_processor import pdf_processor
                    if pdf_processor.semantic_chunker and pdf_processor.semantic_chunker.adaptive_threshold:
                        pdf_processor.semantic_chunker.provide_feedback(
                            chunk_was_useful=chunk_was_useful,
                            retrieval_score=float(avg_score)
                        )
                except Exception as e:
                    logger.debug(f"Could not provide RL feedback: {e}")
            
            logger.info(f"RAG query completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG query: {str(e)}")
            raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")
    
    async def _run_qa_chain(self, qa_input: Dict[str, Any]) -> str:
        """Run the QA chain asynchronously."""
        try:
            # Pass the full qa_input dictionary to the chain
            answer = self.qa_chain.invoke(qa_input)
            return answer
        except Exception as e:
            logger.error(f"Error in QA chain: {str(e)}")
            logger.error(f"QA input was: {qa_input}")
            return f"Error generating answer: {str(e)}"
    
    def get_processing_status(self, pdf_id: str) -> Dict[str, Any]:
        """Get processing status for a PDF."""
        try:
            # Check if content exists in storage
            content_exists = pdf_id in content_storage.list_processed_pdfs()
            
            # Check if embeddings exist in vector store
            embeddings_exist = vector_store_service.check_pdf_exists(pdf_id)
            
            return {
                "pdf_id": pdf_id,
                "content_stored": content_exists,
                "embeddings_created": embeddings_exist,
                "status": "completed" if (content_exists and embeddings_exist) else "partial"
            }
        except Exception as e:
            logger.error(f"Error checking processing status for PDF {pdf_id}: {str(e)}")
            return {
                "pdf_id": pdf_id,
                "status": "error",
                "error": str(e)
            }


# Global instance
multimodal_rag_service = MultimodalRAGService()
