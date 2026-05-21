# 📋 Récap des modifications — Session du 20/05/2026

## 🚨 État de la prod

**Le site est hors ligne sur les deux domaines** (cause DNS, pas code).
Voir [`FIX-PROD.md`](./FIX-PROD.md) pour le plan complet de remise en ligne.

| Domaine | État actuel | Action requise |
|---|---|---|
| `simplif-ia.fr` | ❌ Page parking IONOS, pas de SSL | Changer A-record vers `51.75.31.123` |
| `simplif-ia.com` | ❌ Pointe vers IP GCP inactive | Changer A-record vers `51.75.31.123` |
| Coolify (`51.75.31.123`) | ✅ En ligne | Configurer les domaines dans l'UI |

---

## ✅ Modifications effectuées dans le code

### 1. Image Open Graph créée

- **Avant** : `og-image.png` référencé dans toutes les pages mais **fichier inexistant** → aucun aperçu sur Facebook, Twitter, LinkedIn, WhatsApp, Slack…
- **Après** : Créé `frontend/public/assets/og-image.png` (1200×630, identité tricolore française, badges Made in France/RGPD/ISO 27001/AES-256/14 jours gratuits).
- **Impact** : Gros gain SEO + partage social.

### 2. Corrections typographiques

- `frontend/public/pense-maison.html` : `d'conomies` → `d'économies`
- `frontend/public/factures.html` : `d'conomies` → `d'économies`

### 3. Refonte des cards modules sur factures.html

- **Avant** : chaque card avait un label bleu redondant (ex. "Factures") au-dessus d'un `<h3>` identique ("Factures"). 8 modules avec doublons visuels.
- **Après** : remplacés par des emojis évocateurs (📄 Factures · ✍️ Devis · 🧾 Notes de frais · 🏛️ URSSAF · 📊 TVA · 📈 Bilan · 💰 Trésorerie · 🔔 Relances).
- **Impact** : hiérarchie visuelle plus claire, plus de hooks visuels.

---

## 🟡 Audit fait, non corrigé (en attente du choix utilisateur)

### Méta-tags & canonical : choix `.fr` vs `.com`

Tous les fichiers HTML pointent vers `https://simplif-ia.fr/`. Comme la `.fr` est actuellement parquée chez IONOS et redirige vers `.com`, il faudrait potentiellement :
- Soit **garder .fr comme canonique** et fixer le DNS (recommandé pour la cohérence "France")
- Soit **passer canonique en .com** dans tout le code (sitemap, OG, schema.org, robots)

Je n'ai pas fait le switch sans confirmation — choix stratégique.

### Cohérence des design systems

L'index.html utilise un CSS **inline** complet (1114 lignes), tandis que les ~40 autres pages utilisent les fichiers partagés `assets/style.css`, `themes.css`, `marbre-stars.css`, `elegance.css`. Les deux systèmes sont cohérents en termes de couleurs et typo, mais c'est dupliqué. À unifier dans une refonte plus profonde si nécessaire.

### Vérification Chrome live

Pas réalisée (site down + sandbox Linux qui a un deadlock sur le mount FUSE de ton dossier). Dès que la prod sera remontée, on pourra relancer un audit complet (Lighthouse, console, mobile/desktop, parcours utilisateur).

---

## 🎯 Prochaines étapes recommandées

1. **Immédiat** : Suivre [`FIX-PROD.md`](./FIX-PROD.md) pour remettre la prod en ligne (DNS + Coolify).
2. **Une fois en ligne** : Tester chaque page sur le live, je peux faire l'audit Chrome complet.
3. **Décider domaine canonique** (.fr ou .com) et faire un sweep global des métas.
4. **Lighthouse audit** pour identifier les optimisations perf (lazy loading images, préchargement fonts, etc.).
5. **Pages à approfondir** : `inscription.html`, `connexion.html`, `dashboard.html`, `tarifs.html` — pages clés du parcours de conversion.

---

*Généré par Claude · 20/05/2026 · session "develop to the max"*
