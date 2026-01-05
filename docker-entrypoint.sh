#!/bin/bash
set -ex

case "$1" in
prod)
    python manage.py collectstatic --noinput
    python manage.py migrate --no-input

    exec gunicorn \
        --bind=0.0.0.0:9000 \
        --forwarded-allow-ips='*' \
        --max-requests=1000 \
        --max-requests-jitter=60 \
        --name=floret \
        --threads=1 \
        --timeout=30 \
        --workers=4 \
        floret.wsgi
    exit 0
    ;;
local)
    python manage.py migrate --no-input
    python manage.py load_fixtures
    exec python manage.py runserver 0.0.0.0:9000
    exit 0
    ;;
migrate)
    python manage.py migrate --no-input
    exit 0
    ;;
fixtures)
    echo "no fixtures"
    exit 0
    ;;
test)
    pytest . --cov=. --cov-report=html --cov-report=xml
    exit 0
    ;;
worker)
    python manage.py migrate --no-input
    python manage.py setup_schedules
    exec python manage.py qcluster
    exit 0
    ;;
esac

exec "$@"
