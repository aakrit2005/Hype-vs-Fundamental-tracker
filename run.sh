#!/usr/bin/env bash
# Single launcher: data pipeline + backend + frontend.
# Usage:
#   ./run.sh            pipeline (skipped if already ran today) then both servers
#   ./run.sh pipeline   force the data cycle only, then exit
#   ./run.sh servers    skip the data cycle, just serve

set -uo pipefail
cd "$(dirname "$0")"

PY=backend/.venv/bin/python
STAMP="/tmp/hype-tracker-pipeline-$(date +%F).stamp"
BACK_PID=""
FE_PID=""

# ---------- preflight checks ----------

if [ ! -x "$PY" ]; then
  echo "ERROR: backend/.venv not found."
  echo "Create it with: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt"
  exit 1
fi

if [ ! -f backend/.env ]; then
  echo "ERROR: backend/.env is missing. It must contain SERPAPI_KEY and JWT_SECRET."
  exit 1
fi

if ! command -v npm > /dev/null; then
  echo "ERROR: npm not found. Install Node 20+ first."
  exit 1
fi

if [ ! -d frontend/node_modules ]; then
  echo "==> Installing frontend dependencies (first run only)"
  if [ -f frontend/package-lock.json ]; then
    (cd frontend && npm ci)
  else
    (cd frontend && npm install)
  fi
fi

# ---------- data pipeline ----------

run_pipeline() {
  echo "==> [1/3] Refreshing price history"
  "$PY" scripts/backfill_prices.py || { echo "ERROR: backfill_prices failed"; return 1; }

  echo "==> [2/3] Ingesting news, scoring, evaluating alerts"
  "$PY" scripts/daily_update.py || { echo "ERROR: daily_update failed"; return 1; }

  echo "==> [3/3] Measuring the signal (backtest)"
  "$PY" scripts/run_backtest.py || { echo "ERROR: run_backtest failed"; return 1; }

  touch "$STAMP"
  echo "==> Pipeline complete."
}

# ---------- servers ----------

stop_servers() {
  # Each server runs in its own process group, so killing the group
  # also stops child processes like the uvicorn reloader and vite.
  [ -n "$BACK_PID" ] && kill -- -"$BACK_PID" 2>/dev/null
  [ -n "$FE_PID" ] && kill -- -"$FE_PID" 2>/dev/null
  wait 2>/dev/null
}

start_servers() {
  trap 'echo; echo "==> Shutting down..."; stop_servers; exit 0' INT TERM

  echo "==> Starting backend  ->  http://127.0.0.1:8000   (API docs: /docs)"
  setsid "$PY" -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000 &
  BACK_PID=$!

  echo "==> Starting frontend ->  http://localhost:5173"
  setsid npm --prefix frontend run dev &
  FE_PID=$!

  echo
  echo "Both services are up. Press Ctrl+C to stop everything."
  echo

  # Wait until either service exits, then bring the other one down too.
  wait -n
  stop_servers
}

# ---------- entry point ----------

case "${1:-all}" in
  pipeline)
    run_pipeline
    ;;
  servers)
    start_servers
    ;;
  all)
    if [ -f "$STAMP" ]; then
      echo "==> Pipeline already ran today, skipping. (Use './run.sh pipeline' to force it.)"
    else
      run_pipeline || exit 1
    fi
    start_servers
    ;;
  *)
    echo "Usage: ./run.sh [all|pipeline|servers]"
    exit 1
    ;;
esac