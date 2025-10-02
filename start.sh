#!/bin/bash
# Startup script for PersonaMap on Cloud Run

echo "Starting PersonaMap with gunicorn..."
echo "PORT: ${PORT:-8080}"
echo "FLASK_ENV: ${FLASK_ENV}"

# Run gunicorn
exec gunicorn --bind "0.0.0.0:${PORT:-8080}" --workers 2 --timeout 120 --access-logfile - --error-logfile - run:app