# AutoHELP — Plan d’implémentation et état du projet

Mise à jour : 14 novembre 2026. Source : Projet-GenAIText ; paquet généré dans le dossier frère livraison. Les décisions historiques restent dans CHANGEMENTS.md, les résultats exacts dans recette.md.

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
| P1-7 CI | Workflow ajouté et vérifié localement ; exécution distante à constater après publication du dépôt |
| P1-8 Benchmark réel | Outil et 400 questions disponibles ; une annotation relue visuellement, 399 en attente ; corpus non validé |
| P1-9 Recherche hybride | Non entamée : aucune adoption sans benchmark vérifié et gain démontré |
| P1-10 à P2-22 | Non entamées ; ordre strict confirmé par le groupe, attendre les annotations |

Le détail des vingt-deux propositions est dans AMELIORATIONS.md. L'équipe a confirmé de conserver les huit PDF dans livraison/manuels/, malgré la proposition initiale sans PDF. Aucun autre écart au contrat métier n'est introduit.

## Architecture et données

Flask, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate/Alembic, Bootstrap local et JavaScript fetch. pdfplumber/pypdf pour les documents ; normalisation/synonymes, mots-clés, TF-IDF et cosinus pour la recherche. Transport OpenAI/Groq isolé dans llm_service.py ; aucun accès direct du modèle à l'ORM ou aux fichiers.

Tables : users, vehicles, maintenance, conversations, messages et manuel_passages ; archives faq, vehicle_catalog et web_passages conservées. Aucun nettoyage destructif de ces archives ni de l'ancien environnement cassé n'est effectué.

SQLite local ; PostgreSQL obligatoire en APP_ENV=production. Compose local : SQLite dans le volume autohelp_data et Redis sans port hôte. Compose de test : PostgreSQL dédié autohelp_test en tmpfs, sans port public ; configuration trust exclusivement réservée à cette recette isolée.

Les migrations et les imports historiques sont appliqués au démarrage ; aucun compte public n'est créé. create-admin reste une commande explicite avec mot de passe masqué.

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
- OpenAI prioritaire si configuré, sinon Groq ; clés, modèles et URL privés. Sans configuration utilisable : indisponibilité neutre sur les manuels ; FAQ et carnet accessibles.

Les budgets LLM restent ceux d'avant : timeout 5 secondes/appel, budget 20 secondes, quatre tours, contexte borné. Leur configuration avancée et les journaux structurés appartiennent aux tâches futures, non implémentées.

## Benchmark et critères de reprise

`tests/data/evaluation_manuels_reels.json` : cinquante questions par notice, soit quatre cents cas. Une annotation Bigster a été relue sur une page rendue ; page retrouvée (1/1), sans score global de qualité. Les trois cent quatre-vingt-dix-neuf brouillons sont exclus des mesures. La relecture assistée par Codex ne remplace pas la validation automobile professionnelle.

Compléter réponses attendues, pages, variantes, valeurs sourcées et preuve de relecture sans changer les questions pour améliorer le score. Le CLI exige une édition SHA-256 identique et cinquante annotations vérifiées par manuel avant de déclarer le corpus prêt. Génération réelle facultative et limitée, jamais activée par défaut. Guide : EVALUATION_MANUELS.md.

L'équipe demande d'attendre cette validation avant toute tâche suivante, y compris les améliorations indépendantes. Le moteur TF-IDF actuel reste inchangé ; aucun embedding ni BM25 ajouté.

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
