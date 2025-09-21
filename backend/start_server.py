#!/usr/bin/env python3
"""
Startup script for the Multimodal RAG FastAPI server.
This script sets up the environment and starts the server.
"""

import os
import sys
import uvicorn
from pathlib import Path

def setup_environment():
    """Setup environment variables and create necessary directories."""
    
    # Create storage directories
    storage_dirs = [
        "./storage",
        "./storage/uploads", 
        "./storage/content",
        "./storage/vector_db"
    ]
    
    for directory in storage_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("Please copy .env.example to .env and fill in your API keys:")
        print("  cp .env.example .env")
        print("\nRequired API keys:")
        print("  - COHERE_API_KEY (for embeddings)")
        print("  - GOOGLE_API_KEY (for image summarization and QA with Gemini 2.5 Flash)")
        print("  - GROQ_API_KEY (for text/table summarization)")
        return False
    
    print("✓ Environment file found")
    return True

def main():
    """Main startup function."""
    print("🚀 Starting Multimodal RAG API Server...")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Please check the requirements above.")
        sys.exit(1)
    
    print("\n📋 Server Information:")
    print("  - API Documentation: http://localhost:8000/docs")
    print("  - Health Check: http://localhost:8000/health")
    print("  - RAG Health: http://localhost:8000/api/v1/rag/health")
    
    print("\n🔧 Key Endpoints:")
    print("  - Upload PDF: POST /api/v1/rag/upload")
    print("  - Query RAG: POST /api/v1/rag/query")
    print("  - List PDFs: GET /api/v1/rag/pdfs")
    
    print("\n" + "=" * 50)
    print("Starting server on http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the server
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
