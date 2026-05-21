#!/bin/bash
# Démarrage backend Simplif'IA France
# Double-clique sur ce fichier — Terminal s'ouvre automatiquement.

cd "$(dirname "$0")"

clear
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════╗
║         🇫🇷  Simplif'IA France — Backend Launcher           ║
╚══════════════════════════════════════════════════════════════╝
BANNER
echo ""

# === 1) Docker présent ? ===
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker n'est pas installé sur ce Mac."
  echo ""
  echo "   👉 Télécharge Docker Desktop :"
  echo "      https://www.docker.com/products/docker-desktop"
  echo ""
  echo "Appuie sur Entrée pour fermer…"
  read
  exit 1
fi
echo "✅ Docker installé"

# === 2) Docker démarré ? ===
if ! docker info >/dev/null 2>&1; then
  echo ""
  echo "⚠️  Docker Desktop n'est PAS démarré."
  echo "   Je tente de le lancer pour toi…"
  open -a Docker
  echo "   Attente du démarrage (peut prendre 30s)…"
  for i in $(seq 1 60); do
    if docker info >/dev/null 2>&1; then
      echo "✅ Docker Desktop est prêt !"
      break
    fi
    sleep 1
    printf "."
  done
  echo ""
  if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker n'a pas démarré. Lance-le manuellement (icône baleine 🐳) puis relance ce fichier."
    echo "Appuie sur Entrée pour fermer…"
    read
    exit 1
  fi
fi
echo "✅ Docker tourne"
echo ""

# === 3) .env présent ? ===
if [ ! -f .env ]; then
  echo "⚠️  Fichier .env manquant à la racine du projet."
  echo "   Création depuis .env.example…"
  cp .env.example .env 2>/dev/null || echo "   ⚠️  .env.example introuvable non plus"
fi
echo "✅ Configuration .env OK"
echo ""

# === 4) Stop éventuel conteneur cassé ===
echo "🧹 Nettoyage d'éventuels conteneurs en erreur…"
docker compose stop backend 2>/dev/null || true
echo ""

# === 5) Build + Up ===
echo "🔨 Rebuild + démarrage de TOUS les services…"
echo "   (Première fois : ~2-3 min · ensuite ~30s)"
echo ""
docker compose up -d --build

echo ""
echo "⏳ Attente que le backend réponde…"
HEALTHY=0
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    HEALTHY=1
    break
  fi
  printf "."
  sleep 2
done
echo ""

if [ $HEALTHY -eq 1 ]; then
  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║                  ✅  BACKEND PRÊT  ✅                       ║"
  echo "╠══════════════════════════════════════════════════════════════╣"
  echo "║                                                              ║"
  echo "║  👉  Back-office  : http://localhost:8080/admin.html         ║"
  echo "║  👉  App          : http://localhost:8080/app.html           ║"
  echo "║  👉  Landing      : http://localhost:8080/index.html         ║"
  echo "║  👉  API          : http://localhost:8000                    ║"
  echo "║                                                              ║"
  echo "║  Pour le panneau Clés API :                                  ║"
  echo "║    Back-office → Système → 🔑 Clés API                       ║"
  echo "║                                                              ║"
  echo "║  N'oublie pas Cmd+Shift+R pour rafraîchir sans cache         ║"
  echo "║                                                              ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo ""
  # Ouvre automatiquement le back-office
  sleep 2
  open "http://localhost:8080/admin.html"
else
  echo ""
  echo "⚠️  Le backend ne répond pas. Logs des 25 dernières lignes :"
  echo ""
  docker compose logs backend --tail=25
  echo ""
  echo "État des conteneurs :"
  docker compose ps
fi

echo ""
echo "Appuie sur Entrée pour fermer cette fenêtre…"
read
