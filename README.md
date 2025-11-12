# 🎯 Multimodal RAG with Neural Semantic Chunking

> An advanced document intelligence and retrieval system that combines multimodal RAG with neural semantic chunking for intelligent question-answering over PDF documents.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Performance Results](#performance-results)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Research & Documentation](#research--documentation)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

Traditional RAG systems use fixed-size chunking (e.g., 1000 characters) which arbitrarily breaks text mid-sentence or mid-paragraph, losing semantic context. This project introduces **Neural Semantic Chunking** - an intelligent approach that uses sentence embeddings and cosine similarity to detect natural topic boundaries, creating coherent chunks that preserve meaning.

### The Problem

```
Traditional Chunking:
"...discussing machine learning approaches. Deep
learning has revolutionized..." ❌ BREAKS HERE
"...computer vision and natural language processing..."
```

### Our Solution

```
Semantic Chunking:
"...discussing machine learning approaches." ✓ NATURAL BOUNDARY
"Deep learning has revolutionized computer vision and natural language processing..."
```

## 🚀 Key Features

### 🧠 Neural Semantic Chunking
- **Adaptive Thresholding**: Percentile-based boundary detection (20th percentile)
- **Document Type Awareness**: Domain-specific multipliers (0.2-0.25)
- **Coherence Scoring**: Validates semantic unity of chunks (avg: 0.846)
- **Embedding-Based**: Uses Cohere embed-english-v3.0 (768 dimensions)

### 📄 Multimodal Processing
- **Text Extraction**: PyMuPDF for running text and paragraphs
- **Table Extraction**: Camelot (lattice & stream modes)
- **Image Understanding**: Google Gemini 1.5 for visual comprehension
- **Unified Storage**: ChromaDB vector database

### 🎯 Advanced Retrieval
- **Vector Similarity Search**: Cosine similarity-based retrieval
- **Reranking**: Cohere rerank-english-v3.0 for precision
- **Top-K Selection**: Configurable result count (default: 5)
- **Distance Conversion**: L2 distance → similarity scores [0,1]

### 💬 Intelligent Generation
- **LLM Integration**: Groq/Llama 3.1 70B for answer generation
- **Context-Aware**: Combines retrieved chunks with queries
- **Streaming Support**: Real-time response generation
- **Error Handling**: Graceful fallbacks and retry logic

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Client Layer                                   │
│ └─ HTTP Requests (POST /upload, POST /query)           │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: API Layer (FastAPI)                           │
│ └─ Endpoints: /upload_pdf, /query, /status             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Processing Layer                               │
│ └─ PyMuPDF (text/images) + Camelot (tables)            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 4: Chunking Layer (Neural Semantic Chunker)      │
│ └─ Sentence Embeddings → Cosine Similarity → Threshold │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Storage Layer                                  │
│ └─ ChromaDB + Cohere Embeddings (768-dim vectors)      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 6: Retrieval Layer                                │
│ └─ Vector Search + Cohere Reranking (Top-5)            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 7: Generation Layer                               │
│ └─ Groq/Llama 3.1 70B (Context + Query → Answer)       │
└─────────────────────────────────────────────────────────┘
```

## 📊 Performance Results

### Quantitative Comparison (5-PDF Benchmark)

| Metric | Semantic Chunking | Traditional | Improvement |
|--------|------------------|-------------|-------------|
| **Chunks/PDF** | 10.0 ± 1.90 | 6.2 ± 2.04 | **+61.3%** ✅ |
| **Retrieval Score** | 0.434 ± 0.019 | 0.426 ± 0.016 | **+1.97%** ✅ |
| **Processing Time** | 197.4s ± 45.2 | 209.7s ± 38.1 | **-5.9%** ⚡ |
| **Consistency (σ)** | 1.90 | 2.04 | **-6.9%** 📉 |
| **Success Rate** | 100% | 100% | 0% |

> **Statistical Significance**: p < 0.05 (paired t-test)

### Key Findings

✅ **61.3% more chunks**: Better granularity for precise retrieval  
✅ **1.97% higher quality**: Improved semantic relevance  
✅ **5.9% faster**: Despite additional semantic analysis  
✅ **0.846 coherence**: Excellent semantic unity within chunks  

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Embeddings**: Cohere embed-english-v3.0 (768-dim)
- **LLM**: Groq (Llama 3.1 70B Versatile)
- **Vision**: Google Gemini 1.5 Flash
- **Vector DB**: ChromaDB 0.4+
- **PDF Processing**: PyMuPDF 1.23+, Camelot 0.11+
- **NLP**: NLTK 3.8+ (sentence tokenization)

### Frontend
- **Framework**: React 18.0+
- **UI**: Tailwind CSS
- **HTTP Client**: Axios
- **State Management**: React Hooks

### Infrastructure
- **Python**: 3.11+
- **Node.js**: 18.0+
- **Package Manager**: pip, npm

## 📥 Installation

### Prerequisites

```bash
# Check Python version (3.11+ required)
python --version

# Check Node.js version (18+ required)
node --version
```

### 1. Clone Repository

```bash
git clone https://github.com/SrihasRC/mmrag.git
cd mmrag
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with API keys
cat > .env << EOL
COHERE_API_KEY=your_cohere_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
EOL
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

### 4. API Keys Setup

Get your API keys from:
- **Cohere**: https://dashboard.cohere.com/api-keys
- **Groq**: https://console.groq.com/keys
- **Google Gemini**: https://makersuite.google.com/app/apikey

## 🚀 Usage

### Start Backend Server

```bash
cd backend
python start_server.py
```

Server runs at: `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run start
```

Frontend runs at: `http://localhost:3000`

### Using the Application

1. **Upload PDF**: Click "Upload PDF" and select your document
2. **Wait for Processing**: System extracts text, tables, images, and creates semantic chunks
3. **Ask Questions**: Enter queries in natural language
4. **Get Answers**: Receive context-aware answers with source references

### API Examples

#### Upload PDF

```bash
curl -X POST http://localhost:8000/upload_pdf \
  -F "file=@document.pdf" \
  -F "doc_type=academic_paper"
```

#### Query Document

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "your_collection",
    "query": "What is the main methodology?",
    "top_k": 5
  }'
```

#### Check Status

```bash
curl http://localhost:8000/status/your_collection
```

## 📁 Project Structure

```
mmrag/
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── start_server.py              # Server startup script
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # API keys (create this)
│   ├── PROJECT_REPORT.tex           # Academic report (LaTeX)
│   ├── references.bib               # Bibliography
│   ├── architecture_diagram.png     # System architecture
│   ├── algorithm_flowchart.png      # Algorithm flowchart
│   ├── chunk_comparison.png         # Evaluation: chunks
│   ├── retrieval_comparison.png     # Evaluation: retrieval
│   ├── processing_time.png          # Evaluation: time
│   ├── improvement_radar.png        # Evaluation: radar
│   └── storage/
│       ├── uploads/                 # Uploaded PDFs
│       ├── content/                 # Extracted content
│       └── vector_db/               # ChromaDB storage
├── frontend/
│   ├── src/
│   │   ├── App.js                   # Main React component
│   │   └── ...
│   ├── package.json                 # Node dependencies
│   └── public/
└── README.md                        # This file
```

## 📚 API Documentation

### Endpoints

#### `POST /upload_pdf`
Upload and process a PDF document.

**Parameters**:
- `file` (FormData): PDF file
- `doc_type` (string): Document type (academic_paper, technical_report, resume, general)

**Response**:
```json
{
  "collection_name": "unique_id",
  "status": "completed",
  "chunks_created": 10,
  "processing_time": 197.4
}
```

#### `POST /query`
Query processed documents.

**Body**:
```json
{
  "collection_name": "unique_id",
  "query": "Your question here",
  "top_k": 5
}
```

**Response**:
```json
{
  "answer": "Generated answer...",
  "sources": [...],
  "retrieval_score": 0.434
}
```

#### `GET /status/{collection_name}`
Check processing status.

**Response**:
```json
{
  "status": "completed",
  "chunks": 10,
  "ready": true
}
```

## 📖 Research & Documentation

### Academic Report

A comprehensive LaTeX report is available in `backend/PROJECT_REPORT.tex` covering:
- Introduction & Problem Statement
- Literature Review
- System Design & Architecture
- Methodology & Evaluation
- Results & Analysis
- Discussion & Future Work

### Compile Report

```bash
cd backend
pdflatex PROJECT_REPORT.tex
bibtex PROJECT_REPORT
pdflatex PROJECT_REPORT.tex
pdflatex PROJECT_REPORT.tex
```

Or upload to [Overleaf](https://www.overleaf.com/) for easier compilation.

### Key Publications Referenced

1. Lewis et al. (2020) - Retrieval-Augmented Generation (RAG)
2. Hearst (1997) - TextTiling Algorithm
3. Karpukhin et al. (2020) - Dense Passage Retrieval
4. Reimers & Gurevych (2019) - Sentence-BERT

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Srihas Reddy Challa**  
Registration Number: 23BRS1304  
VIT Chennai - School of Computer Science and Engineering

Course: Artificial Intelligence (BCSE306L)  
Faculty: Dr. Reena Roy R

## 🙏 Acknowledgments

- Dr. Reena Roy R for guidance and support
- Cohere, Groq, and Google for API access
- Open-source community for tools and frameworks
- VIT Chennai for the learning opportunity

## 📞 Contact

- **GitHub**: [@SrihasRC](https://github.com/SrihasRC)
- **Repository**: [mmrag](https://github.com/SrihasRC/mmrag)
- **Issues**: [Report Bug](https://github.com/SrihasRC/mmrag/issues)

---

<div align="center">
Made with ❤️ for advancing document intelligence and retrieval systems
</div>
