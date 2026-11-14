# AutoHELP

Application automobile en français : comptes privés, carnet d'entretien, échéances et conversations persistantes.
Sans véhicule, réponses détaillées depuis les quarante fiches de FAQ locale. Avec un véhicule, réponses fondées uniquement sur son manuel Dacia exact, reformulées par le modèle configuré et terminées par une ligne Source vérifiée.

## Livraison Docker

Docker Desktop/Engine et Compose 2.24 minimum doivent être démarrés.

```bat
cd C:\Users\SafeyeddineK\Desktop\Projet\livraison
copy .env.example .env
docker compose up --build
```

Ouvrir http://localhost:5000. Dans un second terminal :

```bash
docker compose exec web flask import-manuels --lecture-seule
docker compose exec web flask list-manuels
docker compose exec web flask create-admin
```

Les migrations sont appliquées au démarrage. Aucun compte public ni clé n'est fourni. La FAQ et le carnet fonctionnent sans fournisseur ; les réponses documentaires nécessitent une configuration privée valide. Les huit notices autorisées restent dans `manuels/`, montées en lecture seule, hors Git et hors image. Respecter les droits du constructeur et le cadre de partage autorisé.

SQLite et la clé de session sont conservés dans le volume nommé `autohelp_data`. `docker compose down` arrête l'application sans supprimer ce volume ; ne pas ajouter `-v` si les données doivent être gardées. Le web utilise Gunicorn et un utilisateur non-root. `/health` vérifie la vivacité sans requête base ; `/ready` vérifie la connexion et le schéma.

Le projet source monte `data/manuels/` ; le générateur adapte ce chemin vers `manuels/` dans la livraison. Pour une recette isolée, utiliser un autre nom de projet Compose et un autre PORT, pas les données privées.

## Configuration privée

Toutes les valeurs de `.env.example` sont vides. Copier ce modèle dans `.env` sur chaque poste ; ne jamais partager le fichier renseigné.

| Variables | Utilisation |
| --- | --- |
| SECRET_KEY | Sessions et CSRF ; générée et persistée en local si absente, obligatoire en production |
| DATABASE_URL | SQLite local ; PostgreSQL obligatoire avec APP_ENV=production |
| PORT, APP_ENV | Port 5000 par défaut dans Compose ; environnement local ou production |
| OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL | Configuration du fournisseur prioritaire |
| GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL | Configuration utilisée si OpenAI n'est pas configuré |
| SEARCH_PROVIDER, SEARCH_API_KEY, SEARCH_BASE_URL, AI_API_KEY | Variables historiques, hors du parcours actuel |

Aucun modèle ni URL de fournisseur n'est implicite : renseigner les valeurs disponibles sur votre compte. Recréer web après modification : `docker compose up -d --force-recreate web`. Aucune clé n'est affichée aux utilisateurs ni transmise dans le contexte documentaire.

## Installation locale du source

Python 3.12 ou ultérieur compatible avec les dépendances épinglées. Windows utilise le serveur Flask de développement ; Gunicorn s'exécute sous Linux/Docker.

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate ; Linux/macOS : source .venv/bin/activate
python -m pip install -r requirements.txt
flask --app run db upgrade
flask --app run import-vehicules
flask --app run import-faq
flask --app run run --host 127.0.0.1 --port 5001
```

Sur le poste de développement actuel, l'environnement utilisable est `.work/venv`. L'ancien `.venv` reste conservé en attendant la décision de nettoyage du groupe.

## Véhicules et manuels

Les listes en cascade et leur validation serveur proviennent des PDF Dacia locaux identifiés. Inventaire actuel : Bigster, Duster, Jogger, Logan, Spring 2026 ; Sandero 2021 et 2026 ; Sandero Stepway 2026. Modèle et millésime restent distincts, sans remplacement par un autre document. Les anciens véhicules hors inventaire sont conservés ; `flask lister-vehicules-hors-liste` les affiche sans modification.

Dans le source, placer les PDF autorisés sous `data/manuels/<marque>/<modele>/<annee>/manuel.pdf`. Le nom ou la couverture doivent identifier l'édition ; un dossier d'année ne constitue pas une preuve. Sinon, fournir une provenance officielle vérifiée et liée à l'empreinte du fichier dans `index.json`. Les notices inconnues, corrompues, chiffrées ou sans texte sont signalées, sans OCR automatique.

```bash
flask --app run lister-manuels-dacia
flask --app run import-manuels
flask --app run list-manuels
```

Après remplacement, réimporter. pdfplumber extrait les colonnes et tableaux ; les passages gardent page PDF, page imprimée, chapitre, section et versions. Les passages nécessitant une revue visuelle sont exclus des réponses. La dernière recette documentaire d'octobre consignait 11 892 passages actifs, dont 11 221 utilisables ; ce chiffre n'est pas un nouveau comptage de chaque installation.

## Règles de réponse et limites

- Sans véhicule : `data/faq_generale.json`, quarante réponses de 150 à 300 mots, recherche locale sans API, clôture unique vers un mécanicien. Aucun chiffre technique inventé ni source de manuel.
- Avec véhicule : outil unique `rechercher_manuel(requete)`, lecture seule, véhicule fixé côté serveur, synthèse limitée aux passages retrouvés, références et valeurs contrôlées. Aucune FAQ ni recherche web en remplacement.
- Une réponse documentaire finit par Source avec manuel, page imprimée, page PDF et chapitre/section. Un document ou une pagination absents sont annoncés honnêtement.
- Les consignes de sécurité restent dans le contenu, sans bandeaux répétés. Aucun diagnostic à distance.
- Historique privé après reconnexion ; changer de véhicule écarte les anciens passages du contexte.

Les entretiens enregistrent date, compteur, coût en MAD, notes et échéances saisies. Les états sont future, atteinte, dépassée ou absente ; aucun intervalle constructeur n'est déduit automatiquement. Pas de plaque/VIN ni notification email/SMS.

## Tests, génération et Git

```bash
python -m pytest -q -p no:cacheprovider
python scripts/build_delivery.py
python scripts/verifier_livraison.py
flask --app run evaluer-chatbot --rapport .work/evaluation.md
```

Le générateur vérifie les huit notices et refuse les changements non gérés ou non sauvegardés dans la cible. Pour adopter une copie personnalisée déjà sauvegardée, son option `--backup-archive` exige un ZIP contenant la version exacte de chaque fichier remplacé. Aucun fichier inconnu n'est supprimé automatiquement. La livraison exclut environnements, caches, bases, clés, `.env`, données de comptes et rapports temporaires ; la seule exception PDF est la liste des huit notices autorisées confirmée par l'équipe.

Avant commit :

```bash
git add --all
python scripts/audit_git.py
git diff --cached --check
```

L'audit porte sur les blobs indexés et masque les secrets reconnus. Il ne remplace pas une revue spécialisée. Une sauvegarde privée intégrale a précédé les améliorations du 14 novembre ; elle contient aussi configuration et données locales et ne doit pas être diffusée.

## Documentation et déploiement

- `docs/AMELIORATIONS.md` : tâches et critères de reprise.
- `docs/PLAN_IMPLEMENTATION.md` : architecture et état des phases.
- `docs/CHANGEMENTS.md` : décisions datées.
- `docs/FORMAT_REPONSES.md` : contrat des réponses.
- `docs/recette.md` : résultats réels et limites des vérifications.

La recette factice mesure le protocole, pas l'exactitude d'un vrai modèle. Une relecture automobile humaine reste nécessaire. Le déploiement public nécessite encore hébergement, domaine, HTTPS, PostgreSQL, sauvegardes et recette sur l'environnement final.

## Recette des deux moteurs

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests
docker compose -f docker-compose.test.yml run --rm --no-deps -e AUTOHELP_TEST_DATABASE_URL= tests
```

La première commande utilise PostgreSQL de test ; la seconde SQLite. Le Compose de test n'expose pas PostgreSQL et utilise tmpfs. Sa configuration trust est exclusivement réservée à la recette isolée. AUTOHELP_TEST_DATABASE_URL doit viser une base dédiée finissant par _test ; la fixture efface ses tables entre les tests. Ne jamais pointer vers une base utilisateur.

## Protection contre les abus

Compose démarre Redis sans port hôte et partage les quotas entre workers. Développement natif : mémoire par processus ; production : définir RATELIMIT_STORAGE_URI vers Redis/Redis TLS, stockage mémoire refusé. Connexion : 20 POST/minute/IP ; inscription : 5/heure/IP ; chat : 20/minute/compte. Cinq échecs verrouillent temporairement le compte pendant quinze minutes ; un succès efface les échecs précédents. 429 comporte un message français et Retry-After, JSON pour l'API. Une panne du backend renvoie 503.

LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT et CHAT_RATE_LIMIT règlent les quotas. Ne pas faire confiance aux en-têtes d'adresse d'un proxy non configuré. Référence technique : [configuration Flask-Limiter](https://flask-limiter.readthedocs.io/en/stable/configuration.html).

## HTTPS et proxy

Les sessions expirent après huit heures, sans renouvellement systématique. En production, cookies Secure/HttpOnly/SameSite=Lax et HSTS sont activés. PROXY_HOPS vaut zéro par défaut : aucune confiance dans X-Forwarded-For/Proto. Définir le nombre exact de proxys de confiance uniquement si le réseau interdit l'accès direct à Gunicorn ; le middleware ne transfère pas X-Forwarded-Host. Voir les [consignes Flask sur ProxyFix](https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/) et les [cookies de sécurité Flask](https://flask.palletsprojects.com/en/stable/web-security/).

## Audit des dépendances

Installer requirements-dev.txt pour pip-audit et ruff. Lancer `python -m pip_audit -r requirements.txt` et `python -m pip_audit -r requirements-dev.txt`. Les versions corrigées et les résultats datés sont dans docs/AUDIT_DEPENDANCES.md ; un résultat sans avis connu n'est pas une garantie permanente.

## Intégration continue

Le workflow .github/workflows/ci.yml exécute Ruff, audit des secrets reconnus dans Git, pip-audit, construction de l'image et tests sur SQLite/PostgreSQL. Aucune clé ni PDF réel nécessaire. Les notices synthétiques et l'extrait géométrique permettent la recette ; seules les intégrations optionnelles de PDF locaux sont ignorées sans les documents. Après publication du dépôt sur GitHub par le groupe, un push ou une pull request déclenche la CI.

```bash
python -m ruff check .
python -m ruff format --check .
```

## Benchmark des vrais manuels — annotations en attente

Quatre cents questions (cinquante par notice) sont dans tests/data/evaluation_manuels_reels.json. Cinquante annotations Bigster ont été préparées par relecture assistée et contrôles visuels ciblés ; 350 restent à établir, et une revue humaine des attendus reste requise. Le rappel partiel Bigster est de 25/49 (51,0 %) sur les cas avec information présente ; le cas absent est mesuré séparément (1/1). Aucun score global de qualité n'est revendiqué. La commande `flask --app run evaluer-manuels --partiel --rapport .work/rapport_manuels.md` mesure uniquement les attendus relus, sans appel distant par défaut. Sans --partiel, une trace de revue humaine est exigée pour chaque annotation, avec cinquante cas par notice. Le mode --avec-modele est facultatif et borné par --limite. Guide : docs/EVALUATION_MANUELS.md. À la demande du groupe, les tâches suivantes attendent la validation de ce corpus ; le moteur actuel reste inchangé.

## Revue des passages

Administrateurs : ouvrir /admin/manuels, comparer la page PDF exacte au texte, documenter la décision et valider ou corriger chaque passage séparément. Les réserves ne sont jamais levées automatiquement. Un PDF absent/changé ou une révision périmée empêche la validation. Le journal conserve les empreintes et décisions ; un réimport ne réapplique pas aveuglément les corrections.

La version moteur peut être choisie parmi les marqueurs du manuel exact ; « Je ne sais pas » ne déduit aucune motorisation. Les précisions libres existantes restent compatibles. Un choix explicite alimente le filtrage serveur des variantes.

## Mot de passe oublié

Un opérateur disposant de l’accès au serveur peut lancer `docker compose exec web flask reset-password adresse@example.com`. Le nouveau mot de passe est saisi deux fois sans affichage. Aucun email n’est envoyé ; les sessions précédentes sont révoquées. Ne pas transmettre le mot de passe dans une option de commande ou un journal.
