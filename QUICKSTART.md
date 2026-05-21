# 🚀 Quickstart — De zéro à déployé en 15 minutes

## Étape 1 · Installer le projet localement

Ouvrez votre **Terminal Mac** (pas Cowork) et tapez :

```bash
cd ~/Desktop/ia\ france/simplif-ia-france

# Le sandbox a laissé un .git verrouillé, on le supprime
sudo rm -rf .git

# Préparer l'environnement
cp .env.example .env

# Générer JWT_SECRET et MASTER_ENCRYPTION_KEY
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(64))"
python3 -c "from cryptography.fernet import Fernet; print('MASTER_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
# Copiez les 2 lignes dans .env, et remplissez aussi POSTGRES_PASSWORD et ADMIN_PASSWORD

# Lancer la stack Docker locale
docker compose up -d --build
```

Test : http://localhost:8080 (frontend) · http://localhost:8080/docs (API Swagger).

## Étape 2 · Pousser sur GitHub

```bash
git init -b main
git add .
git commit -m "feat: initial Simplif'IA France platform"

# Créez un repo sur github.com (privé recommandé), puis :
git remote add origin git@github.com:VOTRE-ORG/simplif-ia-france.git
git push -u origin main
```

## Étape 3 · Déployer sur Coolify

### A. Dans l'UI Coolify (http://51.75.31.123:8000)

1. **Project** → **+ Add New Resource** → **Docker Compose**
2. Source : **GitHub** (autorisez Coolify si pas déjà fait)
3. Repo : `simplif-ia-france` · Branche : `main`
4. Compose file : `docker-compose.yml`
5. **Environment Variables** : copiez le contenu de votre `.env` local (sans `#` commentaires)
6. **Domain** : ajoutez `simplifia.votre-domaine.fr` + activez Let's Encrypt
7. **Deploy**

### B. (Alternative) Déploiement par API

```bash
# Créez un NOUVEAU token Coolify (révoquez l'ancien partagé en chat)
export COOLIFY_TOKEN=<votre-nouveau-token>

# Récupérez l'UUID de l'app dans Coolify (URL du projet)
export COOLIFY_APP_UUID=<uuid>

# Déployez
./scripts/deploy-coolify.sh $COOLIFY_APP_UUID
```

## Étape 4 · Configurer GitHub Actions pour redéployer auto à chaque push

Dans **GitHub repo → Settings → Secrets and variables → Actions**, ajoutez :
- `COOLIFY_TOKEN` = votre nouveau token
- `COOLIFY_URL` = `http://51.75.31.123:8000`
- `COOLIFY_APP_UUID` = l'UUID de votre app

Désormais, à chaque `git push`, GitHub Actions :
1. Lance les tests
2. Build les images Docker
3. Déclenche le déploiement Coolify

## ⚠️ Sécurité avant la prod

- [ ] **Révoquer le token Coolify** partagé en chat
- [ ] **Régénérer la clé ElevenLabs** partagée en chat
- [ ] DEBUG=false dans `.env`
- [ ] CORS_ORIGINS = uniquement votre domaine
- [ ] Backups Postgres actifs dans Coolify
- [ ] DPIA RGPD signée
- [ ] CGU/Politique de confidentialité publiées

## Aide

- Documentation API : `https://votre-domaine.fr/docs` (en mode DEBUG seulement)
- Logs : `docker compose logs -f` (local) ou Coolify UI (prod)
- Reset complet : `make reset` (efface DB locale et redémarre)

## Stack déployée

```
Internet
   │
   ▼  HTTPS (Let's Encrypt via Coolify)
┌──────────────────────────┐
│   Frontend nginx :80     │  → HTML statiques (landing, prototype, admin)
│   /api/* proxy           │  → Backend
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐     ┌─────────────┐     ┌──────────┐
│ Backend FastAPI :8000    │────►│ Postgres 16 │     │ Redis 7  │
│ JWT auth · vault AES-256 │     └─────────────┘     └──────────┘
│ Gemini · ElevenLabs · BAN│
│ Sirene · Annuaire admin  │
└──────────────────────────┘
```
