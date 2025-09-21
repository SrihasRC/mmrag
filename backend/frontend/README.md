# Multimodal RAG Streamlit Interface

A comprehensive Streamlit web interface for testing and interacting with the Multimodal RAG FastAPI backend. This interface provides an intuitive way to upload PDFs, view extracted content, query the system, and manage your documents.

## 🚀 Features

- **📤 PDF Upload & Processing**: Upload PDFs and view real-time processing results
- **🔍 RAG Query Interface**: Natural language querying with source attribution
- **📋 Content Management**: View and manage extracted text chunks, tables, and images
- **📊 System Statistics**: Monitor vector database and system health
- **🔧 Advanced Tools**: Direct vector search and API endpoint testing
- **🖼️ Image Viewer**: Display extracted images with AI-generated descriptions
- **📊 Table Viewer**: Render extracted tables in HTML format
- **📝 Text Viewer**: Browse through extracted text chunks

## 📁 Project Structure

```
frontend/
├── streamlit_app.py          # Main Streamlit application
├── run_streamlit.py          # Startup script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8+
- FastAPI backend running on `http://localhost:8000`

### 1. Navigate to Frontend Directory
```bash
cd /home/srihasrc/Music/mmrag/frontend
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Interface
```bash
# Using the startup script (recommended)
python run_streamlit.py

# Or directly with Streamlit
streamlit run streamlit_app.py --server.port=8501
```

## 🌐 Access the Interface

Once started, the interface will be available at:
- **Local**: http://localhost:8501
- **Network**: http://0.0.0.0:8501

## 📱 Interface Pages

### 1. 📤 Upload & Process
- Upload PDF files (drag & drop or file picker)
- Configure processing options
- View real-time processing results
- Display AI-generated summaries for text, tables, and images
- Show processing statistics (chunks, tables, images count)

### 2. 🔍 Query RAG
- Natural language query interface
- Filter by specific PDF or search all documents
- Adjust number of retrieved results
- View AI-generated answers with source attribution
- Display relevant document chunks used for answering

### 3. 📋 Manage PDFs
- List all processed PDFs
- View processing status for each PDF
- Browse extracted content:
  - **Text Files**: View individual text chunks
  - **Tables**: Render HTML tables
  - **Images**: Display extracted images
  - **Metadata**: View processing metadata
- Delete PDF data from the system

### 4. 📊 System Stats
- Vector database statistics
- Content type distribution charts
- List of processed PDFs
- Backend health monitoring
- System performance metrics

### 5. 🔧 Advanced Tools
- **Direct Vector Search**: Query the vector database directly
- **API Endpoint Tester**: Test backend endpoints
- **Debug Information**: View raw API responses
- **System Diagnostics**: Advanced troubleshooting tools

## 🎯 Key Features

### Content Visualization
- **Text Chunks**: Organized display of extracted text segments
- **Tables**: HTML rendering of extracted tables with proper formatting
- **Images**: Gallery view of extracted images with AI descriptions
- **Summaries**: AI-generated summaries for all content types

### Query Interface
- **Smart Search**: Semantic search across all content types
- **Source Attribution**: See which documents contributed to answers
- **Filtering**: Query specific PDFs or search globally
- **Relevance Scoring**: View similarity scores for retrieved content

### Management Tools
- **Processing Status**: Monitor PDF processing pipeline
- **Content Browser**: Navigate through extracted content
- **Data Management**: Delete or reorganize PDF data
- **Statistics Dashboard**: System usage and performance metrics

## 🔧 Configuration

### Backend Connection
The interface connects to the FastAPI backend at `http://localhost:8000` by default. To change this:

```python
# In streamlit_app.py
API_BASE_URL = "http://your-backend-url:port"
```

### Streamlit Configuration
Customize the interface by modifying `streamlit_app.py`:

```python
st.set_page_config(
    page_title="Your Custom Title",
    page_icon="🔬",
    layout="wide"
)
```

## 🚨 Troubleshooting

### Backend Not Running
```
❌ Backend is not running! Please start the FastAPI server first.
```
**Solution**: Start the backend first:
```bash
cd ../backend
python start_server.py
```

### Connection Errors
```
Error: Connection refused
```
**Solution**: Check if backend is running on correct port:
```bash
curl http://localhost:8000/health
```

### Missing Dependencies
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: Install requirements:
```bash
pip install -r requirements.txt
```

### File Upload Issues
- Ensure PDF files are valid and not corrupted
- Check file size limits (backend may have restrictions)
- Verify PDF is not password-protected

## 📋 Usage Workflow

1. **Start Backend**: Ensure FastAPI server is running
2. **Launch Interface**: Run the Streamlit app
3. **Upload PDF**: Use the Upload & Process page
4. **View Content**: Check extracted text, tables, and images
5. **Query System**: Ask questions about your documents
6. **Manage Data**: Use the management tools as needed

## 🎨 Interface Screenshots

### Upload & Process Page
- File upload with drag & drop
- Processing progress indicators
- Real-time results display
- Summary statistics

### Query Interface
- Natural language input
- PDF filtering options
- Answer display with sources
- Relevance scoring

### Content Management
- Tabbed content viewer
- Image gallery
- Table renderer
- Metadata browser

## 🔒 Security Notes

- The interface connects to localhost by default
- No authentication is implemented (add if needed for production)
- File uploads are processed by the backend
- Ensure backend security measures are in place

## 🤝 Contributing

To extend the interface:

1. **Add New Pages**: Create new functions and add to navigation
2. **Enhance Visualizations**: Use Streamlit components for better displays
3. **Add Features**: Integrate new backend endpoints
4. **Improve UX**: Enhance user experience with better layouts

## 📄 Dependencies

- **streamlit**: Web interface framework
- **requests**: HTTP client for backend communication
- **pillow**: Image processing and display
- **pandas**: Data manipulation for statistics

## 🔗 Related

- [Backend Documentation](../backend/README.md)
- [API Documentation](http://localhost:8000/docs)
- [Streamlit Documentation](https://docs.streamlit.io)

---

This interface provides a complete testing and management environment for your Multimodal RAG system. Upload documents, explore extracted content, and query your knowledge base through an intuitive web interface!
