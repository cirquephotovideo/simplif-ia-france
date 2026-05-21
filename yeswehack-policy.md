# Bug Bounty Policy · Simplif'IA France

Programme officiel sur **YesWeHack** : https://yeswehack.com/programs/simplif-ia-france

## Scope (in-scope)

### Production
- `https://simplif-ia.fr` et tous ses sous-domaines
- `https://api.simplif-ia.fr` (API REST)
- `https://app.simplif-ia.fr` (espace utilisateur)
- `https://admin.simplif-ia.fr` (back-office)
- Mobile apps (iOS / Android) quand publiées

### Out of scope
- Self-hosted instances Coolify (51.75.31.123:8000)
- Environments staging
- Third-party services (Stripe, OVH, AR24, FranceConnect)
- Social engineering, phishing employees
- Physical attacks
- DoS / DDoS / volumetric attacks
- Reports automatisés sans PoC

## Vulnerabilities · barème indicatif

| Sévérité | CVSS 3.1 | Récompense |
|----------|----------|------------|
| Critical | 9.0 – 10.0 | 2 500 € – 5 000 € |
| High     | 7.0 – 8.9  | 800 € – 2 500 € |
| Medium   | 4.0 – 6.9  | 200 € – 800 €   |
| Low      | 0.1 – 3.9  | 50 € – 200 €    |
| Informational | — | Hall of Fame |

### Multiplicateurs
- × 2 si exploit fonctionnel fourni
- × 1.5 si chain attack démontré
- × 0.5 si dup, si déjà signalé < 7 jours
- × 0 si rapport sans PoC ou findings d'outils auto bruts

## Bounty hunt rules

1. **Aucun accès aux données utilisateurs réelles.** Créez vos propres comptes de test (5 max).
2. **Aucune dégradation de service.** Pas de bruteforce > 5 req/s, pas de DoS.
3. **Aucune modification/suppression de données utilisateurs.** Si POC requiert un write, créez vos propres ressources.
4. **Signal immédiat** si vous accédez accidentellement à des données tierces (purger sans archive).
5. **Pas de disclosure publique** avant correctif déployé + accord de notre part (90 jours max).
6. **1 rapport = 1 vuln.** Chain reports acceptés mais détaillez chaque maillon.

## SLA

| Action | Délai |
|--------|-------|
| Accusé de réception | < 24 h ouvrées |
| Triage initial | < 72 h |
| Critical patch | < 7 jours |
| High patch | < 30 jours |
| Medium/Low patch | < 90 jours |
| Paiement après triage | < 14 jours |

## Hall of Fame

Tous les chercheurs reportant une vuln valide (sauf demande contraire) sont listés sur https://simplif-ia.fr/securite.html#hall-of-fame avec :
- Pseudonyme ou nom (au choix)
- Mois/année
- Sévérité (Critical/High/Medium/Low)
- Lien profil YesWeHack

## Categories particulièrement appréciées

- **Auth bypass** (toutes formes)
- **Privilege escalation** (user → admin)
- **IDOR** sur /api/vault, /api/demarches
- **RCE** sur backend FastAPI
- **SQLi** (théoriquement impossible avec ORM, prouvez-le sinon)
- **SSRF** sur intégrations api.gouv.fr
- **Crypto flaws** sur le chiffrement coffre-fort
- **JWT** sign/verify issues
- **Stored XSS** sur le front (app.html, admin.html)
- **CSRF** despite middleware (prouvez la bypass)
- **Account takeover** end-to-end

## Categories non rétribuées

- Missing security headers (déjà documenté)
- Email enumeration via login (réponse uniforme appliquée)
- CSP weaknesses sans PoC d'exploit
- Clickjacking sur pages sans state-changing actions
- Best-practices recommendations (use TaskCreate workflow)
- 0day publics sans PoC adapté

## PGP

Clé publique pour rapports chiffrés :
https://simplif-ia.fr/.well-known/pgp-key.txt

Fingerprint : `4F8A 9E2C 3B7D 5F1A 8C0E 6D4B 9A7F 2E5C 1D8B 3A6F` (placeholder à régénérer)

## Contact

- security@simplif-ia.fr (urgent)
- bug-bounty@simplif-ia.fr (triage)
- YesWeHack platform (preferred · audit trail)

Conformité : ce programme respecte la loi française (LPM 2013, RGPD) et la jurisprudence sur la divulgation responsable (Bluetouff, 2014).
