#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT=1229
HOST=0.0.0.0

echo "啟動 Django 開發伺服器 http://${HOST}:${PORT}/ （外網可連）"
exec python3 manage.py runserver "${HOST}:${PORT}"
