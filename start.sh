#!/bin/bash
# Startup script for PersonaMap on Cloud Run

echo "Starting PersonaMap with gunicorn..."
echo "PORT: ${PORT:-8080}"
echo "FLASK_ENV: ${FLASK_ENV}"

# Ensure instance directory exists and is writable
mkdir -p /app/instance
chmod 755 /app/instance

# Set production environment
export FLASK_ENV=production

# Run gunicorn
exec gunicorn --bind "0.0.0.0:${PORT:-8080}" --workers 2 --timeout 120 --access-logfile - --error-logfile - run:app