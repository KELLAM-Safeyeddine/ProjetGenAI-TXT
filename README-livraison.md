# Lancer AutoHELP

Prérequis : Docker Desktop/Engine démarré et Docker Compose **2.24 ou plus récent**. Aucun Python à installer sur l’hôte. Le nom du dossier reste `livraison`.

```bat
cd C:\Users\SafeyeddineK\Desktop\Projet\livraison
copy .env.example .env
docker compose up --build
```

Ouvrir **http://localhost:5000**. Le fichier `.env` est facultatif pour démarrer la FAQ et le carnet ; toutes les valeurs du modèle d’exemple sont vides. Aucun compte ni clé API n’est fourni.

### Initialisation documentaire, une fois

Les migrations sont appliquées au démarrage ; les imports historiques ne sont plus automatiques. Indexer les notices fournies une première fois, puis après remplacement d’un PDF :

```bash
docker compose exec web flask import-manuels --lecture-seule
docker compose exec web flask list-manuels
```

L’import complet peut prendre plusieurs minutes. L’option conserve les PDF et leur manifeste sur le montage en lecture seule ; l’index est écrit dans la base SQLite persistante.

### Administrateur, arrêt et vérifications

```bash
docker compose exec web flask create-admin
docker compose down
```

La création demande des identifiants privés et un mot de passe masqué. `down` conserve le volume `autohelp_data`, qui contient base et clé de session générée ; éviter `down -v` pour garder les données.

```bash
docker build -t autohelp .
docker compose exec web python -m pytest -q -p no:cacheprovider
```

`/health` vérifie le serveur sans accès base ; `/ready` exige aussi un index utilisable et la configuration du fournisseur (sinon 503 attendu). Gunicorn tourne avec un utilisateur non-root. SQLite convient au partage local ; le Compose de production autonome PostgreSQL/Redis/Caddy et la sauvegarde sont préparés dans docs/DEPLOIEMENT.md ; domaine, hébergement et recette Internet restent à fournir.

### Manuels

Les huit notices Dacia validées sont fournies dans **`manuels/`**, avec `index.json` : Bigster, Duster, Jogger, Logan et Spring 2026, Sandero 2021/2026 et Sandero Stepway 2026. Elles restent **protégées par les droits du constructeur et ne doivent pas être redistribuées en dehors du cadre autorisé**. La copie générée `livraison/` reste hors Git ; depuis le 20 novembre 2026, les huit PDF du source sont versionnés uniquement sous `data/manuels/dacia/`, avec empreintes contrôlées. Les PDF restent exclus de l’image et montés en lecture seule à l’exécution.

Pour remplacer ou ajouter un document dans ce périmètre, arrêter le service, placer le PDF dans `manuels/dacia/<modele>/<annee>/manuel.pdf`, puis mettre à jour sa provenance et sa preuve d’identité dans `manuels/index.json`. Une année de dossier seule ne prouve pas la version ; un changement de fichier invalide l’ancienne empreinte. Après validation de l’édition, relancer le service et l’import ci-dessus. Ne pas emprunter un PDF d’un autre modèle ou d’une autre année.

### Modèle et limites

Sans véhicule, la FAQ fonctionne sans clé. Pour les réponses sourcées du manuel, renseigner dans le `.env` privé les trois variables `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`, ou leurs équivalents `GROQ_*`, puis `docker compose up -d --force-recreate web`. LLM_PROVIDER=auto conserve la priorité OpenAI ; openai/groq permettent un choix explicite, none désactive le dialogue documentaire. Ne jamais partager le `.env` ni utiliser une clé réelle pendant les tests unitaires.

Les passages incertains restent bloqués, une notice absente n’est jamais remplacée et une relecture professionnelle reste nécessaire. Les résultats réellement obtenus, dont les vérifications Docker possibles ou non, figurent dans [docs/RAPPORT_LIVRAISON.md](docs/RAPPORT_LIVRAISON.md).
