# Production préparée, hébergement à choisir

Le Compose local reste SQLite/Redis sur localhost:5000. **docker-compose.production.yml est autonome** : ne pas le fusionner avec le Compose local. Il utilise PostgreSQL persistant, Redis privé, Gunicorn non-root, Caddy et un service de sauvegarde. Seul Caddy publie les ports 80/443 ; le web n’a aucun port hôte et PROXY_HOPS=1 correspond à ce proxy unique. Ne pas ajouter un CDN/proxy supplémentaire sans revoir cette confiance et le réseau.

## Préparer sur le serveur choisi

Le groupe n’a pas encore fourni de domaine/hébergeur. Aucun service public, DNS ou certificat public n’est créé par cette tâche.

1. Copier la livraison autorisée et conserver ses notices dans manuels/. Vérifier les droits de partage.
2. Construire `docker build -t autohelp .`.
3. Sur un dossier sans configuration privée préexistante : `python scripts/init_production.py --domain votre.domaine`. Cette assistance génère une clé de session et un mot de passe PostgreSQL distincts, sans les afficher ni écraser un fichier. Si Python n’est pas installé sur un hôte Linux, utiliser l’image :

```bash
docker run --rm --user "$(id -u):$(id -g)" --mount type=bind,source="$PWD",target=/workspace --entrypoint python autohelp scripts/init_production.py --directory /workspace --domain votre.domaine
```

4. Compléter le .env privé : identité/contact du responsable, durée de conservation décidée et fournisseur/modèle/URL. Les clés de modèle restent facultatives au démarrage ; leur absence rend le dialogue manuel indisponible et /ready en 503, sans empêcher /health ou la FAQ.
5. Pointer le DNS du domaine vers le serveur et rendre 80/443 accessibles à Caddy. Lancer :

```bash
docker compose -f docker-compose.production.yml up --build -d
docker compose -f docker-compose.production.yml exec web flask import-manuels --lecture-seule
docker compose -f docker-compose.production.yml exec web flask create-admin
docker compose -f docker-compose.production.yml logs --tail 20 backup
```

Les secrets générés restent dans .env et secrets/, ignorés par Git, Docker et la livraison générée. Sous Linux, .env et le répertoire secrets sont privés sur l’hôte ; le fichier mot de passe est lisible dans les conteneurs via son montage individuel. Ne pas modifier ces droits sans vérifier les UID du web, de PostgreSQL et du service de sauvegarde.

## Recette locale réellement exécutée le 14 novembre 2026

Projet Docker isolé autohelp-production-qa, domaine localhost et ports de recette 5080/5443. PostgreSQL, Redis, web, Caddy et sauvegarde démarrés ; migrations appliquées. Certificat **local** émis par Caddy, puis vérifié par le client de recette avec son autorité locale (aucune installation de confiance sur Windows). Accueil, health, confidentialité et conditions : 200 ; HSTS présent ; /ready : 503 attendu sans fournisseur. Import réel Bigster complet, création CLI d’un administrateur éphémère, CSRF actif et réponse avec Source vérifiée via transport factice réussis. Le compte temporaire est supprimé.

Parcours HTTP réel sur HTTPS : inscription, véhicule, entretien, chat, déconnexion/reconnexion et historique conservé ; compte de recette supprimé ensuite. Sauvegarde/restauration réelle des sept tables comparées : voir SAUVEGARDE_POSTGRESQL.md. Ces contrôles ne valent pas une recette Internet publique ni une mesure de qualité du modèle.

Avant ouverture publique : vérifier la conformité et les transferts avec le responsable, faire relire les réponses et le corpus, valider les dépendances/images à la date de déploiement, tester les droits, la persistance après redémarrage, les sauvegardes et la restauration, puis effectuer la même recette depuis l’URL publique.

Arrêter sans supprimer les volumes : `docker compose -f docker-compose.production.yml down`. Sauvegardes et base demeurent privées ; ne pas ajouter -v pour conserver les données.

Références officielles consultées le 14 novembre 2026 : [HTTPS Caddy](https://caddyserver.com/docs/automatic-https), [reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [version 2.11.9](https://github.com/caddyserver/caddy/releases/tag/v2.11.9).
