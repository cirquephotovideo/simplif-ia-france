#!/usr/bin/env bash
# ============================================================
# PUSH INCRÉMENTAL · GitHub → Coolify auto-deploy
# ============================================================
# Pousse les changements locaux vers GitHub sans détruire l'historique.
# Coolify détecte le push via webhook et redéploie automatiquement.
# ============================================================
set -e

cd "$(dirname "$0")"

GRN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[0;33m'; BLU='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

clear
echo ""
echo -e "${BLU}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLU}${BOLD}║   📤  Push GitHub · Simplif'IA France                ║${NC}"
echo -e "${BLU}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Vérifier qu'on est dans un repo git
if [ ! -d .git ]; then
  echo -e "${RED}❌ Pas de dossier .git ici. Le repo n'est pas initialisé.${NC}"
  echo "Utilise Deployer-GitHub-Coolify.command pour une première init."
  read -p "Appuie sur Entrée pour fermer…"
  exit 1
fi

# 2. Status
echo -e "${YEL}[1/4]${NC} État du repo…"
git -c safe.directory='*' status --short
CHANGED=$(git -c safe.directory='*' status --porcelain | wc -l | tr -d ' ')
echo ""

# 3. Commit
if [ "$CHANGED" -eq 0 ]; then
  echo -e "${YEL}Rien de nouveau à commiter localement.${NC}"
  echo "Je tente quand même un push au cas où il y aurait des commits non poussés."
else
  echo -e "${YEL}[2/4]${NC} Commit des $CHANGED fichier(s)…"
  git -c safe.directory='*' add .
  read -p "💬 Message de commit (Entrée = 'chore: update') : " MSG
  MSG="${MSG:-chore: update}"
  git -c safe.directory='*' -c user.email="arnaud@gredai.com" -c user.name="Arnaud Durand" commit -m "$MSG"
  echo -e "${GRN}✅ Commit créé${NC}"
fi

# 4. Push
echo ""
echo -e "${YEL}[3/4]${NC} Push vers GitHub…"
echo -e "Si GitHub demande l'auth :"
echo -e "  • Username : ${BLU}pixeeplay${NC}"
echo -e "  • Password : ${BLU}Personal Access Token${NC} (pas le mdp GitHub)"
echo -e "  • PAT à créer : ${BLU}https://github.com/settings/tokens/new${NC} (cocher 'repo')"
echo ""
git -c safe.directory='*' push origin main

# 5. Coolify
echo ""
echo -e "${GRN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GRN}║   ✅  Code poussé · Coolify va déployer auto         ║${NC}"
echo -e "${GRN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "🔗 Suivre le déploiement :"
echo -e "   ${BLU}http://51.75.31.123:8000/project/yocsskwsk4c0gg8c8kkw4wsc/environment/xcs048gokgsks4wkooc0csog/application/gc0k4s0gk8wcc4sog0ogkosg/deployments${NC}"
echo ""

# 6. Tentative d'auto-trigger Coolify si token configuré
if [ -n "${COOLIFY_TOKEN:-}" ]; then
  echo -e "${YEL}[4/4]${NC} Déclenchement manuel Coolify via API…"
  COOLIFY_APP_UUID="gc0k4s0gk8wcc4sog0ogkosg"
  curl -sf -X POST \
    -H "Authorization: Bearer $COOLIFY_TOKEN" \
    "http://51.75.31.123:8000/api/v1/deploy?uuid=$COOLIFY_APP_UUID" \
    && echo -e "${GRN}✅ Déploiement déclenché via API${NC}" \
    || echo -e "${YEL}⚠ API token absent ou invalide — Coolify devrait déployer via webhook quand même${NC}"
fi

echo ""
read -p "Appuie sur Entrée pour fermer…"
