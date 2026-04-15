#!/bin/bash
set -e

# 1. Check if we are running LOCALLY
if [ "$IS_LOCAL" = "True" ]; then
    echo "--- STARTING IN LOCAL DEV MODE ---"
    # Generate fresh SSL certs for the current IP
    python manage.py runserver_plus 0.0.0.0:8000 --cert-file cert.crt --key-file cert.key &
    sleep 5
    exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
else
    echo "--- STARTING IN CLOUD MODE ---"
    # Use the $PORT variable provided by Google Cloud Run
    exec daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application
fi