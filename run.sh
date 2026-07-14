#!/bin/bash

set -e

# Start the backend in the background
source .venv/bin/activate

.venv/bin/uvicorn backend.app.main:app --reload &
BACKEND_PID=$!

# Make sure the backend gets killed when this script exits,
# whether that's Ctrl+C, an error, or normal exit.
trap "kill $BACKEND_PID" EXIT

# Start the frontend in the foreground — this is what keeps
# the script alive and shows you its logs directly in this terminal
cd frontend
npm run dev