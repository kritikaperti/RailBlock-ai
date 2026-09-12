#!/usr/bin/env bash
# =========================================================================
# RailBlock AI - Linux/Unix Automated Production Deployment Script
# =========================================================================

set -e

echo "========================================================================="
echo "  [IR] RailBlock AI - Production Deployment & Launch Script"
echo "========================================================================="

echo "[1/3] Creating virtual environment if not present..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "[2/3] Installing production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/3] Launching RailBlock AI with Uvicorn (Workers: 2)..."
export PORT=${PORT:-8000}
uvicorn backend.main:app --host 0.0.0.0 --port "$PORT" --workers 2
