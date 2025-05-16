# main.py

import subprocess
import sys
import os
import threading
import time

def run_backend():
    print("🚀 Starting FastAPI backend on http://127.0.0.1:9999")
    subprocess.run([sys.executable, "backend.py"])

def run_frontend():
    print("🌐 Starting Streamlit frontend on http://localhost:8501")
    os.system("streamlit run frontend.py")

if __name__ == "__main__":
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.start()

    time.sleep(3)  # Optional: Give the backend a head start

    run_frontend()
