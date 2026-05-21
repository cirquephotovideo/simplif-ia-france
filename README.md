# Simplif'IA France

Plateforme SaaS de simplification administrative française assistée par IA.

## Stack

- **Backend** : Python 3.11 · FastAPI · SQLAlchemy · PostgreSQL · Redis
- **Frontend** : HTML/JS statique · Nginx
- **IA** : Google Gemini (RAG) · ElevenLabs (TTS) · Tesseract (OCR)
- **Déploiement** : Docker Compose · Coolify · GitHub Actions

## Architecture

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Frontend    │────►│   Backend     │────►│  PostgreSQL  │
│  Nginx :80   │     │  FastAPI :8000│     │     :5432    │
└──────────────┘     └───────┬───────┘     └──────────────┘
                             │
                     ┌───────┼─────────────┐
                     ▼       ▼             ▼
                  Gemini  ElevenLabs   API Gouv.fr
                                       (BAN, Sirene,
                                        Annuaire)
```

## Démarrage rapide (local)

### Prérequis

- Docker 24+ et Docker Compose v2
- Make (optionnel)

### Lancer

```bash
git clone https://github.com/<votre-org>/simplif-ia-france.git
cd simplif-ia-france
cp .env.example .env
# Éditez .env et renseignez vos clés API
docker compose up --build
```

Application accessible sur :
- Frontend : http://localhost:8080
- API Backend : http://localhost:8000
- Docs Swagger : http://localhost:8000/docs

### Compte admin par défaut

Au premier lancement, un compte admin est créé (voir `.env`) :
- Email : `admin@simplif-ia.fr`
- Mot de passe : valeur de `ADMIN_PASSWORD`

## Variables d'environnement

Voir `.env.example`. Les principales :

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `POSTGRES_PASSWORD` | Mot de passe DB | ✅ |
| `JWT_SECRET` | Secret JWT (32+ chars) | ✅ |
| `MASTER_ENCRYPTION_KEY` | Clé maîtresse AES-256 (44 chars base64) | ✅ |
| `GEMINI_API_KEY` | Clé Google Gemini API | Recommandé |
| `ELEVENLABS_API_KEY` | Clé ElevenLabs (TTS premium) | Optionnel |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Compte admin initial | ✅ |

Pour générer des secrets :
```bash
# JWT secret
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Master encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Déploiement Coolify

1. Pousser le repo sur GitHub.
2. Dans Coolify, créer un nouveau projet → Type "Docker Compose".
3. Connecter au repo GitHub.
4. Renseigner les variables d'environnement de `.env.example`.
5. Build & deploy.

## Sécurité

- ⚠️ Ne **jamais** committer `.env`, fichiers `*.key`, ou logs de prod.
- Tous les documents utilisateurs sont chiffrés AES-256 avant stockage.
- Les clés API tierces (Gemini, ElevenLabs) restent côté backend uniquement.
- Authentification JWT avec rotation de refresh tokens.
- Audit log immuable de toutes les actions sensibles.

## Conformité

- Hébergement souverain (OVH / Scaleway / Outscale recommandé).
- RGPD : droits d'accès, export, suppression implémentés.
- Article 4 loi 71-1130 : positionnement "outil" et non "conseil juridique".

## Licence

Propriétaire. © 2026 Simplif'IA France.
