# Cache et recette de charge

14 novembre 2026. Le classement actif reste identique. Cache LRU de huit index TF-IDF par processus/worker, clé par identité exacte, édition et documents. Verrou de construction, remplacement par nouvelle clé après correction, aucune mise en commun de références entre véhicules. Le cache n'est pas partagé entre workers ; chaque worker paye son chargement initial.

`flask profiler-index` ne consulte aucun modèle. Mesure sur les 11 892 passages actifs réels dans un conteneur isolé, sans compte/message et sans réseau : huit index construits, huit réutilisations, 13,991 s sous tracemalloc, 69,72 Mio Python retenus, pic Python 75,90 Mio, pic du processus 257 240 Kio (environ 251 Mio). Inclut bibliothèques et chargement initial ; ne garantit pas la mémoire de toutes les charges ou le débit d'un fournisseur. Deux workers gardent deux caches distincts.

Les listes de conversations sont paginées par cinquante avec aperçu SQL sans charger tous les messages ; les messages sont repris par lots de cent, retours préchargés. Les curseurs restent soumis au filtre propriétaire et l'interface permet de charger les pages précédentes.

## Charge de protocole, exclusivement sur données fictives

L'image est construite depuis le source. `scripts.load_app` refuse de démarrer sans AUTOHELP_LOAD_TEST=1, crée une base temporaire et un petit PDF fictif, utilise un transport modèle simulé et conserve CSRF/authentification. Ne jamais utiliser ce serveur de recette pour héberger les données réelles.

```bash
docker build -t autohelp .
docker network create autohelp-charge
docker run -d --name autohelp-charge-qa --network autohelp-charge --network-alias charge -e AUTOHELP_LOAD_TEST=1 --entrypoint gunicorn autohelp --bind 0.0.0.0:5000 --workers 1 scripts.load_app:app
docker run --rm --network autohelp-charge --mount type=bind,source=<chemin-absolu>/scripts/load_chat.js,target=/scripts/load_chat.js,readonly grafana/k6:2.4.0 run /scripts/load_chat.js
docker stop autohelp-charge-qa
docker rm autohelp-charge-qa
docker network rm autohelp-charge
```

Résultat réel : cinq utilisateurs virtuels, quinze secondes, 335 réponses documentaires factices vérifiées sur 335, 355 requêtes HTTP, aucune erreur HTTP, p95 HTTP 39,97 ms. Les cookies persistent entre les itérations pour reproduire une session de navigateur. Cela ne mesure pas la latence/qualité d'un vrai modèle, ni la charge du corpus complet : le profil mémoire réel et la charge de protocole sont deux recettes distinctes.

Documentation officielle et version k6 vérifiées le 14 novembre : [exécution](https://grafana.com/docs/k6/latest/get-started/running-k6/), [version 2.4.0](https://github.com/grafana/k6/releases/tag/v2.4.0).
