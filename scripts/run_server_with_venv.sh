#!/bin/bash
# Create a venv in the project, install deps, and run the server. Use this if system pip fails.
set -e
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment at .venv ..."
  python3 -m venv .venv
fi

echo "Activating venv and installing dependencies..."
source .venv/bin/activate

# Install minimal server deps first so the app starts
pip install -q -r requirements-phase4-server.txt 2>/dev/null || pip install -q fastapi "uvicorn[standard]" pydantic

# Install full deps so /chat works (Phase 2 + 3)
if [ -f "requirements.txt" ]; then
  echo "Installing full dependencies (may take a few minutes)..."
  pip install -q -r requirements.txt
fi

echo ""
echo "Starting server at http://127.0.0.1:8000"
echo "Open that URL in your browser. Press Ctrl+C to stop."
echo ""
exec python scripts/run_phase4.py
