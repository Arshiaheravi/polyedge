#!/bin/bash
set -e

echo "Starting PolyEdge..."

# FastAPI serves both the API and the single-page frontend (mounted at "/"),
# so a single server is all that's needed.
cd backend
echo ""
echo "PolyEdge is running!"
echo "  App:      http://localhost:8003"
echo "  API docs: http://localhost:8003/docs"
echo ""
echo "Press Ctrl+C to stop."

exec uvicorn app.main:app --reload --port 8003
