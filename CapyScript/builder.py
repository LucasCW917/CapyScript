import subprocess
import sys
import os
from pathlib import Path

PROJECT_NAME = "CapyCompiler"
ENTRY_FILE = "CapyCompiler.py"

def main():
    root = Path(__file__).parent.resolve()
    entry_path = root / ENTRY_FILE

    if not entry_path.exists():
        print(f"[ERROR] {ENTRY_FILE} not found in {root}")
        sys.exit(1)

    print("[INFO] Building executable...")
    print(f"[INFO] Entry: {entry_path}")

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",                 # single exe
        "--clean",                   # wipe temp cache
        "--name", PROJECT_NAME,      # exe name
        "--console",                 # keep console (compiler!)
        str(entry_path)
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n[SUCCESS] Build completed.")
        print(f"[OUTPUT] dist/{PROJECT_NAME}.exe")

    except subprocess.CalledProcessError as e:
        print("\n[FAILURE] Build failed.")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()

