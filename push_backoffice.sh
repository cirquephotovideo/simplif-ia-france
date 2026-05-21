#!/usr/bin/env bash
# Push du back-office Simplif'IA France
# Usage : bash push_backoffice.sh
set -e

cd "$(dirname "$0")"

echo "🧹 Nettoyage des locks éventuels…"
rm -f .git/index.lock .git/HEAD.lock 2>/dev/null || true

echo "📋 Mise à jour du .gitignore…"
grep -q "^node_modules/" .gitignore 2>/dev/null || echo "node_modules/" >> .gitignore
grep -q "^\*.bak" .gitignore 2>/dev/null || echo "*.bak" >> .gitignore

echo "🗑  Retrait de node_modules du tracking (si présent)…"
git rm -r --cached node_modules 2>/dev/null || true
git rm --cached frontend/public/admin.html.bak 2>/dev/null || true

echo "➕ Staging de tous les changements…"
git add -A

echo "📝 Liste des fichiers modifiés :"
git status --short

echo ""
echo "💾 Commit…"
git commit -m "feat: back-office + gestion clés API + sécurité

Backend FastAPI
- Modèle ApiCredential (40+ providers, chiffrement Fernet AES-256)
- API /api/credentials (CRUD + test + reveal + toggle)
- Service gouv_api_extended (clients pour API Particulier, Entreprise,
  France Travail, Légifrance, Judilibre, INSEE, AR24, Yousign,
  Anthropic, OpenAI, Gemini, Mistral, ElevenLabs, Stripe, Sentry)
- Models Mail, VaultAccessRequest, AdminSetting + endpoints
- Migration localStorage -> PostgreSQL

Frontend
- Panneau Clés API dans le back-office (sidebar Système)
- 40+ cartes provider avec test live, edit modal, export .env
- Bouton URGENT bulletproof (handler robuste + fallback)
- Toutes les popups toast désactivées définitivement
- Tarifs détaillés (Free / Premium / Pro)
- Léa auto-pilote + Boîte de Léa + limite échanges (2/5/Premium)
- Search FAB déplacée à droite + watchdog

Documentation
- API_REGISTRATION_GUIDE.md : URLs d'inscription + délais pour
  toutes les APIs gouvernementales et tiers"

echo ""
echo "🚀 Push vers origin/main…"
git push origin main

echo ""
echo "✅ Terminé !"
