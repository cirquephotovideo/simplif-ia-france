# 🛠 Plan de remise en ligne de la prod — Simplif'IA France

> Diagnostic effectué le 20/05/2026. Le site est actuellement **hors ligne** depuis le web (les deux domaines retournent une erreur SSL/serveur).

---

## 🔍 Diagnostic technique

### État actuel des domaines

| Domaine | IP DNS actuelle | Statut | Problème |
|---|---|---|---|
| `simplif-ia.fr` | `217.160.0.226` | ❌ Page parking IONOS | Pas de certificat SSL valide, redirige en HTTP vers `simplif-ia.com` |
| `simplif-ia.com` | `34.111.179.208` (Google Cloud) | ❌ TLS handshake échoue | Pas de serveur fonctionnel à cette IP |

### Serveur applicatif

| Élément | État |
|---|---|
| Serveur Coolify (`51.75.31.123`, OVH) | ✅ En ligne, ports 80/443/8000 ouverts |
| Traefik (reverse proxy de Coolify) | ✅ Répond — mais **404** pour `simplif-ia.com` et `simplif-ia.fr` (pas de route configurée) |
| UI Coolify (`http://51.75.31.123:8000`) | ✅ Accessible (page de login) |

### Cause racine

**Les enregistrements DNS pointent vers les mauvaises IPs**, et Coolify n'a pas de domaine configuré pour cette application. Il faut :

1. Mettre à jour les A-records pour pointer vers `51.75.31.123`
2. Configurer le domaine dans Coolify pour que Traefik route correctement
3. Laisser Coolify émettre le certificat Let's Encrypt automatiquement

---

## ✅ Étapes pour remettre la prod en ligne

### Étape 1 — Mettre à jour les DNS

#### a) `simplif-ia.fr` chez **IONOS** (le domaine est managé chez IONOS d'après les MX records `mx00.ionos.fr` / `mx01.ionos.fr`)

1. Se connecter à `https://login.ionos.fr/`
2. Domaines & SSL → `simplif-ia.fr` → **Modifier DNS**
3. Supprimer les A-records existants pointant vers `217.160.0.226`
4. Créer ces A-records :

   | Type | Nom | Valeur | TTL |
   |---|---|---|---|
   | A | `@` | `51.75.31.123` | 3600 |
   | A | `www` | `51.75.31.123` | 3600 |
   | A | `api` | `51.75.31.123` | 3600 |

5. Vérifier qu'il n'y a **pas** de redirection HTTP active vers `simplif-ia.com` (sinon la supprimer)

#### b) `simplif-ia.com` — où est-il managé ?

L'IP actuelle (`34.111.179.208`) est une IP Google Cloud Load Balancer. Le domaine est probablement géré soit chez :
- **Google Domains / Squarespace Domains** (si tu as acheté via Google)
- **OVH, Cloudflare, Gandi…** selon où tu l'as enregistré

À faire :
1. Identifier le registrar dans tes emails (recherche "simplif-ia.com")
2. Connecter-toi au registrar
3. Mêmes A-records que ci-dessus (`@`, `www`, `api` → `51.75.31.123`)

> ⚠️ Si tu as une zone DNS chez **Cloudflare**, vérifier que le mode est "DNS only" (nuage gris) **avant** que Coolify ait émis son certificat Let's Encrypt. Sinon le challenge HTTP-01 échouera.

### Étape 2 — Configurer le domaine dans Coolify

1. Ouvrir `http://51.75.31.123:8000/`
2. Login → ouvrir l'application Simplif'IA France
3. Onglet **General** → champ **Domains**, ajouter :
   ```
   https://simplif-ia.fr
   https://www.simplif-ia.fr
   https://simplif-ia.com
   https://www.simplif-ia.com
   ```
4. Onglet **Configuration** → s'assurer que le service `frontend` est bien exposé (port `80` interne mappé)
5. Cliquer **Redeploy**
6. Vérifier dans les logs Traefik que les certificats Let's Encrypt sont émis (`certificate obtained successfully`)

### Étape 3 — Vérification

Après propagation DNS (≈ 5-30 min) :

```bash
# Doit renvoyer 200 OK
curl -I https://simplif-ia.fr/
curl -I https://simplif-ia.com/

# Doit montrer un cert Let's Encrypt valide
echo | openssl s_client -servername simplif-ia.fr -connect simplif-ia.fr:443 2>&1 | grep "subject="
```

Et ouvrir dans Chrome : `https://simplif-ia.fr` et `https://simplif-ia.com` doivent afficher la home.

---

## 🚧 Bonus — Ajouter les labels Traefik directement dans le repo

Si Coolify n'ajoute pas automatiquement les bonnes routes, tu peux forcer les labels dans `docker-compose.yml` :

```yaml
  frontend:
    # … existant …
    labels:
      - "coolify.managed=true"
      - "traefik.enable=true"
      - "traefik.http.routers.simplif-frontend.rule=Host(`simplif-ia.fr`) || Host(`www.simplif-ia.fr`) || Host(`simplif-ia.com`) || Host(`www.simplif-ia.com`)"
      - "traefik.http.routers.simplif-frontend.entrypoints=https"
      - "traefik.http.routers.simplif-frontend.tls=true"
      - "traefik.http.routers.simplif-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.services.simplif-frontend.loadbalancer.server.port=80"

  backend:
    # … existant …
    labels:
      - "coolify.managed=true"
      - "traefik.enable=true"
      - "traefik.http.routers.simplif-backend.rule=Host(`api.simplif-ia.fr`) || Host(`api.simplif-ia.com`)"
      - "traefik.http.routers.simplif-backend.entrypoints=https"
      - "traefik.http.routers.simplif-backend.tls=true"
      - "traefik.http.routers.simplif-backend.tls.certresolver=letsencrypt"
      - "traefik.http.services.simplif-backend.loadbalancer.server.port=8000"
```

---

## ❓ Ce que JE ne peux PAS faire à ta place

- Modifier les enregistrements DNS chez IONOS / le registrar de .com (mot de passe / 2FA requis)
- Me logger dans l'UI Coolify (login requis)
- Émettre un certificat Let's Encrypt (déclenché par Traefik après que le DNS pointe correctement)

## ✅ Ce que je PEUX faire pendant que tu fais ça

1. Améliorer les labels Traefik dans `docker-compose.yml` (proposé ci-dessus)
2. Pré-construire toutes les améliorations frontend (design, SEO, copywriting) → quand la prod sera remontée, le déploiement bénéficiera de tout d'un coup
3. Vérifier toutes les pages en local avec Chrome (tu lances le `Lancer-Simplif-IA.command`)

---

*Document généré automatiquement par Claude — 20/05/2026.*
