#!/bin/bash
# Restart and run Phase 4 (backend + frontend). Uses .venv and installs full requirements so chat works.
set -e
cd "$(dirname "$0")/.."

echo "Stopping any existing server on port 8000..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
sleep 1

if [ ! -d ".venv" ]; then
  echo "Creating .venv..."
  python3 -m venv .venv
fi
echo "Installing dependencies (numpy<2, groq, chromadb, etc.)..."
.venv/bin/pip install "numpy<2" -q 2>/dev/null || true
.venv/bin/pip install -r requirements.txt -q

echo ""
echo "Starting at http://127.0.0.1:8000 — Press Ctrl+C to stop."
echo ""
exec .venv/bin/python scripts/run_phase4.py
