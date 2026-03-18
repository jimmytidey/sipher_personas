#!/bin/bash
# Azure App Service startup script
set -e

pip install --quiet -r requirements.txt

gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.main:app \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 120 \
  --access-logfile -
