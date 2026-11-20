# AutoHELP — Plan d’implémentation et état du projet

Mise à jour : 20 novembre 2026. Source : Projet-GenAIText ; paquet généré dans le dossier frère livraison. Les décisions historiques restent dans CHANGEMENTS.md, les résultats exacts dans recette.md.

Choix d'hébergement actuel : Render gratuit avec PostgreSQL Neon et Redis TLS Upstash (guide RENDER.md). Blueprint Python 3.12, démarrage limité à un worker et administration documentaire depuis le PC, l'offre gratuite n'ayant pas de Shell. L'utilisateur a un compte Render ; les services Neon/Upstash, les secrets et la recette de l'URL publique restent à fournir. La préparation ne déclare pas un site déjà déployé et ne réduit aucune protection existante.

Publication GitHub effectuée le 18 novembre ; [première exécution CI distante réussie](https://github.com/KELLAM-Safeyeddine/ProjetGenAI-TXT/actions/runs/44335669198). Le 20 novembre, huit notices Dacia sont autorisées dans Git par chemins et SHA-256 explicites pour faciliter le clonage sur PythonAnywhere ; les autres PDF, secrets et données locales restent exclus, tous les PDF restent hors image Docker. La procédure Web/WSGI est décrite dans PYTHONANYWHERE.md ; PostgreSQL et Redis restent obligatoires en production, aucun compte PythonAnywhere n'est encore déployé. Le lien de consultation page par page a été retiré de l'assistant, sans changer ses réponses.

## Règles actuelles

- Français ; comptes, véhicules, entretiens et conversations privés.
- Sans véhicule : FAQ locale uniquement, quarante fiches de 150 à 300 mots, sans libellé ni source de manuel ; clôture unique vers un mécanicien.
- Avec véhicule : manuel exact uniquement, lié à marque/modèle/année ; outil rechercher_manuel en lecture seule ; contenu utile puis Source vérifiée avec pages imprimée/PDF, chapitre et section. Aucun relais FAQ/web.
- Les versions mécaniques sont fixées à partir de la question originale et de la motorisation enregistrée côté serveur. API et évaluation utilisent maintenant la même liaison de contexte ; le modèle ne choisit ni véhicule, version ni page.
- Références inconnues et valeurs sans support rejetées. Sécurité dans les phrases utiles, sans bandeaux. Aucun diagnostic à distance.
- CSRF, ORM, propriété, hachage et affichage textuel conservés. Pas de plaque/VIN, entraînement de modèle ou notification email/SMS.

## État des phases initiales

| Phase | État réel |
| --- | --- |
| Connaissances et chatbot | Implémentés ; benchmark réel et relecture professionnelle incomplets |
| Plateforme et données | Comptes, carnet, échéances, migrations et isolation implémentés |
| Intégration | API, historique et formats de réponses implémentés |
| Tests | Campagnes SQLite/PostgreSQL, PDF fictifs/réels et recette HTTP exécutées ; détails datés dans recette.md |
| Livraison | Générateur réconcilié, Docker local validé, huit notices conservées hors image/Git |
| Déploiement public | Non réalisé : hébergement, domaine, HTTPS et recette publique restent à fournir |

## Améliorations du 14 novembre

| Tâche | État |
| --- | --- |
| P0-1 Git | Validé : socle commité, exclusions et audit des blobs indexés |
| P0-2 Docker | Validé : image construite, non-root, migrations, santé, import et persistance |
| P0-3 Deux bases | Validé : suite complète sur SQLite/PostgreSQL et migrations PostgreSQL |
| P0-4 Abus | Validé : quotas, verrouillage temporaire, Redis partagé et panne fermée |
| P0-5 Sessions/proxy | Validé : cookies bornés, CSP stricte, confiance proxy explicite ; navigateur sans violation CSP |
| P0-6 Dépendances | Validé : Flask/pytest/pypdf corrigés ; audits runtime/dev sans avis connu à la date de recette |
| P1-7 CI | Workflow publié ; première exécution GitHub Actions du 18 novembre réussie |
| P1-8 Benchmark réel | Outil et 400 questions disponibles ; 50 annotations Bigster assistées, 350 à établir ; revue humaine attendue, corpus non validé |
| P1-9 Recherche hybride | Prototype BM25 comparé, non activé : 32/49 contre 25/49 sur le lot Bigster, avec une régression ; validation complète attendue |
| P1-10 Revue admin | Réserves paginées, rendu de l'édition exacte, correction/validation et journal ; concurrence et droits testés |
| P1-11 Motorisation | Choix issus du manuel exact, option inconnue et compatibilité avec les anciennes précisions libres |
| P1-12 Mot de passe | CLI opérateur, saisie masquée, réponse neutre et révocation des sessions précédentes |
| P1-13 Observabilité | Journaux JSON sur liste blanche et identifiant de requête ; health distinct de ready ; Sentry non activé |
| P1-14 Dialogue | Choix explicite du fournisseur, budgets bornés, tentatives limitées et tests d'injection ; Groq mesuré, OpenAI non configuré/non mesuré |
| P1-15 Retours | Utile/pas utile, commentaire privé, reprise dans l'historique et export CSV administrateur |
| P2-16 Données personnelles | Confidentialité/conditions, export privé et purge configurable avec simulation ; validation juridique à fournir avant publication |
| P2-17 Échéances | Échéances proches et compteur rapide protégés ; seuils d'affichage configurables, sans périodicité constructeur inventée |
| P2-18 Conversations | Renommer/supprimer, nouvelle conversation et progression accessible ; recette mobile/clavier effectuée |
| P2-19 Archives | Modèles/commandes isolés sous legacy et export compressé ; suppression des archives et de l'ancien environnement non exécutée sans accord du groupe |
| P2-20 Performance | Cache borné par worker/identité/édition, pagination, profil sur le corpus réel et charge avec modèle factice |
| P2-21 Sauvegarde | Service PostgreSQL planifié avec rotation ; restauration isolée vérifiée sur les onze tables, connexion et historique compris |
| P2-22 Production | Compose PostgreSQL/Redis/Caddy autonome et HTTPS local testés ; hébergeur, domaine et recette Internet restent à fournir |

Le détail des vingt-deux propositions est dans AMELIORATIONS.md. L'équipe a confirmé de conserver les huit PDF dans livraison/manuels/, malgré la proposition initiale sans PDF. Aucun autre écart au contrat métier n'est introduit.

## Architecture et données

Flask, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate/Alembic, Bootstrap local et JavaScript fetch. pdfplumber/pypdf pour les documents ; normalisation/synonymes, mots-clés, TF-IDF et cosinus pour la recherche. Transport OpenAI/Groq isolé dans llm_service.py ; aucun accès direct du modèle à l'ORM ou aux fichiers.

Tables : users, vehicles, maintenance, conversations, messages, manuel_passages, manual_reviews et feedback ; archives faq, vehicle_catalog et web_passages conservées. Aucun nettoyage destructif de ces archives ni de l'ancien environnement cassé n'est effectué.

SQLite local ; PostgreSQL obligatoire en APP_ENV=production. Compose local : SQLite dans le volume autohelp_data et Redis sans port hôte. Compose de test : PostgreSQL dédié autohelp_test en tmpfs, sans port public ; configuration trust exclusivement réservée à cette recette isolée.

Les migrations sont appliquées au démarrage ; les imports historiques ne sont plus automatiques. Les manuels sont importés explicitement. Aucun compte public n'est créé. create-admin reste une commande explicite avec mot de passe masqué.

## Véhicules et inventaire documentaire

Le formulaire et la validation serveur utilisent les PDF Dacia identifiés localement. Une année de dossier ne prouve pas une édition : couverture/nom ou provenance officielle liée au SHA-256 exigés. Les anciens véhicules hors inventaire sont conservés et listables, sans substitution de manuel.

| Marque | Modèle | Année |
| --- | --- | ---: |
| Dacia | Bigster | 2026 |
| Dacia | Duster | 2026 |
| Dacia | Jogger | 2026 |
| Dacia | Logan | 2026 |
| Dacia | Sandero | 2021 |
| Dacia | Sandero | 2026 |
| Dacia | Sandero Stepway | 2026 |
| Dacia | Spring | 2026 |

Huit fichiers, sept contenus distincts ; les notices communes explicitement validées gardent leurs identités séparées. Dernier import source consigné en octobre : 11 892 passages actifs, dont 671 bloqués et 11 221 utilisables ; ce n'est pas un nouveau comptage de chaque installation.

Extraction géométrique par colonnes, tableaux et avertissements atomiques ; pages imprimées détectées dans le pied de page, sans décalage universel. Passages vers 700 caractères avec chevauchement ; renvois conservés en métadonnées, mots coupés recollés. Aucun OCR automatique. Les réserves visuelles restent bloquées.

Les entretiens conservent date, compteur, coût en MAD, notes et échéances saisies. États future/atteinte/dépassée/absente ; aucune fréquence constructeur déduite automatiquement.

## Sécurité et configuration

- POST connexion 20/minute/IP, inscription 5/heure/IP, chat 20/minute/compte ; quotas configurables.
- Cinq échecs : verrouillage de quinze minutes, identique pour compte inconnu ; succès : compteurs remis à zéro. Clés IP/compte HMACisées.
- Redis partagé en Compose et obligatoire en production ; mémoire pour le développement natif. Pas de bascule silencieuse sans protection ; panne renvoyée en 503.
- Sessions de huit heures, sans renouvellement systématique ; cookies HttpOnly/SameSite=Lax, Secure en production, paramètres remember définis.
- CSP sans scripts/styles inline autorisés, frame-ancestors none, object-src none, nosniff, Referrer-Policy et HSTS sous HTTPS.
- PROXY_HOPS=0 par défaut. Déclarer le nombre exact de proxys seulement si le réseau empêche de les contourner ; adresse et protocole transférés, jamais l'hôte.
- LLM_PROVIDER=auto : OpenAI prioritaire si configuré, sinon Groq ; openai/groq imposent le fournisseur sans bascule silencieuse ; none désactive le dialogue documentaire. Clés, modèles et URL privés. Sans configuration utilisable : indisponibilité neutre sur les manuels ; FAQ et carnet accessibles.

Les budgets LLM sont configurables et bornés : timeout 1–30 secondes/appel, budget total 5–90 secondes, 2–8 tours, 1–3 tentatives, contexte 8 000–48 000 caractères. Défauts conservés : 5 secondes/appel, 20 secondes au total, quatre tours, deux tentatives, 28 000 caractères. Les délais navigateur/Gunicorn suivent le budget. Mesure réelle unique Groq : 7,344 s, deux appels, Source vérifiée ; OpenAI non mesuré faute de configuration. Les journaux JSON excluent contenu privé et secrets.

## Benchmark et critères de reprise

`tests/data/evaluation_manuels_reels.json` : cinquante questions par notice, soit quatre cents cas. Cinquante annotations Bigster sont préparées après lecture indépendante et contrôles visuels ciblés ; 350 brouillons sont exclus des mesures. Mesure partielle : rappel top trois 25/49 (51,0 %) sur les cas avec réponse présente, absence de passage 1/1 pour le tarif local non documenté. Les attendus ne sont pas ajustés au classement. Aucune génération réelle mesurée, aucun score global de qualité. La relecture assistée par Codex ne remplace pas la validation automobile professionnelle.

Compléter réponses attendues, pages, variantes, valeurs sourcées et preuve de relecture sans changer les questions pour améliorer le score. Le CLI exige une édition SHA-256 identique et cinquante annotations vérifiées par manuel, avec trace explicite de revue humaine, avant de déclarer le corpus prêt. L’empreinte du jeu figure dans le rapport ; les mesures numériques distinguent km/h de km et conservent les décimales et bornes de plages. Génération réelle facultative et limitée, jamais activée par défaut. Guide : EVALUATION_MANUELS.md.

La demande du groupe « continue tous » permet désormais les tâches indépendantes pendant la revue du corpus ; l’adoption d’un moteur reste conditionnée à des mesures fiables. Le moteur TF-IDF actif reste inchangé. Le prototype local BM25 est disponible uniquement dans le comparateur, sans accès depuis l'API ou le modèle ; aucun embedding ajouté. Voir COMPARAISON_RECHERCHE.md.

## Validation intégrée et éléments externes

Le 14 novembre : 402 tests sur SQLite (221,64 s) et 402 sur PostgreSQL (79,66 s), sans échec ni test ignoré ; Ruff lint/format conforme (137 fichiers Python). Migrations PostgreSQL upgrade/check/downgrade/upgrade/check réussies. Le jeu de protocole conserve 78/78 comportements avec modèle factice, sans mesurer la qualité d'un vrai fournisseur. Résultats Docker/livraison, charge, restauration et HTTPS dans recette.md.

Les fonctions indépendantes des tâches 10 à 22 sont implémentées. Restent la préparation/revue humaine du corpus (350 attendus à établir, puis revue de tous les attendus), la décision sur le moteur, la mesure OpenAI si une configuration est fournie, la décision de supprimer les archives, la validation des textes/formalités CNDP et le déploiement sur un hébergement choisi. La publication GitHub et la première exécution distante sont validées séparément ; les autres points ne sont pas présentés comme déjà validés.

## Livraison et commandes

Le générateur inclut code, migrations, données factuelles/FAQ, tests, documentation, CI, configuration d'exemple et huit notices autorisées. Pas de .env réel, clé, base, compte, cache, environnement ou rapport temporaire. Il refuse les fichiers inconnus et les modifications locales non sauvegardées ; une adoption requiert une archive ZIP contenant exactement les fichiers remplacés.

```bat
cd C:\Users\SafeyeddineK\Desktop\Projet\livraison
copy .env.example .env
docker compose up --build
```

Accès : http://localhost:5000. Puis :

```bash
docker compose exec web flask import-manuels --lecture-seule
docker compose exec web flask create-admin
docker compose exec web flask evaluer-manuels --partiel --rapport /app/instance/rapport_manuels.md
```

Recette des bases, depuis le source :

```bash
docker compose -f docker-compose.test.yml up -d db-test
docker compose -f docker-compose.test.yml run --rm tests
docker compose -f docker-compose.test.yml run --rm --no-deps -e AUTOHELP_TEST_DATABASE_URL= tests
```

Génération/audit : `python scripts/build_delivery.py`, `python scripts/verifier_livraison.py`, `python scripts/audit_git.py`. Les résultats précis et les limites des tests restent dans recette.md ; l'état de la publication GitHub et du déploiement public n'est pas inventé.
