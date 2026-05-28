#!/bin/bash

set -e

cleanup() {
  echo "Stopping everything"
  trap - SIGINT SIGTERM EXIT
  pkill -P $$ 2>/dev/null || true

  exit 0
}

trap cleanup SIGINT SIGTERM

docker compose up -d

until nc -z localhost 5672; do sleep 2; done
until nc -z localhost 6379; do sleep 2; done

lsof -ti :5000 | xargs kill -9 2>/dev/null || true

source .venv/bin/activate

python3 run.py

until nc -z localhost 5000; do sleep 1; done

while true; do
  PYTHONWARNINGS="ignore" PYTHONPATH=. python3 -m src.workers.summarize_worker
  sleep 2
done &

wait