#!/bin/bash

set -e

echo "Performing database migrations..."
alembic upgrade head

echo "Starting API..."
# --limit-max-requests 1000    Restart worker every 1k requests (prevents crashes due to memory leaks)
# --workers 2                  Multiple workers so that one is always online if the other one is restarting
uvicorn \
  --host 0.0.0.0 \
  --port 80 \
  --limit-max-requests 1000 \
  --workers 2 \
  main:api
