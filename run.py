import os
import subprocess
import sys
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))

BACKEND = os.path.join(ROOT, "backend")

print("=" * 50)
print("      CRIPTONIX RESTAURANT ERP")
print("=" * 50)

print("Iniciando Backend...")

backend = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload"
    ],
    cwd=BACKEND
)

print("Esperando servidor...")

time.sleep(3)

print("Abriendo navegador...")

webbrowser.open("http://127.0.0.1:8000")

backend.wait()