#!/usr/bin/env bash
# Script à exécuter une fois sur votre Mac (pas dans le sandbox Cowork)
# Initialise git, push sur GitHub, et déploie via Coolify
set -euo pipefail

cd "$(dirname "$0")/.."

# 1. Nettoyer un éventuel .git corrompu créé en sandbox
if [ -d .git ]; then
  echo "🧹 Suppression de .git existant…"
  rm -rf .git
fi

# 2. Init Git frais
echo "📦 Initialisation Git…"
git init -b main
git add .
git commit -m "feat: initial Simplif'IA France platform"

# 3. Demander l'URL du repo GitHub
if [ -z "${GITHUB_REPO:-}" ]; then
  read -p "🔗 URL repo GitHub (ex: git@github.com:votre-org/simplif-ia-france.git) : " GITHUB_REPO
fi

# 4. Pousser
git remote add origin "$GITHUB_REPO"
git push -u origin main

echo ""
echo "✅ Code poussé sur GitHub !"
echo ""
echo "Étapes suivantes dans Coolify (http://51.75.31.123:8000) :"
echo "  1. + New Resource → Docker Compose → GitHub"
echo "  2. Choisir le repo simplif-ia-france, branche main"
echo "  3. Coller les variables d'environnement de .env.example (avec vraies valeurs)"
echo "  4. Configurer le domaine + Let's Encrypt"
echo "  5. Deploy"
echo ""
echo "📝 N'oubliez pas : RÉVOQUEZ le token Coolify partagé en chat"
echo "   et créez-en un nouveau dans Coolify → Settings → API Tokens"
