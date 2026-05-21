# Guide de déploiement

## 1. Tests locaux

```bash
cp .env.example .env
make secrets   # copiez JWT_SECRET et MASTER_ENCRYPTION_KEY dans .env
# éditez .env pour définir POSTGRES_PASSWORD et ADMIN_PASSWORD
make up
```

→ http://localhost:8080

## 2. Pousser sur GitHub

```bash
cd simplif-ia-france
git init
git add .
git commit -m "feat: initial Simplif'IA France platform"
git branch -M main
git remote add origin git@github.com:VOTRE-ORG/simplif-ia-france.git
git push -u origin main
```

## 3. Configuration Coolify

### A. Créer la ressource

1. Connectez-vous à votre Coolify (ex: http://51.75.31.123:8000).
2. **Projects** → **+ Add New Resource** → **Docker Compose**.
3. Source : **GitHub** → connectez le repo `simplif-ia-france`.
4. Branche : `main`.
5. Path du compose : `docker-compose.yml`.

### B. Variables d'environnement

Dans Coolify → votre ressource → **Environment Variables**, copiez tout votre `.env` (sans les commentaires).

⚠️ **Critique** :
- `POSTGRES_PASSWORD` : strong password
- `JWT_SECRET` : généré avec `make secrets`
- `MASTER_ENCRYPTION_KEY` : généré avec `make secrets`
- `ADMIN_PASSWORD` : votre mot de passe admin
- `CORS_ORIGINS` : votre domaine de production
- `ALLOWED_HOSTS` : votre domaine de production

### C. Domaine

- **Domain** : ajoutez votre domaine (ex: `simplifia.votre-domaine.fr`)
- **Generate Let's Encrypt SSL** : activez

### D. Healthcheck

Coolify détecte automatiquement les healthchecks définis dans les Dockerfiles.

### E. Déploiement automatique GitHub Actions

Dans **Settings → Secrets** sur GitHub, ajoutez :
- `COOLIFY_TOKEN` : votre token API Coolify (régénérez-le après le partage initial)
- `COOLIFY_URL` : `http://51.75.31.123:8000`
- `COOLIFY_APP_UUID` : visible dans l'URL Coolify de votre app

À chaque push sur `main`, le workflow `.github/workflows/ci.yml` :
1. Lance les tests
2. Build les images Docker
3. Déclenche le redéploiement Coolify via webhook

## 4. Déploiement manuel via API Coolify

```bash
# Lancer un déploiement immédiat
curl -X POST \
  -H "Authorization: Bearer $COOLIFY_TOKEN" \
  "http://51.75.31.123:8000/api/v1/deploy?uuid=$APP_UUID"

# Vérifier le statut
curl -H "Authorization: Bearer $COOLIFY_TOKEN" \
  "http://51.75.31.123:8000/api/v1/applications/$APP_UUID"
```

## 5. Post-déploiement

1. **Test santé** : `curl https://votre-domaine.fr/health` → `{"status": "ok"}`
2. **Login admin** : `https://votre-domaine.fr/admin.html` avec `ADMIN_EMAIL` / `ADMIN_PASSWORD`
3. **Rotation des clés** :
   - Révoquez le token Coolify partagé en chat
   - Générez de nouveaux secrets et mettez-les à jour dans Coolify
4. **Backups** :
   - Configurer les backups Postgres (intégré dans Coolify : Database → Backups)
   - Sauvegarder le volume `storage-data` (S3 + chiffrement supplémentaire recommandé)

## 6. Monitoring

- Coolify expose les logs container en temps réel.
- Pour la prod, ajouter Sentry (`SENTRY_DSN` à intégrer dans `app/main.py`).
- Pour les métriques : Prometheus + Grafana (Coolify peut spawner les containers).

## 7. Rollback

Coolify garde les images des déploiements précédents. Pour rollback :
1. **Deployments** → choisir un déploiement précédent → **Redeploy**

Ou via la CLI Docker directement sur le serveur :
```bash
docker tag simplifia-backend:previous simplifia-backend:latest
docker compose up -d
```

## 8. Sécurité production · checklist avant ouverture publique

- [ ] DEBUG=false dans .env
- [ ] CORS_ORIGINS = uniquement votre domaine
- [ ] Tous les secrets régénérés (jamais ceux du dev)
- [ ] Let's Encrypt activé (HTTPS only)
- [ ] Backups Postgres planifiés
- [ ] Rate limiting activé (slowapi)
- [ ] DPIA RGPD complétée et signée
- [ ] CGU / Politique de confidentialité publiées
- [ ] Politique de réponse à incident écrite
- [ ] 2FA admin activé (à coder en complément du JWT)
