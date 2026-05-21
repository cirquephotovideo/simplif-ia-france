# 🚀 Remettre Simplif'IA en ligne — 3 étapes, 15 minutes

> Le code est **prêt**. Les labels Traefik ont été ajoutés au `docker-compose.yml`. Il ne reste que 3 actions manuelles que tu dois faire (login/2FA requis — je ne peux pas les faire à ta place).

---

## ✅ Étape 1 — Pousser le docker-compose mis à jour sur GitHub *(2 min)*

Dans ton terminal Mac, depuis le dossier `simplif-ia-france/` :

```bash
git add docker-compose.yml
git commit -m "feat(deploy): ajoute labels Traefik pour routing Coolify"
git push
```

---

## ✅ Étape 2 — Corriger le DNS *(5 min + propagation 5-30 min)*

### Pour `simplif-ia.fr` (chez IONOS)

1. Va sur https://login.ionos.fr/
2. **Domaines & SSL** → `simplif-ia.fr` → **Modifier DNS**
3. Supprime les A-records actuels pointant vers `217.160.0.226`
4. Crée ces 3 A-records :

   | Type | Nom | Valeur | TTL |
   |---|---|---|---|
   | A | `@` | `51.75.31.123` | 3600 |
   | A | `www` | `51.75.31.123` | 3600 |
   | A | `api` | `51.75.31.123` | 3600 |

5. **Important** : si une "redirection Web" vers `simplif-ia.com` est active, **désactive-la**.

### Pour `simplif-ia.com`

L'IP actuelle (`34.111.179.208`) est une IP Google Cloud — le domaine est sans doute chez **Google Domains / Squarespace** ou un autre registrar. Cherche dans tes emails "simplif-ia.com" pour retrouver le registrar.

Une fois identifié, mêmes A-records :

| Type | Nom | Valeur | TTL |
|---|---|---|---|
| A | `@` | `51.75.31.123` | 3600 |
| A | `www` | `51.75.31.123` | 3600 |
| A | `api` | `51.75.31.123` | 3600 |

> ⚠️ Si tu as Cloudflare devant : passer le nuage en **gris** ("DNS only") jusqu'à ce que Let's Encrypt ait émis le cert. Tu pourras le repasser en orange après.

---

## ✅ Étape 3 — Configurer Coolify *(5 min)*

1. Ouvre http://51.75.31.123:8000/
2. Login → ouvre l'application **Simplif'IA France**
3. Onglet **General** → champ **Domains** → coller les 4 lignes :
   ```
   https://simplif-ia.fr
   https://www.simplif-ia.fr
   https://simplif-ia.com
   https://www.simplif-ia.com
   ```
4. (Si l'API doit être exposée) Ajouter aussi :
   ```
   https://api.simplif-ia.fr
   https://api.simplif-ia.com
   ```
5. Clique **Save** puis **Redeploy**
6. Vérifie dans les logs Traefik / Coolify la ligne `certificate obtained successfully`

---

## ✅ Vérification finale *(quand DNS propagé)*

Test en ligne de commande :
```bash
curl -I https://simplif-ia.fr/        # doit renvoyer 200 OK
curl -I https://simplif-ia.com/       # doit renvoyer 200 OK
```

Puis dis-moi "**c'est en ligne**" et je relance un audit Chrome complet :
- Lighthouse (perf, SEO, accessibilité, best-practices)
- Console errors / network failed requests
- Parcours utilisateur sur 5 pages clés (home, tarifs, inscription, factures, pense-maison)
- Rendu mobile vs desktop

---

## 🆘 Si tu bloques sur l'une des étapes

Dis-moi laquelle. Pour l'étape 2 je peux t'aider à retrouver ton registrar à partir d'indices (factures, emails). Pour l'étape 3 je peux te guider clic par clic dans Coolify (capture d'écran si besoin).
