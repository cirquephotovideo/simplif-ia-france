#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

GRN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; NC='\033[0m'

clear
echo -e "${YEL}🛑 Arrêt de Simplif'IA France…${NC}\n"

if docker compose ps -q 2>/dev/null | grep -q .; then
  docker compose down
  echo -e "\n${GRN}✅ Tous les conteneurs sont arrêtés.${NC}"
else
  echo -e "${YEL}⚠️  Aucun conteneur en cours.${NC}"
fi

echo ""
echo "Appuyez sur Entrée pour fermer…"
read
