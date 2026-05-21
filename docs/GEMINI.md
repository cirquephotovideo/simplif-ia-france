# 🧠 Gemini · Capacités IA de Simplif'IA France

Ce document liste **tout ce que Maître Léa fait grâce à Gemini** dans le projet.

> **Setup** : ajoute ta clé dans `.env` (`GEMINI_API_KEY=AIza...`) puis double-clique
> sur `Lancer-Simplif-IA.command`. Sans clé, tous les endpoints répondent en
> **mode démo** (réponses simulées).

---

## 🏎 Modèle utilisé

Par défaut : **`gemini-1.5-pro-latest`** (multimodal, contexte 2 M tokens).
Tu peux le changer dans `.env` :

```env
GEMINI_MODEL=gemini-1.5-pro-latest     # qualité max (lent, plus cher)
GEMINI_MODEL=gemini-1.5-flash-latest   # rapide, moins cher (recommandé)
GEMINI_MODEL=gemini-2.0-flash-exp      # dernière génération (en bêta)
```

---

## 🎯 Les 14 capacités exposées via l'API

| # | Endpoint | Capacité | Pour quoi |
|---|---|---|---|
| 1 | `POST /api/ai/chat` | **Maître Léa · chat juridique** | Répondre aux questions de droit admin français, sourcé Légifrance |
| 2 | `POST /api/ai/translate-jargon` | **Anti-jargon · 3 niveaux** | Traduire un courrier admin en : original / FALC / impact pratique |
| 3 | `POST /api/ai/ocr` | **OCR multimodal de documents** | Scanner une photo/PDF de courrier → extraire montants, dates, dossier, action |
| 4 | `POST /api/ai/cerfa/prefill` | **Pré-remplissage CERFA** | Remplir un CERFA à partir des données du coffre-fort utilisateur |
| 5 | `POST /api/ai/classify-mail` | **Classification de courriers** | Type, priorité, délai, organisme, action recommandée |
| 6 | `POST /api/ai/detect-aids` | **Détection d'aides éligibles** | À partir d'un profil → liste d'aides probables avec montants estimés |
| 7 | `POST /api/ai/letter` | **Génération RAPO / courrier formel** | Rédige un recours préalable obligatoire avec articles de loi cités |
| 8 | `POST /api/ai/summarize` | **Résumé automatique** | Compresse un long document en N mots |
| 9 | `POST /api/ai/translate` | **Traduction multilingue** | FR ↔ EN, AR, ES, PT, créole, ZH, RU |
| 10 | `POST /api/ai/extract-entities` | **Extraction d'entités** | Dates, montants, IBAN, dossiers, adresses, articles de loi |
| 11 | `POST /api/ai/check-consistency` | **Audit de cohérence d'un dossier** | Détecte erreurs, pièces manquantes, taux de succès estimé |
| 12 | `POST /api/ai/email-reply` | **Réponse contextuelle à un mail** | Génère une réponse selon l'intent (refuser, accepter, demander info…) |
| 13 | `POST /api/ai/voice-text` | **Texte adapté à la voix (TTS)** | Réécrit un texte pour qu'il soit naturel à lire à voix haute |
| 14 | `POST /api/ai/fact-check` | **Vérification factuelle sourcée** | Vrai/faux/partiel + articles officiels |

Plus : `GET /api/ai/health` → état du service, modèle utilisé, capacités actives.

---

## 🪄 Ce qui est génial avec Gemini (vs ChatGPT)

1. **Vision native multimodale** — donne-lui directement une photo de courrier CAF,
   il extrait montants, dates, dossier, action en une seule requête. Pas besoin de
   passer par Tesseract avant.
2. **Contexte gigantesque** — jusqu'à **2 millions de tokens** (≈ 1 500 pages PDF).
   On peut lui donner un Code de la Sécurité Sociale entier comme contexte RAG.
3. **Mode JSON natif** — `response_mime_type=application/json` garantit du JSON
   valide. Plus de parsing fragile avec regex.
4. **Function calling** — Gemini peut décider d'appeler des outils (API gouv,
   Légifrance, Stripe…). Idéal pour l'agent "Clic-par-clic".
5. **Système d'instructions persistant** — Maître Léa reste juridique strict même
   sur 50 tours de conversation.
6. **Streaming** — réponses en streaming pour UX rapide (typing indicator).
7. **Voix native** (Gemini Audio) — bientôt remplacera ElevenLabs pour le TTS,
   directement sur le même endpoint.
8. **Coût bas** — `gemini-1.5-flash` : ~0,075 € par 1M tokens (vs Claude Sonnet
   3 € / 1M). Idéal pour les volumes de Simplif'IA.

---

## 💡 Exemples de prompts puissants pour Simplif'IA

### Cas 1 · Indu CAF (mail entrant)

L'utilisateur reçoit un courrier CAF "Indu APL 840 €". Le flux :

```bash
# 1. Scan multimodal du courrier
curl -F "file=@indu_caf.jpg" http://localhost:8080/api/ai/ocr
# → {document_type: "indu_caf", amount: 840, case_number: "7842156",
#    deadline: "2026-06-28", action_required: "RAPO sous 2 mois"}

# 2. Génération du RAPO
curl -X POST http://localhost:8080/api/ai/letter \
  -d '{"purpose":"RAPO indu APL 840€","recipient":"CAF de Paris",
       "context":{"dossier":"7842156","raison":"prime exceptionnelle non récurrente"}}'
# → {subject, letter (4 paragraphes), articles cités, send_via: "LRE_eIDAS"}

# 3. Envoi en LRE via AR24 (endpoint séparé /lre/send)
```

### Cas 2 · Naturalisation

```bash
# Profil utilisateur → aides éligibles
curl -X POST http://localhost:8080/api/ai/detect-aids \
  -d '{"profile":{"rfr":11500,"foyer":2,"logement":"locataire","age":34,"statut":"salarié"}}'
# → APL (180€/mois), Prime activité (85€), Chèque énergie (148€/an)…
```

### Cas 3 · Anti-jargon

```bash
# Le user colle un texte admin incompréhensible
curl -X POST http://localhost:8080/api/ai/translate-jargon \
  -d '{"text":"Conformément à l article L553-1 du CSS..."}'
# → {level_1_original, level_2_falc (lisible niveau A2),
#    level_3_impact: {deadline, action, risk, amount}}
```

### Cas 4 · Multimodal · CNI scannée

```bash
# Scan CNI → CERFA pré-rempli
curl -F "file=@cni_recto_verso.pdf" http://localhost:8080/api/ai/ocr
# → {nom, prénom, date_naissance, lieu_naissance, numéro_CNI}

curl -X POST http://localhost:8080/api/ai/cerfa/prefill \
  -d '{"cerfa_id":"12100*02","user_data":{...données OCR...}}'
# → CERFA aide juridictionnelle rempli, prêt à signer
```

---

## 🔐 Sécurité & RGPD

- **Zero-retention** : Gemini Enterprise stocke 0 prompt côté Google
  (vérifier la config dans Google Cloud Console).
- **Pas de PII brut** : extraire d'abord les entités, puis envoyer le minimum
  contextuel nécessaire.
- **Anonymisation** : remplacer noms/numéros par tokens avant prompt si possible.
- **Cache Redis** sur les réponses non-PII pour économiser les tokens.

---

## 📊 Coûts estimés (gemini-1.5-flash)

| Action | Tokens moyens | Coût/100 actions |
|---|---|---|
| Chat juridique court | ~800 in + 300 out | 0,007 € |
| OCR document | ~2000 in (image) + 500 out | 0,028 € |
| Génération RAPO | ~600 in + 800 out | 0,015 € |
| Anti-jargon | ~1500 in + 600 out | 0,016 € |
| Classification mail | ~400 in + 100 out | 0,003 € |

**Pour 1000 utilisateurs actifs avec ~10 actions/mois** : **≈ 80 €/mois** de coût IA.

---

## 🧪 Test rapide

Une fois la stack lancée :

```bash
# Sans auth (mode démo)
curl http://localhost:8080/api/ai/health

# Avec auth (token JWT requis)
TOKEN=$(curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@simplif-ia.fr","password":"yNrs99igkRxYaKHDV1mT-gUIgcCUVT0-"}' | jq -r .access_token)

curl -X POST http://localhost:8080/api/ai/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"J ai reçu un indu CAF de 840€, que faire ?"}'
```

---

## 🚀 Prochaines étapes (post-MVP)

- **RAG Légifrance** : indexer 10 000 articles dans Qdrant pour citations exactes
- **Streaming** : SSE pour Maître Léa en temps réel
- **Function calling** : Gemini déclenche directement les démarches via les APIs gouv
- **Cache prompts** : Redis 24h sur les questions fréquentes
- **Fine-tuning** : modèle custom sur jurisprudence française (Vertex AI)
- **Vision PDF natif** : sauter Tesseract, tout passer en Gemini Vision
