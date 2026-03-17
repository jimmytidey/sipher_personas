#!/bin/bash
# Azure App Service startup script
# Configured in the portal under Settings → Configuration → Startup Command:
#   startup.sh
#
# Azure sets the PORT env var; default to 8000 for local testing.
gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.main:app \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 120 \
  --access-logfile -
