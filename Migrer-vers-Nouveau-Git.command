#!/usr/bin/env bash
# ============================================================
# MIGRATION · Pousser le code vers le nouveau repo GitHub
# cirquephotovideo/simplif-ia-france (privé, créé via Claude)
# ============================================================
set -e

cd "$(dirname "$0")"

GRN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; BLU='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

NEW_REPO="https://github.com/cirquephotovideo/simplif-ia-france.git"
NEW_REPO_SSH="git@github.com:cirquephotovideo/simplif-ia-france.git"

clear
echo ""
echo -e "${BLU}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLU}${BOLD}║   🚚  Migration vers le nouveau repo GitHub                ║${NC}"
echo -e "${BLU}${BOLD}║   cirquephotovideo/simplif-ia-france                       ║${NC}"
echo -e "${BLU}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Reset git (l'ancien historique pixeeplay reste sur l'ancien repo)
echo -e "${YEL}[1/5]${NC} Réinitialisation Git locale (pour repartir propre)…"
if [ -d .git ]; then
  rm -rf .git
fi
git init -b main > /dev/null
echo -e "${GRN}✅ Repo Git ré-initialisé${NC}"
echo ""

# 2. Add + commit tout le code actuel
echo -e "${YEL}[2/5]${NC} Ajout des fichiers et commit initial…"
git add .
git -c user.email="arnaud@gredai.com" -c user.name="Arnaud Durand" \
  commit -m "feat: Simplif'IA France · migration vers nouveau repo + Traefik labels" > /dev/null
NB_FILES=$(git ls-files | wc -l | tr -d ' ')
echo -e "${GRN}✅ Commit créé · ${NB_FILES} fichiers${NC}"
echo ""

# 3. Configure remote
echo -e "${YEL}[3/5]${NC} Configuration du remote…"
git remote add origin "$NEW_REPO" 2>/dev/null || git remote set-url origin "$NEW_REPO"
echo -e "Remote : ${BLU}$NEW_REPO${NC}"
echo -e "${GRN}✅ Remote configuré${NC}"
echo ""

# 4. Push
echo -e "${YEL}[4/5]${NC} Push vers GitHub…"
echo ""
echo -e "${YEL}⚠ Si GitHub demande l'authentification :${NC}"
echo -e "   Username : ${BLU}cirquephotovideo${NC}"
echo -e "   Password : ${BLU}ton Personal Access Token (PAT)${NC}"
echo -e "   Pas de PAT ? → ${BLU}https://github.com/settings/tokens/new${NC}"
echo -e "   Cocher la case ${BLU}'repo'${NC} (Full control of private repositories)"
echo ""

git push -u origin main

echo ""
echo -e "${GRN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GRN}║   ✅  Code poussé sur cirquephotovideo/simplif-ia-france  ║${NC}"
echo -e "${GRN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 5. Prochaines étapes
echo -e "${YEL}[5/5]${NC} Prochaines étapes (auto)"
echo ""
echo -e "1. ${BLU}Coolify${NC} sera mis à jour pour pointer vers ce repo"
echo -e "   → Claude le fait via l'UI web (en parallèle)"
echo ""
echo -e "2. ${BLU}GitHub App${NC} : installer 'Coolify' sur ton compte cirquephotovideo"
echo -e "   → Si pas déjà fait, Coolify te demandera de l'autoriser"
echo -e "   → Lien direct : ${BLU}https://github.com/apps/coolify-io/installations/new${NC}"
echo ""
echo -e "3. ${BLU}Auto-deploy${NC} : à chaque ${BOLD}git push${NC} depuis ce dossier,"
echo -e "   Coolify va build + déployer automatiquement."
echo -e "   Pour pousser, double-clique sur ${BLU}Pousser-vers-GitHub.command${NC}"
echo ""
echo -e "🔗 ${BLU}Repo${NC} : https://github.com/cirquephotovideo/simplif-ia-france"
echo -e "🔗 ${BLU}Coolify${NC} : http://51.75.31.123:8000/project/yocsskwsk4c0gg8c8kkw4wsc/environment/xcs048gokgsks4wkooc0csog/application/gc0k4s0gk8wcc4sog0ogkosg"
echo ""

read -p "Appuie sur Entrée pour fermer…"
