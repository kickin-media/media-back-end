#!/bin/bash

set -e

echo "Performing database migrations..."
alembic upgrade head

echo "Starting API..."
# --workers                    Multiple workers so that one is always online if the other one is restarting
#                              Default: 5 (2*CPUs+1 for 2-core VM), override via WEB_CONCURRENCY env var
uvicorn \
  --host 0.0.0.0 \
  --port 80 \
  --workers "${WEB_CONCURRENCY:-5}" \
  main:api
