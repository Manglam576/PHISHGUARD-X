import subprocess
import sys
import time

def main():
    print("Starting PHISHGUARD-X...")

    # Start FastAPI backend
    print("Starting integration backend on port 8000...")
    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "integration.api:app", "--host", "0.0.0.0", "--port", "8000"
    ])

    time.sleep(2)  # Give backend time to start

    # Start Streamlit frontend
    print("Starting Streamlit frontend...")
    frontend = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "Threat-graph-main/dashboard.py", "--server.port", "8501"
    ])

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nShutting down PHISHGUARD-X...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
