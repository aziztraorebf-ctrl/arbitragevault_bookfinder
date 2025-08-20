#!/usr/bin/env python3
"""
Development runner script for ArbitrageVault FastAPI
Usage: python run_dev.py
"""

import uvicorn
import os
from pathlib import Path

# Set environment for development
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./arbitragevault_dev.db")

if __name__ == "__main__":
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Starting ArbitrageVault BookFinder API (Development Mode)")
    print("📚 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("🏥 Health: http://localhost:8000/api/v1/health/")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
