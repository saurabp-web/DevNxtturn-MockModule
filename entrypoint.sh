#!/bin/bash
set -e

# 1. Check if we are running LOCALLY
if [ "$IS_LOCAL" = "True" ]; then
    echo "--- LOCAL DEV: GENERATING SSL CERTIFICATES ---"
    # Use OpenSSL to create the files (This doesn't use any ports, so no crash!)
    openssl req -x509 -newkey rsa:4096 -keyout cert.key -out cert.crt -days 365 -nodes \
        -subj "/C=US/ST=Dev/L=Dev/O=NxtTurn/OU=Dev/CN=*.nip.io"
    
    echo "--- STARTING DAPHNE WITH SSL ON PORT 8000 ---"
    # We use the --endpoint flag. This tells Daphne to ONLY use SSL on 8000.
    exec daphne -e ssl:8000:privateKey=cert.key:certKey=cert.crt config.asgi:application
else
    echo "--- STARTING IN CLOUD MODE ---"

    echo "Running Database Migrations..."
    python manage.py migrate --noinput
    # Cloud Run provides the port via $PORT. We use plain HTTP here.
    exec daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application
fi