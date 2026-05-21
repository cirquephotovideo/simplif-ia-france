#!/usr/bin/env bash
# Déploiement Coolify · usage : ./deploy-coolify.sh <APP_UUID>
# Le token doit être dans la variable d'env COOLIFY_TOKEN
set -euo pipefail

if [ -z "${COOLIFY_TOKEN:-}" ]; then
  echo "❌ COOLIFY_TOKEN non défini. export COOLIFY_TOKEN=xxx"
  exit 1
fi

COOLIFY_URL="${COOLIFY_URL:-http://51.75.31.123:8000}"
APP_UUID="${1:-${COOLIFY_APP_UUID:-}}"

if [ -z "$APP_UUID" ]; then
  echo "❌ Usage : ./deploy-coolify.sh <APP_UUID>"
  exit 1
fi

echo "🚀 Déclenchement du déploiement Coolify pour app $APP_UUID..."
HTTP_CODE=$(curl -s -o /tmp/coolify-resp.json -w "%{http_code}" \
  -X POST \
  -H "Authorization: Bearer $COOLIFY_TOKEN" \
  "$COOLIFY_URL/api/v1/deploy?uuid=$APP_UUID")

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  echo "✅ Déploiement déclenché ($HTTP_CODE)"
  cat /tmp/coolify-resp.json
else
  echo "❌ Erreur ($HTTP_CODE)"
  cat /tmp/coolify-resp.json
  exit 2
fi
