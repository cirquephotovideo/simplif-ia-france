#!/usr/bin/env bash
# ============================================================
# DÉPLOIEMENT AUTOMATIQUE · GitHub + Coolify
# ============================================================
set -e

cd "$(dirname "$0")"

GRN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; BLU='\033[0;34m'; NC='\033[0m'

clear
echo -e "${BLU}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLU}║      SIMPLIF'IA FRANCE · Déploiement GitHub          ║${NC}"
echo -e "${BLU}╚══════════════════════════════════════════════════════╝${NC}\n"

# ---- 1. Nettoyage .git existant ----
echo -e "${YEL}[1/5]${NC} Nettoyage .git existant…"
if [ -d .git ]; then
  sudo rm -rf .git 2>/dev/null || rm -rf .git
fi
echo -e "${GRN}✅ Nettoyé${NC}\n"

# ---- 2. Init Git ----
echo -e "${YEL}[2/5]${NC} Initialisation Git…"
git init -b main > /dev/null 2>&1
git add .
git -c user.email="arnaud@gredai.com" -c user.name="Arnaud Durand" commit -m "feat: Simplif'IA France · plateforme complète" > /dev/null 2>&1
echo -e "${GRN}✅ Commit créé · 75 fichiers${NC}\n"

# ---- 3. Configuration remote ----
REPO="${GITHUB_REPO:-https://github.com/pixeeplay/simplif-ia-france.git}"
echo -e "${YEL}[3/5]${NC} Configuration GitHub remote…"
echo -e "Repo : ${BLU}$REPO${NC}"
git remote add origin "$REPO" 2>/dev/null || git remote set-url origin "$REPO"
echo -e "${GRN}✅ Remote configuré${NC}\n"

# ---- 4. Push ----
echo -e "${YEL}[4/5]${NC} Push vers GitHub…"
echo -e "${YEL}⚠ Si GitHub demande l'authentification :${NC}"
echo -e "   Username : ${BLU}pixeeplay${NC}"
echo -e "   Password : ${BLU}votre Personal Access Token${NC} (PAT, pas le mot de passe)"
echo -e "   Pas de PAT ? Créez-en un : https://github.com/settings/tokens/new"
echo -e "   Cocher 'repo' (full control)\n"
git push -u origin main --force

echo ""
echo -e "${GRN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GRN}║         ✅ CODE POUSSÉ SUR GITHUB                     ║${NC}"
echo -e "${GRN}╚══════════════════════════════════════════════════════╝${NC}\n"

# ---- 5. Coolify deploy ----
echo -e "${YEL}[5/5]${NC} Déploiement Coolify…"
if [ -n "${COOLIFY_TOKEN:-}" ] && [ -n "${COOLIFY_APP_UUID:-}" ]; then
  COOLIFY_URL="${COOLIFY_URL:-http://51.75.31.123:8000}"
  echo "Déclenchement du déploiement…"
  curl -sf -X POST \
    -H "Authorization: Bearer $COOLIFY_TOKEN" \
    "$COOLIFY_URL/api/v1/deploy?uuid=$COOLIFY_APP_UUID" \
    && echo -e "\n${GRN}✅ Déploiement déclenché${NC}\n" \
    || echo -e "\n${RED}❌ Échec du déploiement Coolify${NC}\n"
else
  echo -e "${YEL}⚠ COOLIFY_TOKEN non défini.${NC}"
  echo -e "Déploiement à lancer manuellement dans Coolify :"
  echo -e "   ${BLU}http://51.75.31.123:8000${NC}\n"
fi

echo -e "${BLU}Étapes suivantes dans Coolify :${NC}"
echo -e "  1. Ouvrez ${BLU}http://51.75.31.123:8000${NC}"
echo -e "  2. Si l'app existe déjà : Settings → Redeploy"
echo -e "  3. Si nouvelle app : + Add Resource → Docker Compose → branche main"
echo ""
echo "Appuyez sur Entrée pour fermer…"
read
