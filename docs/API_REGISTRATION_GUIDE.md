# 🔑 Guide de création des comptes API — Simplif'IA France

Toutes les APIs nécessaires au fonctionnement complet de la plateforme, avec les **liens d'inscription**, les **pré-requis**, et les **délais d'obtention typiques**.

> Toutes les clés se collent ensuite dans **Back-office → Système → 🔑 Clés API**. Elles sont chiffrées AES-256 (Fernet) en base et ne sont jamais visibles en clair sans re-authentification admin.

---

## 1. APIs Gouvernementales (DINUM) — via DataPass

**Procédure commune** : toutes ces APIs passent par DataPass, qui gère les autorisations CNIL/RGPD.

1. Créer un compte sur https://datapass.api.gouv.fr/
2. Renseigner l'organisation Simplif'IA (SIRET, RGPD, DPO)
3. Demander l'habilitation pour chaque API (formulaire spécifique)
4. Recevoir une clé `API_KEY` par email après validation (3-15 jours)

| API | URL d'inscription | Délai | Niveau d'accès |
|---|---|---|---|
| **API Particulier** | https://datapass.api.gouv.fr/api-particulier | 7-10j | Gratuit · convention DINUM |
| **API Entreprise** | https://datapass.api.gouv.fr/api-entreprise | 10-15j | Réservé administrations (Simplif'IA éligible via convention) |
| **API SIV** (carte grise) | https://datapass.api.gouv.fr/api-siv | 15-30j | Habilitation Min. Intérieur |
| **API Points Permis** | https://datapass.api.gouv.fr/ | 7j | Gratuit |
| **API HistoVec** | https://histovec.interieur.gouv.fr/ | 10j | Gratuit |
| **API Impôts (DGFiP)** | https://www.impots.gouv.fr/api-particuliers | 15j | Convention DGFiP |
| **API Ameli (CNAM)** | https://assure.ameli.fr/ | 30j | Convention CNAM |
| **API France Travail** | https://francetravail.io/inscription | Immédiat (sandbox) · 5j (prod) | OAuth2 client_credentials |
| **API CPF** | https://www.moncompteformation.gouv.fr/ | 10j | Convention Caisse Dépôts |
| **API ANTS** | https://ants.gouv.fr/ | 15j | Convention ANTS |
| **API COMEDEC** | https://ants.gouv.fr/Les-solutions/COMEDEC | 30j | Mairies raccordées uniquement |
| **API Mes Aides** | https://mes-aides.gouv.fr/ | 7j | Gratuit (DINUM) |
| **Enedis Data Connect** | https://datahub-enedis.fr/data-connect/ | 30j | Consentement utilisateur requis |
| **API DPE ADEME** | https://data.ademe.fr/ | Immédiat | Open data · clé optionnelle |
| **API ANEF** | https://administration-etrangers-en-france.interieur.gouv.fr/ | Variable | Sur projet |

---

## 2. Open Data (gratuit, immédiat)

| API | Inscription | Clé |
|---|---|---|
| **Légifrance** (PISTE) | https://piste.gouv.fr/ | OAuth2 client_credentials |
| **Judilibre** (PISTE) | https://piste.gouv.fr/ | Idem |
| **data.gouv.fr** | https://www.data.gouv.fr/fr/admin/me/ | API key dans profil |
| **INSEE Sirene v3** | https://api.insee.fr/catalogue/ | OAuth2 |
| **Service-Public.fr** | Pas de clé (public) | — |

**Procédure PISTE** (Légifrance + Judilibre) :
1. Compte sur https://piste.gouv.fr/
2. "Mes applications" → "Créer une application"
3. Cocher les APIs voulues (Légifrance, Judilibre)
4. Récupérer `CLIENT_ID` + `CLIENT_SECRET`
5. Endpoint token : `https://oauth.piste.gouv.fr/api/oauth/token`

---

## 3. Identité & SSO

### FranceConnect / FranceConnect+

1. Inscription : https://partenaires.franceconnect.gouv.fr/monprojet/inscription
2. Remplir le dossier (sécurité, DPO, RGPD, captures écran)
3. Validation DINUM : **4-8 semaines**
4. Récupération `CLIENT_ID` + `CLIENT_SECRET` sandbox → puis prod
5. Scopes utiles : `openid profile email address phone identite_pivot`

### La Poste Identité Numérique

1. https://www.idn.laposte.fr/ → espace partenaires
2. Convention commerciale (payant : ~0,80 €/identification)

---

## 4. Courrier & Signature électronique

### AR24 (LRE qualifiée eIDAS)

1. https://www.ar24.fr/inscription-pro/
2. Compte pro avec KBis (validation 24h)
3. Paramétrer un compte d'envoi (RIB pour facturation)
4. Récupérer `API_KEY` dans Paramètres → API
5. **Coût** : ~4,68 € TTC par LRE envoyée

### Yousign

1. https://yousign.com/fr/inscription
2. Compte développeur immédiat
3. Sandbox illimitée → prod après convention
4. **Coût** : 0,50 € à 8 € selon niveau (simple → qualifiée)
5. Token dans **Réglages → API**

### Universign (alternative)

1. https://www.universign.com/fr/inscription/
2. Compte pro · validation 48h
3. PSCE qualifié eIDAS

---

## 5. IA & TTS

| Provider | Inscription | Délai | Coût indicatif |
|---|---|---|---|
| **Google Gemini** | https://aistudio.google.com/apikey | Immédiat | Gratuit jusqu'à 15 req/min |
| **OpenAI** | https://platform.openai.com/api-keys | Immédiat (CB requise) | ~5$/mois usage léger |
| **Anthropic Claude** | https://console.anthropic.com/settings/keys | Immédiat | Crédit gratuit 5$ |
| **Mistral AI** | https://console.mistral.ai/api-keys/ | Immédiat | Tier gratuit |
| **ElevenLabs (TTS)** | https://elevenlabs.io/app/settings/api-keys | Immédiat | 22$/mois pour Léa |

---

## 6. Paiement

### Stripe

1. https://dashboard.stripe.com/register
2. Mode Test immédiat (clés `sk_test_...`)
3. Activation prod : KBis + RIB (24-48h)
4. Récupérer dans Dashboard :
   - `SECRET_KEY` (sk_live_...)
   - `WEBHOOK_SECRET` (whsec_...)
5. Configurer webhook : `https://api.simplif-ia.fr/api/stripe/webhook`
6. Events : `checkout.session.completed`, `customer.subscription.updated`, `invoice.paid`

---

## 7. Sécurité

### hCaptcha (anti-bot, RGPD-friendly)

1. https://dashboard.hcaptcha.com/sites
2. Ajouter le domaine `simplif-ia.fr`
3. Récupérer `SITEKEY` (public) + `SECRET` (privé)

### Sentry (monitoring erreurs)

1. https://sentry.io/signup/
2. Créer un projet Python (FastAPI)
3. Récupérer le `DSN` dans **Settings → Client Keys**

---

## ⚡ Ordre de priorité recommandé

Pour démarrer rapidement, configurez dans cet ordre :

1. ✅ **Anthropic ou Gemini** (LLM Léa) — *immédiat*
2. ✅ **ElevenLabs** (voix Léa) — *immédiat*
3. ✅ **Stripe** (paiements Premium) — *24h*
4. ✅ **Yousign sandbox** (signature) — *immédiat*
5. ✅ **PISTE / Légifrance** (RAG juridique) — *immédiat*
6. ✅ **AR24** (LRE) — *24h*
7. ✅ **FranceConnect sandbox** — *48h*
8. 🟡 **API Particulier** (DataPass) — *10j*
9. 🟡 **API France Travail** — *5j*
10. 🟡 **FranceConnect+ production** — *6-8 semaines*

---

## 🔒 Sécurité des clés

- Toutes les clés sont **chiffrées au repos** (Fernet AES-256) avec `MASTER_ENCRYPTION_KEY`
- Le frontend admin n'affiche qu'un **aperçu masqué** (4 derniers caractères)
- Pour révéler une clé en clair, l'admin doit re-saisir son mot de passe via `/api/credentials/{provider}/reveal`
- Les valeurs ne sont **jamais loggées** (filtre Loguru sur les champs sensibles)
- Backups DB chiffrés par défaut

---

## 📞 Support

- DataPass : datapass@api.gouv.fr
- DINUM (API Gouv) : api@modernisation.gouv.fr
- PISTE : support.piste@modernisation.gouv.fr
