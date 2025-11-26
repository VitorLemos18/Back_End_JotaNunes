#!/bin/bash
set -e

# Rodar migrações
python manage.py migrate || true
python manage.py migrate --database=django_internal || true

# Iniciar servidor
exec gunicorn jn_custom.wsgi:application --bind 0.0.0.0:${PORT:-8000}

