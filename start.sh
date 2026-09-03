#!/bin/bash

# Start RAGarator backend and frontend for local preview.
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

cd "$ROOT/frontend"
npm run dev

trap "kill $BACKEND_PID" EXIT
