#!/bin/bash

set -e

echo "Performing database migrations..."
alembic upgrade head

echo "Starting API..."
uvicorn main:api --host 0.0.0.0 --port 80