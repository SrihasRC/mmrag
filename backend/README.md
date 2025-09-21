# Multimodal RAG FastAPI Backend

A production-ready FastAPI backend implementation of multimodal RAG (Retrieval-Augmented Generation) system that processes PDF documents to extract text, tables, and images, generates summaries, and enables semantic search using Cohere embeddings.

## 🚀 Features

- **📄 PDF Processing**: Extract text, tables, and images from PDF documents
- **🤖 AI Summarization**: Generate summaries using Groq (text/tables) and OpenAI (images)
- **🔍 Semantic Search**: Vector similarity search using Cohere embeddings
- **💾 Organized Storage**: Save extracted content in structured folders per PDF
- **🌐 REST API**: Comprehensive FastAPI endpoints with automatic documentation
- **🔄 Multimodal RAG**: Query across text, table, and image content simultaneously

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── multimodal_rag.py      # API endpoints
│   ├── config/
│   │   └── config.py              # Configuration settings
│   ├── services/
│   │   ├── content_storage.py     # Content organization service
│   │   ├── multimodal_rag.py      # Main RAG orchestration
│   │   ├── pdf_processor.py       # PDF extraction service
│   │   └── vector_store.py        # Vector database service
│   └── main.py                    # FastAPI application
├── storage/                       # Generated content storage
│   ├── content/                   # Organized PDF content
│   ├── uploads/                   # Uploaded PDF files
│   └── vector_db/                 # Chroma vector database
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── start_server.py               # Server startup script
├── CHANGELOG.md                  # Detailed change log
└── README.md                     # This file
```

## 🛠 Installation & Setup

### 1. Clone and Navigate
```bash
cd /home/srihasrc/Music/mmrag/backend
```

### 2. Create Virtual Environment (if not already created)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

Required API keys in `.env`:
```env
COHERE_API_KEY=your_cohere_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Start the Server
```bash
# Using the startup script (recommended)
python start_server.py

# Or directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 API Documentation

Once the server is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 Key Endpoints

### PDF Processing
- `POST /api/v1/rag/upload` - Upload and process PDF
- `GET /api/v1/rag/status/{pdf_id}` - Check processing status
- `GET /api/v1/rag/pdfs` - List all processed PDFs

### RAG Queries
- `POST /api/v1/rag/query` - Query the RAG system
- `POST /api/v1/rag/vector-store/search` - Direct vector search

### Content Management
- `GET /api/v1/rag/content/{pdf_id}` - Get saved content
- `DELETE /api/v1/rag/pdf/{pdf_id}` - Delete PDF data

### System Health
- `GET /health` - Basic health check
- `GET /api/v1/rag/health` - Comprehensive RAG health check
- `GET /api/v1/rag/vector-store/stats` - Vector database statistics

## 💡 Usage Examples

### 1. Upload and Process PDF
```bash
curl -X POST "http://localhost:8000/api/v1/rag/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf" \
  -F "save_content=true"
```

### 2. Query the RAG System
```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main contribution of this paper?",
    "pdf_id": "your_pdf_id",
    "top_k": 5
  }'
```

### 3. Check System Health
```bash
curl -X GET "http://localhost:8000/api/v1/rag/health"
```

## 📂 Content Organization

The system organizes extracted content as follows:

```
storage/content/{pdf_id}/
├── texts/              # Individual text chunks (.txt)
├── tables/             # Table HTML files (.html)
├── images/             # Images (.jpg) and base64 (.b64)
├── summaries/          # AI-generated summaries (.json)
└── metadata/           # Processing metadata (.json)
```

## 🔧 Configuration

### Environment Variables
- `COHERE_API_KEY`: Required for embeddings
- `GOOGLE_API_KEY`: Required for image summarization and QA with Gemini 2.5 Flash
- `GROQ_API_KEY`: Required for text/table summarization
- `LANGCHAIN_API_KEY`: Optional for tracing
- `STORAGE_PATH`: Base storage directory (default: ./storage)

### Model Configuration
- **Text/Table Summarization**: Groq Llama-3.1-8b-instant
- **Image Summarization**: Google Gemini 2.5 Flash
- **Question Answering**: Google Gemini 2.5 Flash
- **Embeddings**: Cohere embeddings
- **Vector Database**: Chroma

## 🚨 Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   # Check your .env file
   cat .env
   # Ensure all required keys are set
   ```

2. **Import Errors**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

3. **Storage Permissions**
   ```bash
   # Ensure write permissions
   chmod -R 755 storage/
   ```

4. **Vector Database Issues**
   ```bash
   # Clear vector database
   rm -rf storage/vector_db/
   # Restart server to recreate
   ```

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# RAG system health
curl http://localhost:8000/api/v1/rag/health

# Vector store statistics
curl http://localhost:8000/api/v1/rag/vector-store/stats
```

## 🔄 Workflow

1. **Upload PDF** → System extracts text, tables, images
2. **Generate Summaries** → AI creates concise summaries for each content type
3. **Create Embeddings** → Cohere generates vector embeddings
4. **Store Content** → Organized storage in folders + vector database
5. **Query System** → Natural language questions retrieve relevant content
6. **Generate Answers** → AI synthesizes responses from retrieved context

## 🎯 Performance Notes

- **Concurrent Processing**: Supports multiple PDF uploads
- **Batch Summarization**: Efficient batch processing for content
- **Vector Search**: Fast similarity search with filtering
- **Storage Optimization**: Organized file structure for easy access

## 🔐 Security Considerations

- API keys stored in environment variables
- CORS configured (update for production)
- File upload validation (PDF only)
- Error handling with appropriate HTTP status codes

## 📊 Monitoring

The system provides comprehensive monitoring through:
- Health check endpoints
- Vector database statistics
- Processing status tracking
- Detailed logging

## 🤝 Contributing

1. Follow the existing code structure
2. Add appropriate error handling
3. Update documentation for new features
4. Test endpoints thoroughly

## 📄 License

This project is part of the Multimodal RAG system implementation.

---

For detailed implementation changes, see [CHANGELOG.md](CHANGELOG.md).
