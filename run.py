"""
run.py
Single-command launcher for OCEANTRACE.
Starts the FastAPI server on port 8000 and automatically opens the browser.
Usage:
    python run.py
"""

import sys
import os
import webbrowser
import time
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  OCEANTRACE: Marine Oil Spill Detection & Attribution System")
    print("=" * 65)
    print("  - Launching FastAPI Backend & Leaflet Tactical Dashboard...")
    print("  - Local URL: http://127.0.0.1:8000")
    print("  - Swagger API Docs: http://127.0.0.1:8000/docs")
    print("=" * 65 + "\n")

    # Give uvicorn a moment to bind then open browser
    def open_dashboard():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000")

    import threading
    threading.Thread(target=open_dashboard, daemon=True).start()

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
