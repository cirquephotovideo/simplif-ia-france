# 🔍 Audit Chrome — Simplif'IA France — 20/05/2026

## 🚨 Pourquoi je n'ai pas pu vérifier dans Chrome live

**Le site reste hors ligne en production.** Le DNS n'a pas encore été corrigé depuis la dernière session.

| Domaine | DNS actuel | Réponse Chrome |
|---|---|---|
| `https://simplif-ia.fr/` | `217.160.0.226` (IONOS parking) | TLS handshake échoue (`tlsv1 alert internal error`) |
| `https://simplif-ia.com/` | `34.111.179.208` (IP GCP morte) | `ERR_CONNECTION_CLOSED` |
| Serveur Coolify `51.75.31.123` | en ligne | répond `503` quand on lui envoie le bon `Host` → **les domaines ne sont pas configurés dans Coolify**, ou le service `frontend` n'est pas attaché |

➡️ Tant que les A-records ne pointent pas vers `51.75.31.123` ET que Coolify ne route pas les hôtes vers le service `frontend`, **rien n'est visible publiquement**. Le plan complet est dans `FIX-PROD.md`.

---

## ✅ Ce que j'ai vérifié en statique sur ton code local

### Bonnes nouvelles (tout est en ordre côté code)

- **og-image.png** (64 KB) bien créée dans `frontend/public/assets/`
- **Tous les liens internes** entre pages `.html` sont valides — aucun 404 cassé entre pages
- **Toutes les ressources locales** (CSS, JS, images, fonts) référencées existent réellement
- **40 pages HTML** ont toutes : `<title>`, `meta description`, `charset utf-8`, `lang="fr"`
- **CSP** et headers de sécurité présents en `<meta>` sur toutes les pages
- **Aucune cassure d'encodage** (les `d'conomies` ont été corrigés)
- **Aucun mixed content** (`http://` parasite)
- **Sitemap.xml + robots.txt** présents et cohérents
- **`.well-known/security.txt`** présent (bonus bug bounty)

### Points d'attention (non bloquants)

| Sévérité | Sujet | Détail | Reco |
|---|---|---|---|
| 🟡 SEO | Pas de `hreflang` | `.fr` et `.com` servent le même contenu une fois en ligne → risque de duplicate content | Choisir un canonical définitif (tout pointe déjà vers `.fr`) **et** rediriger 301 `.com → .fr` au niveau Traefik |
| 🟡 SEO | `og:url` figés sur `.fr` | Cohérent avec le canonical `.fr` — donc pas un bug, juste à confirmer | Décision stratégique : `.fr` reste canonique ? |
| 🟡 Perf | `admin.html` = **1 040 KB** | Mono-fichier énorme. Trop lourd sur mobile 4G. | Voir si splittable (admin = derrière login, donc moins critique pour SEO/perf publique) |
| 🟡 Perf | `app.html` = **625 KB** | Idem, mais aussi derrière login | OK pour MVP, à splitter plus tard |
| 🟡 Repo hygiene | `admin.html.bak` (785 KB) tracké | `.bak` est dans `.gitignore` mais ce fichier précis est sans doute déjà commité | `git rm --cached admin.html.bak && git commit` |
| 🟡 Mineur | `50x.html` n'a pas de `viewport` ni `meta description` | Page d'erreur serveur — peu impactant | À compléter si tu y tiens |

### Pages mesurées (H1 OK, tone produit cohérent)

```
index.html        : "Vos démarches admin, enfin simples."
landing.html      : "Vos démarches admin, enfin simples."
tarifs.html       : "Un prix juste, pour tout le monde."
factures.html     : "Factures, devis, URSSAF en pilote automatique."
pense-maison.html : "Pense-Maison. La mémoire de votre foyer."
apropos.html      : "Soulager la charge mentale administrative des Français."
```

---

## 🎯 Prochaines étapes pour que je puisse VRAIMENT vérifier dans Chrome

Tu as deux options :

### Option A — Prévisualiser en local maintenant
Lance le fichier :
```
Lancer-Simplif-IA.command
```
Le site sera dispo sur `http://localhost:8080`. Dis-le-moi, j'ouvre Chrome dessus et je fais l'audit live complet (console, réseau, parcours, mobile, Lighthouse).

### Option B — Remettre la prod en ligne
Suivre [`FIX-PROD.md`](./FIX-PROD.md) :
1. Mettre A-records de `simplif-ia.fr` ET `simplif-ia.com` vers `51.75.31.123`
2. Dans Coolify : ajouter les 4 domaines dans l'app, redeploy, vérifier émission Let's Encrypt
3. Attendre 5-30 min de propagation
4. Me dire "c'est en ligne" → je relance l'audit Chrome live

Tant que ces étapes ne sont pas faites, **personne** (toi, moi, ni un visiteur) ne peut voir le site en production.

---

*Audit généré le 2026-05-20 par Claude.*
