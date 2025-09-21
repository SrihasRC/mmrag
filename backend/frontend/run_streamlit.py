#!/usr/bin/env python3
"""
Startup script for the Multimodal RAG Streamlit interface.
"""

import subprocess
import sys
import requests
import time
from pathlib import Path

def check_backend_running():
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main startup function."""
    print("🚀 Starting Multimodal RAG Streamlit Interface...")
    print("=" * 60)
    
    # Check if backend is running
    print("🔍 Checking backend status...")
    if not check_backend_running():
        print("❌ Backend is not running!")
        print("\nPlease start the FastAPI backend first:")
        print("  cd ../backend")
        print("  python start_server.py")
        print("\nOr run it directly:")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nThen run this script again.")
        return
    
    print("✅ Backend is running!")
    
    # Start Streamlit
    print("\n📱 Starting Streamlit interface...")
    print("=" * 60)
    print("🌐 Interface will be available at: http://localhost:8501")
    print("📚 Features available:")
    print("  - Upload and process PDFs")
    print("  - Query the RAG system")
    print("  - View extracted content (text, tables, images)")
    print("  - Manage processed PDFs")
    print("  - System statistics and health monitoring")
    print("  - Advanced debugging tools")
    print("\nPress Ctrl+C to stop the interface")
    print("=" * 60)
    
    try:
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit interface stopped by user")
    except Exception as e:
        print(f"\n❌ Error running Streamlit: {e}")

if __name__ == "__main__":
    main()
