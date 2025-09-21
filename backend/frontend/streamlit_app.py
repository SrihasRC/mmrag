import streamlit as st
import requests
import json
import base64
from PIL import Image
import io
import pandas as pd
from typing import Dict, List, Any
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Multimodal RAG Interface",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API configuration
API_BASE_URL = "http://localhost:8000"

class MultimodalRAGInterface:
    """Streamlit interface for the Multimodal RAG backend."""
    
    def __init__(self):
        self.api_base = API_BASE_URL
    
    def check_backend_health(self) -> bool:
        """Check if backend is running."""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_pdf(self, uploaded_file, save_content: bool = True) -> Dict:
        """Upload PDF to backend."""
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        params = {"save_content": save_content}
        
        response = requests.post(
            f"{self.api_base}/api/v1/rag/upload",
            files=files,
            params=params
        )
        return response.json()
    
    def query_rag(self, question: str, pdf_id: str = None, top_k: int = 5) -> Dict:
        """Query the RAG system."""
        payload = {
            "question": question,
            "pdf_id": pdf_id,
            "top_k": top_k
        }
        
        response = requests.post(
            f"{self.api_base}/api/v1/rag/query",
            json=payload
        )
        return response.json()
    
    def get_processed_pdfs(self) -> Dict:
        """Get list of processed PDFs."""
        response = requests.get(f"{self.api_base}/api/v1/rag/pdfs")
        return response.json()
    
    def get_pdf_content(self, pdf_id: str) -> Dict:
        """Get saved content for a PDF."""
        response = requests.get(f"{self.api_base}/api/v1/rag/content/{pdf_id}")
        return response.json()
    
    def get_processing_status(self, pdf_id: str) -> Dict:
        """Get processing status for a PDF."""
        response = requests.get(f"{self.api_base}/api/v1/rag/status/{pdf_id}")
        return response.json()
    
    def get_vector_store_stats(self) -> Dict:
        """Get vector store statistics."""
        response = requests.get(f"{self.api_base}/api/v1/rag/vector-store/stats")
        return response.json()
    
    def search_vector_store(self, query: str, pdf_id: str = None, k: int = 5) -> Dict:
        """Direct vector store search."""
        params = {"query": query, "k": k}
        if pdf_id:
            params["pdf_id"] = pdf_id
        
        response = requests.post(
            f"{self.api_base}/api/v1/rag/vector-store/search",
            params=params
        )
        return response.json()
    
    def delete_pdf(self, pdf_id: str) -> Dict:
        """Delete PDF data."""
        response = requests.delete(f"{self.api_base}/api/v1/rag/pdf/{pdf_id}")
        return response.json()

def main():
    """Main Streamlit application."""
    
    # Initialize interface
    rag_interface = MultimodalRAGInterface()
    
    # Header
    st.title("📚 Multimodal RAG Interface")
    st.markdown("Upload PDFs, extract multimodal content, and query using AI-powered search")
    
    # Check backend health
    if not rag_interface.check_backend_health():
        st.error("🚨 Backend is not running! Please start the FastAPI server first.")
        st.code("python start_server.py", language="bash")
        st.stop()
    
    st.success("✅ Backend is running")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📤 Upload & Process", "🔍 Query RAG", "📋 Manage PDFs", "📊 System Stats", "🔧 Advanced Tools"]
    )
    
    # Main content based on selected page
    if page == "📤 Upload & Process":
        upload_and_process_page(rag_interface)
    elif page == "🔍 Query RAG":
        query_rag_page(rag_interface)
    elif page == "📋 Manage PDFs":
        manage_pdfs_page(rag_interface)
    elif page == "📊 System Stats":
        system_stats_page(rag_interface)
    elif page == "🔧 Advanced Tools":
        advanced_tools_page(rag_interface)

def upload_and_process_page(rag_interface):
    """PDF upload and processing page."""
    st.header("📤 Upload & Process PDF")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF document to extract text, tables, and images"
    )
    
    # Processing options
    col1, col2 = st.columns(2)
    with col1:
        save_content = st.checkbox("Save extracted content to storage", value=True)
    with col2:
        show_progress = st.checkbox("Show detailed progress", value=True)
    
    if uploaded_file is not None:
        st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        if st.button("🚀 Process PDF", type="primary"):
            with st.spinner("Processing PDF... This may take a few minutes."):
                try:
                    # Upload and process
                    result = rag_interface.upload_pdf(uploaded_file, save_content)
                    
                    if result.get("status") == "completed":
                        st.success("✅ PDF processed successfully!")
                        
                        # Display results
                        display_processing_results(result)
                        
                        # Store PDF ID in session state for other pages
                        st.session_state.last_pdf_id = result["pdf_id"]
                        
                    else:
                        st.error("❌ Processing failed")
                        st.json(result)
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def display_processing_results(result: Dict):
    """Display PDF processing results."""
    pdf_id = result["pdf_id"]
    summary = result["processing_summary"]
    summaries = result.get("summaries", {})
    
    # Processing summary
    st.subheader("📊 Processing Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Chunks", summary.get("total_chunks", 0))
    with col2:
        st.metric("Text Chunks", summary.get("texts_count", 0))
    with col3:
        st.metric("Tables", summary.get("tables_count", 0))
    with col4:
        st.metric("Images", summary.get("images_count", 0))
    
    # Summaries
    if summaries:
        st.subheader("🤖 AI-Generated Summaries")
        
        # Text summaries
        if "text" in summaries:
            with st.expander(f"📝 Text Summaries ({len(summaries['text'])} items)"):
                for i, summary_text in enumerate(summaries["text"]):
                    st.markdown(f"**Chunk {i+1}:**")
                    st.write(summary_text)
                    st.divider()
        
        # Table summaries
        if "tables" in summaries:
            with st.expander(f"📊 Table Summaries ({len(summaries['tables'])} items)"):
                for i, summary_text in enumerate(summaries["tables"]):
                    st.markdown(f"**Table {i+1}:**")
                    st.write(summary_text)
                    st.divider()
        
        # Image summaries
        if "images" in summaries:
            with st.expander(f"🖼️ Image Summaries ({len(summaries['images'])} items)"):
                for i, summary_text in enumerate(summaries["images"]):
                    st.markdown(f"**Image {i+1}:**")
                    st.write(summary_text)
                    st.divider()
    
    # PDF ID for reference
    st.info(f"📋 PDF ID: `{pdf_id}` (use this ID to query specific documents)")

def query_rag_page(rag_interface):
    """RAG query page."""
    st.header("🔍 Query RAG System")
    
    # Get available PDFs
    try:
        pdfs_data = rag_interface.get_processed_pdfs()
        available_pdfs = pdfs_data.get("processed_pdfs", [])
    except:
        available_pdfs = []
    
    # Query form
    with st.form("query_form"):
        question = st.text_area(
            "Enter your question:",
            placeholder="What is the main contribution of this paper?",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            pdf_filter = st.selectbox(
                "Filter by PDF (optional):",
                ["All PDFs"] + available_pdfs,
                help="Leave as 'All PDFs' to search across all documents"
            )
        
        with col2:
            top_k = st.slider("Number of results to retrieve:", 1, 20, 5)
        
        submitted = st.form_submit_button("🔍 Query", type="primary")
    
    if submitted and question:
        pdf_id = None if pdf_filter == "All PDFs" else pdf_filter
        
        with st.spinner("Searching and generating answer..."):
            try:
                result = rag_interface.query_rag(question, pdf_id, top_k)
                
                # Display answer
                st.subheader("💡 Answer")
                st.write(result["answer"])
                
                # Display sources
                if result.get("sources"):
                    st.subheader("📚 Sources")
                    for i, source in enumerate(result["sources"]):
                        with st.expander(f"Source {i+1}: {source.get('content_type', 'unknown')} from {source.get('pdf_id', 'unknown')}"):
                            st.json(source)
                
                # Query info
                st.info(f"Retrieved {result.get('retrieved_docs_count', 0)} relevant documents")
                
            except Exception as e:
                st.error(f"❌ Query failed: {str(e)}")

def manage_pdfs_page(rag_interface):
    """PDF management page."""
    st.header("📋 Manage PDFs")
    
    # Get processed PDFs
    try:
        pdfs_data = rag_interface.get_processed_pdfs()
        available_pdfs = pdfs_data.get("processed_pdfs", [])
        
        if not available_pdfs:
            st.info("No PDFs processed yet. Upload a PDF first!")
            return
        
        st.success(f"Found {len(available_pdfs)} processed PDFs")
        
        # PDF selection
        selected_pdf = st.selectbox("Select a PDF to manage:", available_pdfs)
        
        if selected_pdf:
            # Get PDF status
            try:
                status = rag_interface.get_processing_status(selected_pdf)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Content Stored", "✅" if status.get("content_stored") else "❌")
                with col2:
                    st.metric("Embeddings Created", "✅" if status.get("embeddings_created") else "❌")
                with col3:
                    st.metric("Status", status.get("status", "Unknown"))
                
            except Exception as e:
                st.error(f"Error getting status: {str(e)}")
            
            # Content viewer
            st.subheader("📄 Content Viewer")
            
            try:
                content = rag_interface.get_pdf_content(selected_pdf)
                
                # Tabs for different content types
                tab1, tab2, tab3, tab4 = st.tabs(["📝 Text Files", "📊 Tables", "🖼️ Images", "📋 Metadata"])
                
                with tab1:
                    text_files = content.get("text_files", [])
                    if text_files:
                        st.info(f"Found {len(text_files)} text files")
                        for i, file_path in enumerate(text_files):
                            with st.expander(f"Text Chunk {i+1}"):
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        st.text(f.read())
                                except Exception as e:
                                    st.error(f"Error reading file: {str(e)}")
                    else:
                        st.info("No text files found")
                
                with tab2:
                    table_files = content.get("table_files", [])
                    if table_files:
                        st.info(f"Found {len(table_files)} table files")
                        for i, file_path in enumerate(table_files):
                            with st.expander(f"Table {i+1}"):
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        html_content = f.read()
                                        st.components.v1.html(html_content, height=300, scrolling=True)
                                except Exception as e:
                                    st.error(f"Error reading file: {str(e)}")
                    else:
                        st.info("No table files found")
                
                with tab3:
                    image_files = content.get("image_files", [])
                    if image_files:
                        st.info(f"Found {len(image_files)} image files")
                        cols = st.columns(2)
                        for i, file_path in enumerate(image_files):
                            with cols[i % 2]:
                                try:
                                    image = Image.open(file_path)
                                    st.image(image, caption=f"Image {i+1}", use_column_width=True)
                                except Exception as e:
                                    st.error(f"Error loading image: {str(e)}")
                    else:
                        st.info("No image files found")
                
                with tab4:
                    metadata = content.get("metadata", {})
                    if metadata:
                        st.json(metadata)
                    else:
                        st.info("No metadata found")
                        
            except Exception as e:
                st.error(f"Error loading content: {str(e)}")
            
            # Delete PDF
            st.subheader("🗑️ Delete PDF")
            st.warning("This will permanently delete all data for this PDF from the system.")
            
            if st.button("🗑️ Delete PDF Data", type="secondary"):
                if st.button("⚠️ Confirm Delete", type="secondary"):
                    try:
                        result = rag_interface.delete_pdf(selected_pdf)
                        st.success("PDF data deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting PDF: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading PDFs: {str(e)}")

def system_stats_page(rag_interface):
    """System statistics page."""
    st.header("📊 System Statistics")
    
    # Vector store stats
    try:
        stats = rag_interface.get_vector_store_stats()
        
        st.subheader("🗄️ Vector Database Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", stats.get("total_documents", 0))
        with col2:
            st.metric("Unique PDFs", stats.get("unique_pdfs", 0))
        with col3:
            content_types = stats.get("content_types", {})
            st.metric("Content Types", len(content_types))
        
        # Content type breakdown
        if content_types:
            st.subheader("📈 Content Type Distribution")
            df = pd.DataFrame(list(content_types.items()), columns=["Content Type", "Count"])
            st.bar_chart(df.set_index("Content Type"))
        
        # PDF list
        pdf_ids = stats.get("pdf_ids", [])
        if pdf_ids:
            st.subheader("📋 Processed PDFs")
            for pdf_id in pdf_ids:
                st.code(pdf_id)
        
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
    
    # Backend health
    st.subheader("🏥 Backend Health")
    try:
        health_response = requests.get(f"{rag_interface.api_base}/api/v1/rag/health")
        health_data = health_response.json()
        
        if health_data.get("status") == "healthy":
            st.success("✅ System is healthy")
        else:
            st.warning("⚠️ System status: " + health_data.get("status", "unknown"))
        
        with st.expander("Detailed Health Information"):
            st.json(health_data)
            
    except Exception as e:
        st.error(f"Error checking health: {str(e)}")

def advanced_tools_page(rag_interface):
    """Advanced tools page."""
    st.header("🔧 Advanced Tools")
    
    # Direct vector search
    st.subheader("🔍 Direct Vector Search")
    st.info("Search the vector database directly (for debugging and testing)")
    
    with st.form("vector_search_form"):
        search_query = st.text_input("Search query:")
        
        col1, col2 = st.columns(2)
        with col1:
            search_pdf_id = st.text_input("PDF ID (optional):")
        with col2:
            search_k = st.slider("Number of results:", 1, 20, 5)
        
        search_submitted = st.form_submit_button("🔍 Search Vector Store")
    
    if search_submitted and search_query:
        try:
            pdf_id = search_pdf_id if search_pdf_id else None
            result = rag_interface.search_vector_store(search_query, pdf_id, search_k)
            
            st.subheader("🎯 Search Results")
            results = result.get("results", [])
            
            for i, res in enumerate(results):
                with st.expander(f"Result {i+1} (Score: {res.get('similarity_score', 0):.4f})"):
                    st.write("**Content:**")
                    st.write(res.get("content", ""))
                    st.write("**Metadata:**")
                    st.json(res.get("metadata", {}))
                    
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
    
    # API endpoint tester
    st.subheader("🌐 API Endpoint Tester")
    st.info("Test API endpoints directly")
    
    endpoint = st.selectbox(
        "Select endpoint:",
        [
            "/health",
            "/api/v1/rag/health", 
            "/api/v1/rag/pdfs",
            "/api/v1/rag/vector-store/stats"
        ]
    )
    
    if st.button("📡 Test Endpoint"):
        try:
            response = requests.get(f"{rag_interface.api_base}{endpoint}")
            st.write(f"**Status Code:** {response.status_code}")
            st.json(response.json())
        except Exception as e:
            st.error(f"Request failed: {str(e)}")

if __name__ == "__main__":
    main()
