# Déployer AutoHELP sur PythonAnywhere

Procédure préparée le 20 novembre 2026 à partir de la documentation officielle. Elle n'a pas été exécutée sur un compte PythonAnywhere. Le déploiement nécessite l'accès au compte et ses services ; publier sur GitHub ne lance pas l'application.

## Prérequis

- Une image système PythonAnywhere proposant Python 3.12, pour la console et l'application Web.
- Un compte payant permettant les connexions aux services externes, un PostgreSQL disponible (option PythonAnywhere ou service externe), et un Redis externe compatible avec les commandes de Flask-Limiter.
- Assez d'espace disque pour les dépendances, l'index et les huit PDF (151 524 804 octets au total).
- Une configuration privée du fournisseur LLM pour les réponses issues des manuels. La FAQ générale fonctionne sans clé.

La configuration actuelle refuse SQLite et les quotas en mémoire en production. Ne pas contourner cette protection en exposant le mode local ; Docker Compose sur VPS demeure une autre solution pour héberger tous les services ensemble.

## Cloner et installer

Dans une console Bash du compte :

```bash
git clone https://github.com/KELLAM-Safeyeddine/ProjetGenAI-TXT.git
cd ~/ProjetGenAI-TXT
mkvirtualenv --python=/usr/bin/python3.12 autohelp
python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

Les huit notices sont déjà dans `data/manuels/dacia/`. Leurs chemins, tailles et empreintes sont listés dans `config/manuels_versionnes.json`. Les autres marques ne sont pas distribuées. Le projet ne fournit aucun compte, clé API ou base utilisateur.

## Configurer en privé

Modifier `.env` dans le compte, sans le commiter :

| Variable | Valeur à préparer |
| --- | --- |
| `APP_ENV` | `production` |
| `SECRET_KEY` | Une clé aléatoire privée d'au moins trente-deux caractères |
| `DATABASE_URL` | URL PostgreSQL fournie par le service choisi, avec ses exigences TLS |
| `RATELIMIT_STORAGE_URI` | URL Redis du service choisi, idéalement `rediss://` avec TLS vérifié |
| `LLM_PROVIDER` | `groq`, `openai` ou `auto` |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL` | Configuration privée du compte Groq si utilisé |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` | Configuration privée du compte OpenAI si utilisé |
| `DATA_CONTROLLER_NAME`, `DATA_CONTROLLER_CONTACT` | Identité et contact validés pour l'application |
| `CONVERSATION_RETENTION_DAYS` | Durée décidée par le responsable ; zéro désactive la purge automatique |

Les URI contenant des identifiants restent des secrets. Aucun hôte PostgreSQL/Redis ni nom de modèle n'est déduit automatiquement. `PROXY_HOPS` doit correspondre au nombre exact de proxys de confiance confirmé pour le déploiement, sans faire confiance à des en-têtes fournis par le visiteur. Vérifier HTTPS, l'adresse client et les limites de connexion avant l'ouverture publique.

## Initialiser la base et l'index

Avec le virtualenv activé et depuis la racine du dépôt :

```bash
workon autohelp
cd ~/ProjetGenAI-TXT
flask --app run db upgrade
flask --app run import-manuels --lecture-seule
flask --app run lister-manuels-dacia
flask --app run create-admin
```

L'import peut être long : utiliser la console, pas une requête HTTP. Le manifeste et les PDF sont lus sans modification ; les passages sont écrits dans PostgreSQL. Le compte administrateur est créé par saisie privée, sans identifiants publics.

## Configurer Web et WSGI

Dans **Web → Add a new web app → Manual configuration**, choisir Python 3.12. Définir le virtualenv `/home/VOTRE_COMPTE/.virtualenvs/autohelp` et le répertoire du source `/home/VOTRE_COMPTE/ProjetGenAI-TXT`.

Remplacer le contenu de démonstration du fichier WSGI proposé par PythonAnywhere par ce code, en adaptant le compte :

```python
import sys

project_home = '/home/VOTRE_COMPTE/ProjetGenAI-TXT'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from run import app as application
```

`run.py` importe la fabrique et la configuration privée `.env`. Ne pas lancer `app.run()`, Flask CLI ou Gunicorn dans cette configuration : PythonAnywhere fournit le serveur WSGI. Docker, Caddy et le Compose du dépôt ne sont pas utilisés par cette procédure.

Configurer éventuellement `/static/` vers `/home/VOTRE_COMPTE/ProjetGenAI-TXT/app/static/`. **Ne pas créer de correspondance statique vers `data/`, `instance/`, `.env` ou les PDF**, afin de conserver les contrôles d'accès de l'application. Activer le HTTPS proposé par l'hébergeur puis cliquer **Reload**.

## Vérifier et mettre à jour

1. Accueil et `/health` doivent répondre avec HTTP 200. `/ready` requiert également le schéma, un index utilisable et la configuration du fournisseur ; sa réponse ne prouve pas qu'un appel payant a réussi.
2. Tester inscription, ajout d'un Dacia présent, entretien et historique après reconnexion.
3. Poser une question sans véhicule, puis sur un véhicule indexé : la réponse documentaire doit finir par une Source avec pages et chapitre vérifiés.
4. Vérifier HTTPS, CSRF, isolation de deux comptes et fonctionnement des quotas Redis.
5. Organiser les sauvegardes PostgreSQL et vérifier une restauration ; le service de sauvegarde Compose ne tourne pas sur PythonAnywhere. Relire les réponses et valider les informations légales avant ouverture.

Pour une mise à jour, sauvegarder la base, faire `git pull --ff-only` sans écraser une modification locale, réactiver le virtualenv, installer les dépendances, appliquer les migrations, réimporter si une édition change, puis cliquer **Reload**. Ne jamais partager `.env` ni les sauvegardes.

## Sources officielles consultées

- [Flask et WSGI sur PythonAnywhere](https://help.pythonanywhere.com/pages/Flask/), consulté le 20 novembre 2026.
- [Versions Python disponibles selon l'image système](https://help.pythonanywhere.com/pages/PythonVersions/), consulté le 20 novembre 2026.
- [Bases de données et connexions externes](https://help.pythonanywhere.com/pages/KindsOfDatabases/), consulté le 20 novembre 2026.
- [Limites des fichiers GitHub](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository), consulté le 20 novembre 2026. Chaque PDF est inférieur à la limite Git de cent Mio ; Git LFS n'est pas nécessaire pour ces huit fichiers.
