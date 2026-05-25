import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
import time


def _stream_output(name, stream):
    for line in iter(stream.readline, ""):
        print(f"[{name}] {line.rstrip()}")
    stream.close()


def run_process(name, cmd, cwd=None, env=None):
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True,
    )
    t = threading.Thread(target=_stream_output, args=(name, p.stdout), daemon=True)
    t.start()
    return p


def main(open_browser: bool = False, install_deps: bool = False):
    root = os.path.dirname(__file__)

    # Backend: run the existing backend/main.py (it runs uvicorn when executed)
    backend_py = sys.executable or "python"
    backend_cmd = f'{shlex_quote(backend_py)} backend/main.py'

    # Frontend: admin (root) and patient-portal (Vite)
    admin_path = root
    patient_path = os.path.join(root, "frontend", "patient-portal")
    admin_cmd = "npm run dev -- --port 5173"
    patient_cmd = "npm run dev -- --port 5174"

    # Optionally install deps
    if install_deps:
        if shutil.which("pip"):
            print("Installing Python deps for backend...")
            subprocess.run(f"{shlex_quote(backend_py)} -m pip install -r backend/requirements.txt", shell=True, check=False)
        if shutil.which("npm"):
            print("Installing Node deps for frontends...")
            # Install in both admin (root) and patient portal if present
            for path in (admin_path, patient_path):
                if os.path.isdir(path):
                    print(f"  npm ci in {path}")
                    subprocess.run("npm ci", cwd=path, shell=True, check=False)

    procs = []
    try:
        print("Starting backend...")
        p_backend = run_process("backend", backend_cmd, cwd=root)
        procs.append(p_backend)

        # small delay so backend starts earlier
        time.sleep(1.0)

        # Start admin frontend at 5173 (if package.json present and npm available)
        if os.path.isdir(admin_path) and shutil.which("npm"):
            print("Starting admin frontend on port 5173...")
            p_admin = run_process("admin-frontend", admin_cmd, cwd=admin_path)
            procs.append(p_admin)
        else:
            print("Skipping admin frontend start (missing folder or npm). Path:", admin_path)

        # Start patient portal frontend at 5174
        if os.path.isdir(patient_path) and shutil.which("npm"):
            print("Starting patient frontend on port 5174...")
            p_patient = run_process("patient-frontend", patient_cmd, cwd=patient_path)
            procs.append(p_patient)
        else:
            print("Skipping patient frontend start (missing folder or npm). Path:", patient_path)

        if open_browser:
            try:
                import webbrowser

                webbrowser.open("http://127.0.0.1:8000/docs")
            except Exception:
                pass

        # Wait until processes exit or are interrupted
        while True:
            alive = [p.poll() is None for p in procs]
            if not any(alive):
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Interrupted — stopping child processes...")
    finally:
        for p in procs:
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        # give processes a moment to exit
        time.sleep(1)
        for p in procs:
            if p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass


def shlex_quote(s: str) -> str:
    # Minimal quoting helper for Windows/Unix compatibility
    if sys.platform == "win32":
        # wrap in double quotes if it contains spaces
        return f'"{s}"' if " " in s else s
    import shlex

    return shlex.quote(s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the full MedAI project (backend + frontend).")
    parser.add_argument("--open", action="store_true", help="Open backend docs in the browser")
    parser.add_argument("--install", action="store_true", help="Install Python/Node deps before starting (may take a while)")
    args = parser.parse_args()
    main(open_browser=args.open, install_deps=args.install)
