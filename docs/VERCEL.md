# AutoHELP sur Vercel Hobby, Neon et Upstash

Préparation du 21 novembre 2026. L'utilisateur dispose d'un compte Vercel, d'un projet Neon et d'une base Upstash. Ce guide utilise ces services existants. Le code est préparé ; les secrets doivent être saisis dans le compte et la recette publique reste à effectuer. La disponibilité du plan Hobby et ses quotas sont ceux affichés dans le compte ; aucune gratuité sans limite n'est promise.

## Configuration livrée

- Python 3.12, sélectionné par `.python-version` ; dépendances épinglées dans `requirements.txt`.
- Flask détecté par `vercel.json`, avec l'entrée `run:app` déclarée dans `pyproject.toml`. Vercel fournit le serveur : ni Gunicorn, ni Docker, ni `flask run` à lancer sur l'hébergeur.
- Fonction limitée à soixante secondes ; conserver le budget LLM par défaut de vingt secondes. Pour modifier ce budget, revoir aussi la durée de fonction.
- Instance temporaire dans le dossier système temporaire, au lieu du source en lecture seule ; aucune clé de session, base utilisateur ou donnée durable ne doit dépendre de ce dossier.
- PostgreSQL Neon et Redis TLS Upstash obligatoires en production. Sur Vercel, `NullPool` évite de garder un pool SQLAlchemy par instance inactive ; utiliser l'URL Neon poolée pour le web.
- Aucun import PDF ni migration au démarrage d'une fonction. L'opérateur initialise Neon depuis le PC avec les commandes existantes, avant l'ouverture du site.
- `scripts/build_vercel.py` vérifie les huit SHA-256 des notices et copie uniquement `app/static/` vers `public/static/` pour le CDN Vercel. Les PDF restent dans la fonction, hors de `public/` et derrière les routes protégées de l'application.
- Les caches de build, `.env`, données personnelles et autres PDF sont exclus par `.vercelignore`. Les fichiers utiles à la fonction sont filtrés séparément par `excludeFiles`.

Les huit PDF occupent 151 524 804 octets. Une estimation locale des quarante-neuf wheels Linux CPython 3.12 donne 327 605 738 octets décompressés, soit environ 479 Mo avec les PDF avant code, adaptateur Vercel et éventuel bytecode. Ce n'est pas la taille d'une fonction réellement construite : le runtime Python standard accepte au maximum 500 Mo selon la documentation consultée. Le résultat du build Vercel fait foi ; la marge doit être vérifiée dans ses journaux, sans activer une offre payante pour contourner une erreur.

## 1. Récupérer les connexions déjà créées

Dans **Neon → Connect**, sélectionner le projet, la branche et la base dédiés à AutoHELP :

- Pour le web Vercel : copier la chaîne PostgreSQL avec pooling activé.
- Pour l'initialisation locale : copier la chaîne directe de la **même base**, avec pooling désactivé.
- Conserver `sslmode=require` et les autres paramètres TLS fournis. Le projet accepte `postgresql://` et le convertit en `postgresql+psycopg://`.

Dans **Upstash → Redis → Connect**, récupérer l'URI Redis standard TLS :

```text
rediss://default:MOT_DE_PASSE@HOTE:6379/0
```

Employer le port indiqué dans votre compte. Ne pas utiliser l'URL REST HTTPS à la place. Les identifiants doivent être encodés dans l'URI s'ils contiennent des caractères spéciaux. Ne jamais envoyer ces connexions avec mot de passe dans un message, une capture ou GitHub.

## 2. Importer le dépôt dans Vercel

1. Choisir l'espace personnel et l'offre **Hobby** adaptée à un projet personnel/étudiant non commercial.
2. **Add New → Project → Import Git Repository**, puis sélectionner `KELLAM-Safeyeddine/ProjetGenAI-TXT`, branche `main`.
3. Vérifier **Framework Preset : Flask**, et la racine du dépôt comme **Root Directory**.
4. Laisser les Build/Output Settings par défaut. Le hook `tool.vercel.scripts.build` exécute `python scripts/build_vercel.py` après l'installation des dépendances. Ne pas mettre la commande Gunicorn/Render dans Build Command, et ne pas définir `public/` comme racine d'un site statique.
5. Définir les variables ci-dessous pour **Production** avant de cliquer Deploy. Pour les Preview, utiliser une branche Neon et des secrets distincts si vous souhaitez les activer.

## 3. Variables privées dans Vercel

| Variable | Valeur |
| --- | --- |
| `APP_ENV` | `production` |
| `SECRET_KEY` | Clé privée aléatoire stable d'au moins trente-deux caractères |
| `DATABASE_URL` | Connexion Neon poolée, avec TLS |
| `RATELIMIT_STORAGE_URI` | Connexion Upstash `rediss://…` |
| `PROXY_HOPS` | `1`, pour l'entrée Vercel sans autre proxy/CDN ajouté |
| `LLM_PROVIDER` | `groq` |
| `GROQ_API_KEY` | Une clé privée valide de votre compte |
| `GROQ_MODEL` | L'identifiant du modèle compatible avec les outils utilisé dans votre configuration locale |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| `DATA_CONTROLLER_NAME` | Identité du responsable à valider |
| `DATA_CONTROLLER_CONTACT` | Contact du responsable à valider |

Ne pas recréer `SECRET_KEY` à chaque déploiement : les sessions doivent rester vérifiables. Vercel fournit lui-même `VERCEL=1` ; ne pas recopier ce drapeau dans votre `.env` local. Il active les chemins temporaires et exige `APP_ENV=production`, une clé explicite, PostgreSQL et Redis. L'absence de clé du fournisseur laisse fonctionner la FAQ, mais le dialogue manuel est indisponible.

Pour générer une clé de session dans un terminal privé :

```bash
python -c "import secrets; print(secrets.token_hex(48))"
```

Copier le résultat uniquement dans les variables privées et le fichier opérateur. Une variable modifiée dans Vercel nécessite un nouveau déploiement. Ne pas utiliser de base SQLite ni de quotas en mémoire pour contourner les prérequis de production.

## 4. Initialiser Neon depuis le PC

L'outil `scripts/render_manage.py` est réutilisé pour Neon sur les deux hébergeurs ; son nom est historique. Il n'envoie aucune donnée à Render et n'appelle aucun modèle.

Depuis le projet source sous PowerShell, créer le fichier privé une seule fois, sans écraser un fichier déjà renseigné :

```powershell
cd C:\Users\SafeyeddineK\Desktop\Projet\Projet-GenAIText
Copy-Item .env.example .env.vercel
notepad .env.vercel
```

Renseigner seulement ces champs dans `.env.vercel` ; les valeurs ci-dessous sont des éléments à remplacer :

```dotenv
APP_ENV=production
SECRET_KEY=LA_MEME_CLE_PRIVEE_QUE_DANS_VERCEL
DATABASE_URL=LA_CONNEXION_NEON_DIRECTE_DE_LA_MEME_BASE
RATELIMIT_STORAGE_URI=LA_CONNEXION_REDIS_TLS_UPSTASH
```

Laisser les autres variables vides. Le fichier est ignoré par Git, Docker et Vercel. L'outil empêche la reprise de la base et des clés du `.env` personnel, tout en imposant une cible PostgreSQL et Redis TLS. Les opérations agissent réellement sur la base Neon désignée : employer un projet dédié et prévoir sa sauvegarde.

Sur le poste actuel, utiliser le virtualenv existant :

```powershell
.\.work\venv\Scripts\python.exe scripts/render_manage.py initialiser --env-file .env.vercel
.\.work\venv\Scripts\python.exe scripts/render_manage.py verifier --env-file .env.vercel
.\.work\venv\Scripts\python.exe scripts/render_manage.py creer-admin --env-file .env.vercel
```

Sur un autre PC, utiliser son virtualenv Python 3.12 après installation de `requirements.txt`. L'initialisation applique les migrations et indexe les huit PDF, sans modifier leur manifeste ; l'extraction peut durer plusieurs minutes. Les mots de passe administrateur sont saisis sans affichage. Ne pas exécuter les tests pytest sur la base du site.

## 5. Déployer et vérifier

Cliquer **Deploy**, puis suivre les Build Logs et Runtime Logs. Le build doit annoncer huit notices vérifiées et six ressources statiques pour l'état actuel du source. Utiliser ensuite l'URL **Production** réellement attribuée par Vercel.

1. Vérifier l'accueil, le CSS et les boutons ; `/health` doit répondre 200.
2. Après initialisation de Neon et configuration du fournisseur, `/ready` doit répondre 200. Il ne facture aucun appel de modèle et ne prouve pas qu'un appel Groq a réussi.
3. S'inscrire avec un compte de démonstration, ajouter un véhicule et un entretien.
4. Sans véhicule : demander quand changer les essuie-glaces, réponse FAQ détaillée.
5. Avec Bigster 2026 : demander comment contrôler le niveau d'huile, réponse terminée par une Source vérifiée avec pages et chapitre.
6. Se déconnecter/reconnecter, effectuer un redéploiement, puis vérifier le carnet et l'historique conservés dans Neon.
7. Contrôler les droits avec un second compte et CSRF, puis les quotas des fournisseurs.

Les données sont partagées entre les fonctions par Neon/Upstash, et non par un fichier temporaire. Les caches de recherche peuvent être recréés à froid. Le stockage temporaire n'est jamais une sauvegarde. Le service de sauvegarde Docker ne s'exécute pas ici : organiser des exports PostgreSQL privés et vérifier une restauration avant de collecter de vraies données.

## Diagnostic

| Symptôme | Vérification |
| --- | --- |
| Demande de carte pour un essai Pro | Vérifier l'espace et le plan Hobby ; ne pas souscrire à un essai payant pour cette procédure |
| Fonction dépassant la taille maximale | Activer `VERCEL_ANALYZE_BUILD_OUTPUT=1` dans les variables, redéployer et lire la répartition réelle ; ne pas déclarer le paquet compatible sans ce contrôle |
| Erreur de système de fichiers en lecture seule | Déployer le commit contenant l'adaptation Vercel et vérifier `VERCEL=1`, `APP_ENV=production` |
| CSS/JS absents | Preset Flask, hook de build, présence de `public/static/` généré et absence d'override d'Output Directory |
| Base ou tables absentes | Exécuter l'initialisation PC sur la même base/branche Neon que celle du site |
| Connexion ou inscription en 503 | URI Redis TLS Upstash, droits réseau et quotas ; ne pas coller son URL REST |
| Manuel absent | Vérifier huit PDF au build et passages indexés sur Neon ; aucun autre millésime ne sera utilisé |
| Assistant indisponible | Clé, modèle, URL et quotas du fournisseur ; consulter les journaux sans publier les secrets |
| Réponse interrompue | Budget LLM, durée de fonction, taille des documents et latence à froid |

## Références officielles consultées le 21 novembre 2026

- [Flask sur Vercel, entrée et ressources statiques](https://vercel.com/docs/frameworks/backend/flask).
- [Runtime Python et contrôle du paquet](https://vercel.com/docs/functions/runtimes/python).
- [Limites des fonctions et analyse de taille](https://vercel.com/docs/functions/limitations).
- [Offre Hobby](https://vercel.com/docs/plans/hobby).
- [Connexions Neon](https://neon.com/docs/connect/connect-from-any-app).
- [Connexions Redis TLS](https://redis.io/docs/latest/develop/clients/connection-urls/).

La taille et le fonctionnement effectifs du déploiement, la vérification des comptes et les quotas doivent encore être constatés dans Vercel ; ce guide n'affirme pas qu'une URL publique a déjà été créée.

Contrôles locaux exécutés : 427 tests réussis en 124,75 s, Ruff conforme sur 145 fichiers Python. Build des ressources réellement exécuté : huit PDF vérifiés, six fichiers publics générés ; aucun PDF dans `public/`. Les tests de reprise utilisent des fabriques et une base de test locales, pas les comptes cloud. Docker Desktop était arrêté et aucune compilation Vercel authentifiée n'a été effectuée.
