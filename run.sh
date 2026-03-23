#!/bin/bash
set -e

echo "Starting PolyEdge..."

# Start backend in background
echo "Starting backend on :8001..."
cd backend
uvicorn app.main:app --reload --port 8001 &
BACKEND_PID=$!
cd ..

# Start frontend static server
echo "Starting frontend on :3000..."
python3 -m http.server 3000 --directory frontend &
FRONTEND_PID=$!

echo ""
echo "PolyEdge is running!"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8001"
echo "  API docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
