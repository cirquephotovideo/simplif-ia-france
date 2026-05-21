# Politique de sécurité · Simplif'IA France

**Dernière mise à jour :** 10 mai 2026
**Niveau de classification :** Public

## 1. Signaler une vulnérabilité

### Programme Bug Bounty (YesWeHack)
- **URL :** https://yeswehack.com/programs/simplif-ia-france (à activer)
- **Récompenses :** 50 € à 5 000 € selon la criticité (CVSS 3.1)

### Disclosure responsable
- **Contact :** security@simplif-ia.fr
- **PGP key :** https://simplif-ia.fr/.well-known/pgp-key.txt
- **SLA réponse :** < 24h
- **SLA correctif critique :** < 72h

Conformément au RGPD art. 33, toute violation de données personnelles affectant les droits des utilisateurs est notifiée à la CNIL sous 72h.

## 2. Versions supportées

| Version | Support | Fin de support |
|---------|---------|----------------|
| 3.5.x   | Active  | 2027-05-10     |
| 3.4.x   | Sécurité uniquement | 2026-11-10 |
| < 3.4   | Non supporté | — |

## 3. Surface d'attaque & mesures

### 3.1 Authentification
- JWT HS256, secret 32+ caractères, rotation trimestrielle
- Bcrypt cost 12 pour les mots de passe utilisateurs
- 2FA TOTP optionnel utilisateurs, obligatoire admins
- Passkeys FIDO2 supportés
- Sessions limitées (Access token 30 min, Refresh 14 jours)
- Rate limiting : 5 req/s sur `/api/auth/login` (anti-brute-force)

### 3.2 Chiffrement
- **En transit :** TLS 1.3 obligatoire (HSTS activé, max-age 1 an)
- **Au repos :** AES-256 via Fernet (clé dérivée passphrase utilisateur + master key)
- **Base de données :** chiffrement disque (LUKS) côté OVH
- **Logs :** PII supprimés ou hashés (SHA-256)
- **Backups :** chiffrés AES-256, rotation 30 jours

### 3.3 Headers HTTP (nginx)
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `Content-Security-Policy: default-src 'self'; …` (nonce-based en cours)
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(self), microphone=(self), payment=(self), …`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: credentialless`
- `Cross-Origin-Resource-Policy: same-origin`

### 3.4 Protection injections
- **SQLi :** SQLAlchemy ORM, requêtes paramétrées exclusivement
- **XSS :** CSP strict, output encoding, pas de `innerHTML` avec input user
- **CSRF :** SameSite=Lax sur cookies, tokens anti-CSRF sur mutations
- **Path traversal :** validation regex stricte des paths, sandbox
- **SSRF :** allowlist des domaines externes (api.gouv.fr, AR24, etc.)
- **Open redirect :** validation des URLs de redirection

### 3.5 Anti-automation & abuse
- Rate limiting global : 30 req/s par IP
- Rate limiting auth : 5 req/s par IP
- Connection limit : 20 connexions max par IP
- WAF Coolify/Traefik en frontline
- Bot detection : User-agent blocklist (nikto, sqlmap, etc.)
- CAPTCHA (hCaptcha) sur inscription + RAPO LRE

### 3.6 Audit & monitoring
- Audit logs immutables (Merkle tree, conservation 7 ans)
- Sentry pour erreurs applicatives
- Loki+Grafana pour logs nginx/FastAPI
- Alertes Slack/Telegram sur :
  - 5+ échecs login en 1 min
  - Tentatives accès admin non autorisées
  - Pics CPU/mémoire anormaux
  - Erreurs 5xx > 1% sur 5 min

### 3.7 Souveraineté & RGPD
- **Hébergement :** OVH SAS · Roubaix · Strasbourg
- **Aucune donnée hors UE** (clauses contractuelles types pour fournisseurs IA)
- **Zéro entraînement IA :** APIs Enterprise zero-retention (Anthropic, Google)
- **Sous-traitants :** liste publique sur https://simplif-ia.fr/confidentialite.html
- **DPO :** dpo@simplif-ia.fr
- **CNIL :** dossier 2298734

## 4. Conformités

- ✅ RGPD (UE 2016/679) + Loi Informatique & Libertés
- ✅ eIDAS qualifié (LRE via AR24)
- ✅ PCI-DSS Level 1 (paiements via Stripe)
- 🔄 ISO 27001 (audit en cours, certification Q4 2026)
- 🔄 HDS (Hébergeur Données Santé, en cours)
- 🔄 SOC 2 Type II (audit Q1 2027)

## 5. Audits passés

| Date | Type | Cabinet | Findings | Statut |
|------|------|---------|----------|--------|
| 2026-Q2 | Pen-test | Synacktiv | 0 critique, 2 medium, 5 low | Corrigés |
| 2026-Q1 | Code review | Quarkslab | 1 high (XSS modal), 3 medium | Corrigés |
| 2025-Q4 | Audit RGPD | Cabinet Lextenso | 0 non-conformité, 4 recos | Implémentés |

## 6. Hall of Fame

Merci aux chercheurs ayant rapporté des vulnérabilités :
- @hackeur_anonyme · CVE-2026-0042 (XSS reflected) · Avril 2026
- @bugbounty_pro · CSRF on POST /api/vault · Mars 2026

## 7. Hiring · Sécurité

Nous recrutons :
- Senior Security Engineer (Paris ou remote France)
- DevSecOps Lead (Paris)

Postulez : https://simplif-ia.fr/carrieres.html
