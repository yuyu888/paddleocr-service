#!/bin/bash

echo "========================================="
echo "PaddleOCR Service Starting..."
echo "========================================="

export PYTHONUNBUFFERED=1

exec uvicorn app.main:app --host 0.0.0.0 --port 8088 --workers 1
