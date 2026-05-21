#!/usr/bin/env bash
# Démarrage du backend Simplif'IA France (avec rebuild)
# Usage : bash start_backend.sh
set -e

cd "$(dirname "$0")"

echo "🐳 Vérification de Docker…"
if ! command -v docker &> /dev/null; then
  echo "❌ Docker n'est pas installé. Installe Docker Desktop : https://docker.com/products/docker-desktop"
  exit 1
fi

if ! docker info &> /dev/null; then
  echo "⚠️  Docker n'est pas démarré. Lance Docker Desktop puis relance ce script."
  exit 1
fi

echo "📦 État actuel des conteneurs :"
docker compose ps

echo ""
echo "🔨 Rebuild et démarrage du backend + frontend + db + redis…"
docker compose up -d --build backend frontend db redis

echo ""
echo "⏳ Attente que le backend soit healthy (max 60s)…"
for i in {1..30}; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend joignable sur http://localhost:8000"
    break
  fi
  echo "   …attente ($i/30)"
  sleep 2
done

echo ""
echo "📊 État final :"
docker compose ps

echo ""
echo "📜 Dernières lignes des logs backend (au cas où) :"
docker compose logs backend --tail=15

echo ""
echo "✅ Terminé ! Recharge le back-office :"
echo "   http://localhost:8080/admin.html"
echo "   → Sidebar Système → 🔑 Clés API"
echo ""
echo "💡 Pour suivre les logs en direct :"
echo "   docker compose logs -f backend"
