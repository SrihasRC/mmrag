import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
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
    
    def _create_text_summarizer(self):
        """Create chain for summarizing text and tables."""
        prompt_text = """
        You are an assistant tasked with summarizing tables and text.
        Give a concise summary of the table or text.
        
        Respond only with the summary, no additional comment.
        Do not start your message by saying "Here is a summary" or anything like that.
        Just give the summary as it is.
        
        Table or text chunk: {element}
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        model = ChatGroq(temperature=0.5, model="llama-3.1-8b-instant")
        return {"element": lambda x: x} | prompt | model | StrOutputParser()
    
    def _create_image_summarizer(self):
        """Create chain for summarizing images using Gemini 2.5 Flash."""
        prompt_template = """Describe the image in detail. For context,
                          the image is part of a research paper explaining the transformers
                          architecture. Be specific about graphs, such as bar plots."""
        
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
            
            # Build context from retrieved documents
            context_text = ""
            if context:
                for i, doc in enumerate(context):
                    context_text += f"Document {i+1}:\n{doc.page_content}\n\n"
            
            messages = [
                SystemMessage(
                    content="You are a helpful assistant that answers questions based on the provided context. "
                           "Use the context to provide accurate and detailed answers. If the context doesn't "
                           "contain enough information to answer the question, say so."
                ),
                HumanMessage(
                    content=f"Context:\n{context_text}\n\nQuestion: {question}"
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
    
    async def process_pdf_complete(self, file, save_content: bool = True) -> Dict[str, Any]:
        """Complete PDF processing pipeline with summarization and vector storage."""
        try:
            # Step 1: Process PDF and extract elements
            logger.info(f"Starting complete PDF processing for: {file.filename}")
            processing_result = await pdf_processor.process_pdf_file(file)
            
            pdf_id = processing_result["file_id"]
            
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
        """Generate summaries for all content types."""
        summaries = {}
        
        # Summarize text content
        text_content = processing_result.get("text_content", [])
        if text_content:
            logger.info(f"Summarizing {len(text_content)} text chunks")
            summaries["text"] = await self._summarize_text_batch(text_content)
        
        # Summarize tables
        tables_html = processing_result.get("tables_html", [])
        if tables_html:
            logger.info(f"Summarizing {len(tables_html)} tables")
            summaries["tables"] = await self._summarize_text_batch(tables_html)
        
        # Summarize images
        images_base64 = processing_result.get("images_base64", [])
        if images_base64:
            logger.info(f"Summarizing {len(images_base64)} images")
            summaries["images"] = await self._summarize_images_batch(images_base64)
        
        return summaries
    
    async def _summarize_text_batch(self, text_list: List[str]) -> List[str]:
        """Summarize a batch of text/table content."""
        try:
            summaries = self.text_summarizer.batch(text_list, {"max_concurrency": 3})
            return summaries
        except Exception as e:
            logger.error(f"Error in text summarization: {str(e)}")
            return [f"Error summarizing content: {str(e)}" for _ in text_list]
    
    async def _summarize_images_batch(self, images_base64: List[str]) -> List[str]:
        """Summarize a batch of images."""
        try:
            # Format images for the chain (using 'image' parameter as in notebook)
            formatted_images = [{"image": img} for img in images_base64]
            summaries = self.image_summarizer.batch(formatted_images, {"max_concurrency": 2})
            return summaries
        except Exception as e:
            logger.error(f"Error in image summarization: {str(e)}")
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
    
    async def query_rag(self, question: str, pdf_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """Query the RAG system."""
        try:
            logger.info(f"Processing RAG query: {question}")
            
            # Retrieve relevant documents
            filter_metadata = {"pdf_id": pdf_id} if pdf_id else None
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
                    "pdf_id": pdf_id
                }
            
            # Generate answer using QA chain
            qa_input = {
                "question": question,
                "context": retrieved_docs
            }
            
            answer = await self._run_qa_chain(qa_input)
            
            # Prepare sources information
            sources = [
                {
                    "source": doc.metadata.get("source", "unknown"),
                    "content_type": doc.metadata.get("content_type", "unknown"),
                    "pdf_id": doc.metadata.get("pdf_id", "unknown"),
                    "chunk_index": doc.metadata.get("chunk_index", -1)
                }
                for doc in retrieved_docs
            ]
            
            result = {
                "question": question,
                "answer": answer,
                "sources": sources,
                "pdf_id": pdf_id,
                "retrieved_docs_count": len(retrieved_docs)
            }
            
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
