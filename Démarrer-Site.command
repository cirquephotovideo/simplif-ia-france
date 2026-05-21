#!/bin/bash
# ==================================================================
# Simplif'IA France · Lanceur local · double-clic pour démarrer
# ==================================================================

cd "$(dirname "$0")"

# Couleurs terminal
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

clear
echo ""
echo -e "${BLUE}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}${BOLD}║   🇫🇷  SIMPLIF'IA FRANCE · Lanceur local                    ║${NC}"
echo -e "${BLUE}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Docker installé ?
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé.${NC}"
    echo "   Installe Docker Desktop : https://docker.com/products/docker-desktop"
    read -p "Appuie sur Entrée pour fermer…"
    exit 1
fi

# 2. Docker daemon lancé ?
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Desktop n'est pas lancé. Je le démarre…${NC}"
    open -a Docker
    echo "   Patiente ~30 secondes que Docker démarre…"
    for i in {1..30}; do
        if docker info &> /dev/null; then
            echo -e "${GREEN}   ✓ Docker prêt après ${i}s${NC}"
            break
        fi
        sleep 1
    done
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker n'a pas démarré après 30s. Lance-le manuellement.${NC}"
        read -p "Appuie sur Entrée pour fermer…"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Docker actif${NC}"

# 3. .env présent ?
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Fichier .env manquant. Je copie .env.example…${NC}"
    cp .env.example .env
    echo -e "${YELLOW}   → Édite .env pour ajouter ta clé GEMINI_API_KEY${NC}"
fi

# 4. GEMINI_API_KEY remplie ?
if grep -qE "^GEMINI_API_KEY=$" .env || grep -qE "^GEMINI_API_KEY=$" .env; then
    echo ""
    echo -e "${YELLOW}🔑  Ta clé GEMINI_API_KEY est vide dans .env${NC}"
    echo "    Sans cette clé, les fonctions IA tourneront en mode démo."
    echo ""
    read -p "   Veux-tu la coller maintenant ? (o/n) : " choix
    if [[ $choix =~ ^[oOyY]$ ]]; then
        read -p "   Colle ta clé Gemini (commence par 'AIza…') : " gkey
        if [ -n "$gkey" ]; then
            # Mac sed avec backup
            sed -i.bak "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$gkey|" .env
            rm -f .env.bak
            echo -e "${GREEN}   ✓ Clé Gemini enregistrée dans .env${NC}"
        fi
    fi
fi

echo ""
echo -e "${BLUE}🚀 Démarrage de la stack Docker…${NC}"
echo "   (build + postgres + redis + backend FastAPI + frontend nginx)"
echo ""

# 5. Lance Docker compose
docker compose up -d --build

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Erreur au démarrage. Vérifie les logs : docker compose logs${NC}"
    read -p "Appuie sur Entrée pour fermer…"
    exit 1
fi

# 6. Attend que tout soit prêt
echo ""
echo -e "${BLUE}⏳ Vérification de la santé des services…${NC}"
sleep 6

# 7. Récap
echo ""
echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   ✅  SIMPLIF'IA EST EN LIGNE                               ║${NC}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐 Site             ${BOLD}http://localhost:8080${NC}"
echo -e "  📱 App utilisateur  ${BOLD}http://localhost:8080/app.html${NC}"
echo -e "  🛠  Back-office      ${BOLD}http://localhost:8080/admin.html${NC}"
echo -e "  🔌 API REST         ${BOLD}http://localhost:8080/api${NC}"
echo -e "  📚 Docs Swagger     ${BOLD}http://localhost:8080/docs${NC}"
echo -e "  🧠 Statut IA        ${BOLD}http://localhost:8080/api/ai/health${NC}"
echo ""
echo -e "${BLUE}Commandes utiles :${NC}"
echo "    make logs       (suivre les logs en direct)"
echo "    make down       (arrêter)"
echo "    make rebuild    (reconstruire sans cache)"
echo ""

# 8. Ouvre le navigateur
echo -e "${BLUE}🌐 Ouverture du navigateur…${NC}"
open http://localhost:8080

echo ""
read -p "Appuie sur Entrée pour fermer ce terminal…"
