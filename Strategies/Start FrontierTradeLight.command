#!/bin/bash
# Double-click launcher for the FrontierTradeLight app (FastAPI backend +
# React frontend). Opens Terminal automatically when double-clicked from
# Finder. Starts both servers, waits for the frontend to come up, opens it
# in your browser, and stops both servers together when this window is
# closed or Ctrl+C is pressed.

set -e

# Resolve this script's own directory, following symlinks, so it works
# regardless of where it's double-clicked from or copied to (e.g. the Dock
# or Desktop) - $0 alone breaks under those.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

BACKEND_PORT=8000
FRONTEND_PORT=5173
VENV_PYTHON="Default/.venv/bin/python"
VENV_UVICORN="Default/.venv/bin/uvicorn"

echo "FrontierTradeLight"
echo "=================="
echo "Working directory: $SCRIPT_DIR"
echo

if [ ! -x "$VENV_UVICORN" ]; then
  echo "Error: $VENV_UVICORN not found or not executable."
  echo "Set up the backend first:"
  echo "  cd Default && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  read -n 1 -s -r -p "Press any key to close..."
  exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "frontend/node_modules not found - running npm install..."
  (cd frontend && npm install)
fi
if [ ! -d "node_modules" ]; then
  echo "node_modules not found - running npm install..."
  npm install
fi

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo
  echo "Shutting down..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  echo "Stopped. You can close this window."
}
trap cleanup EXIT INT TERM

echo "Starting backend on port $BACKEND_PORT..."
"$VENV_UVICORN" api.main:app --reload --port "$BACKEND_PORT" --app-dir Default &
BACKEND_PID=$!

echo "Starting frontend on port $FRONTEND_PORT..."
# exec replaces this subshell with vite itself, so $! below is vite's own
# PID rather than a wrapper's - `npm run dev` would leave vite running as
# an orphaned grandchild that a plain `kill $FRONTEND_PID` never reaches.
(cd frontend && exec node_modules/.bin/vite --port "$FRONTEND_PORT") &
FRONTEND_PID=$!

echo "Waiting for frontend to come up..."
for _ in $(seq 1 60); do
  if curl -s -o /dev/null "http://localhost:$FRONTEND_PORT"; then
    break
  fi
  sleep 1
done

open "http://localhost:$FRONTEND_PORT" 2>/dev/null

echo
echo "Backend:  http://localhost:$BACKEND_PORT/docs"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo
echo "Close this window or press Ctrl+C to stop both servers."

wait
