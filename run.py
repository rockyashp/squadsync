"""
SquadSync - Unified Local Development Server Runner
Starts both the FastAPI Backend and the Frontend Server (Vite React Architecture).
"""

import sys
import shutil
import socket
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend-react"

def get_python_executable():
    """Returns the virtualenv Python if present, otherwise system Python."""
    venv_python_win = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    venv_python_posix = BACKEND_DIR / ".venv" / "bin" / "python"
    
    if venv_python_win.exists():
        return str(venv_python_win)
    elif venv_python_posix.exists():
        return str(venv_python_posix)
    return sys.executable

def print_banner(frontend_type, frontend_port):
    banner = f"""
====================================================================
               SQUAD SYNC - LOCAL DEVELOPMENT SERVERS
====================================================================
 [Frontend Web App]  : http://localhost:{frontend_port} ({frontend_type})
 [Backend API Root]  : http://127.0.0.1:8000
 [Interactive Docs]  : http://127.0.0.1:8000/docs
 [Health Endpoint]   : http://127.0.0.1:8000/health
 [WebSocket Chat]    : ws://127.0.0.1:8000/api/v1/chat/ws

 Press Ctrl+C at any time to gracefully terminate all services.
====================================================================
"""
    print(banner)

def main():
    py_exec = get_python_executable()
    print(f"[*] Using Python: {py_exec}")
    print(f"[*] Project Root: {ROOT_DIR}")

    # Ensure backend directory exists
    if not BACKEND_DIR.exists():
        print(f"[!] Error: Backend directory '{BACKEND_DIR}' not found!")
        sys.exit(1)

    processes = []

    # Check if backend port 8000 is already occupied
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', 8000)) == 0:
            print("[!] Warning: Port 8000 is already in use. A backend instance may already be running.")
            print("[!] If another instance is running, please close it first or check your task manager.")
            sys.exit(1)

    try:
        # 1. Start Backend FastAPI Server via Uvicorn
        print("[*] Launching Backend Server on port 8000...")
        backend_cmd = [
            py_exec,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
        ]
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(BACKEND_DIR),
        )
        processes.append(("Backend", backend_proc))

        # 2. Launch React + Vite Frontend
        npm_bin = shutil.which("npm.cmd") if sys.platform == "win32" else shutil.which("npm")

        if not npm_bin:
            print("[!] Warning: npm not found on PATH. Frontend will not start.")
            frontend_type = "None"
            frontend_port = 0
        elif not FRONTEND_DIR.exists():
            print(f"[!] Warning: Frontend directory '{FRONTEND_DIR}' not found.")
            frontend_type = "None"
            frontend_port = 0
        else:
            print("[*] Launching React + Vite Development Server...")
            frontend_proc = subprocess.Popen(
                [npm_bin, "run", "dev"],
                cwd=str(FRONTEND_DIR),
            )
            frontend_type = "React Vite HMR"
            frontend_port = 5173
            processes.append(("React Frontend", frontend_proc))

        # Wait a moment for servers to bind
        time.sleep(2.0)
        print_banner(frontend_type, frontend_port)

        # Monitor processes
        while True:
            for name, proc in processes:
                poll = proc.poll()
                if poll is not None:
                    print(f"[!] {name} server terminated unexpectedly with code {poll}.")
                    return
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[*] Stopping all services...")
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                print(f"[*] Terminating {name} server...")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("[OK] All services stopped.")

if __name__ == "__main__":
    main()
