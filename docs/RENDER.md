# AutoHELP sur Render gratuit, Neon et Upstash

Préparation du 20 novembre 2026. Les fichiers sont prêts à configurer ; aucun compte Neon/Upstash ni service Render public n'a été créé par ce travail. Les offres gratuites sont soumises à quotas et ne garantissent pas une disponibilité permanente.

## Architecture retenue

Render héberge Flask/Gunicorn en **runtime Python natif**, depuis `main`. Le fichier `.python-version` sélectionne Python 3.12. Les huit PDF Dacia présents dans Git font partie du code déployé ; ils restent dans `data/manuels/dacia/`, sans exposition statique publique. Le Dockerfile habituel continue d'exclure les PDF et n'est pas utilisé par ce déploiement natif.

Neon conserve PostgreSQL : comptes, véhicules, entretiens, conversations, retours et passages des manuels. Upstash conserve les compteurs et verrouillages Redis. Le disque temporaire de Render ne sert pas à stocker ces données. Les limites de sécurité de production restent actives, ainsi que CSRF, isolation, échappement et références vérifiées.

`scripts/start_render.py` applique les migrations puis lance Gunicorn sur le `PORT` fourni par Render, avec **un worker et deux threads**. Les bibliothèques numériques sont limitées à un thread. L'import PDF ne se lance ni au build ni à chaque réveil ; il est effectué depuis le PC vers Neon. La mémoire réelle et les performances sur Render Free doivent encore être mesurées après déploiement.

## Étape 1 — créer Neon

1. Ouvrir [Neon](https://neon.com/), créer un compte et un **projet dédié à AutoHELP**, en offre gratuite.
2. Choisir si possible une région européenne proche de Francfort, où le blueprint place le service web.
3. Dans **Connect**, sélectionner la branche, la base et son rôle. Copier la chaîne de connexion PostgreSQL complète, avec `sslmode=require`. Pour l'initialisation, privilégier la connexion directe (pooling désactivé).
4. Conserver cette URI en privé. Elle contient le mot de passe. Elle sera la variable `DATABASE_URL`.

La forme est `postgresql://UTILISATEUR:MOT_DE_PASSE@HOTE/BASE?sslmode=require`. Le projet convertit ce schéma en `postgresql+psycopg` ; conserver les paramètres TLS fournis. Ne pas utiliser une base personnelle existante ni y exécuter pytest.

## Étape 2 — créer Upstash Redis

1. Ouvrir [Upstash](https://upstash.com/), créer un compte puis une base **Redis** sur l'offre gratuite.
2. Choisir une région proche de l'application.
3. Dans **Connect**, sélectionner un client Redis standard/Python et récupérer la connexion **TLS Redis**, et non l'URL REST HTTPS.
4. Conserver la chaîne complète en privé pour `RATELIMIT_STORAGE_URI` :

```text
rediss://default:MOT_DE_PASSE@HOTE:6379/0
```

Utiliser le port réel indiqué par Upstash. Les caractères spéciaux des identifiants doivent être encodés dans l'URI. Laisser la vérification des certificats active. Le client `redis-py` est déjà dans les dépendances ; aucun SDK REST supplémentaire n'est nécessaire.

## Étape 3 — créer le service Render avec le blueprint

Dans le compte Render existant :

1. **New → Blueprint**, connecter GitHub puis sélectionner `KELLAM-Safeyeddine/ProjetGenAI-TXT`, branche `main`.
2. Render détecte `render.yaml`. Vérifier que le service `autohelp` utilise **Python**, le plan **Free** et la région **Frankfurt**. Le blueprint ne crée aucune base PostgreSQL payante.
3. Renseigner les champs privés demandés :

| Variable | Valeur |
| --- | --- |
| `DATABASE_URL` | URI PostgreSQL Neon, avec TLS |
| `RATELIMIT_STORAGE_URI` | URI Redis TLS Upstash, `rediss://…` |
| `GROQ_API_KEY` | Une clé privée valide, saisie uniquement dans Render |
| `GROQ_MODEL` | Identifiant du modèle compatible avec les outils, déjà utilisé localement ou vérifié sur le compte Groq |
| `DATA_CONTROLLER_NAME` | Identité du responsable, à valider |
| `DATA_CONTROLLER_CONTACT` | Contact du responsable, à valider |

Le blueprint fixe `APP_ENV=production`, `PROXY_HOPS=1` pour l'entrée Render sans autre proxy, `LLM_PROVIDER=groq` et l'URL API Groq. `SECRET_KEY` est générée automatiquement et conservée dans les variables privées Render. Ne pas ajouter de proxy/CDN supplémentaire sans revoir la confiance des en-têtes.

4. Lancer la création puis suivre **Events / Logs**. Le site reçoit une adresse HTTPS `https://NOM_DU_SERVICE.onrender.com` : utiliser l'adresse réellement attribuée.
5. Vérifier l'accueil et `/health`. Avant import des manuels, `/ready` peut renvoyer 503 ; cela n'empêche pas la FAQ générale de fonctionner.

Les déploiements automatiques attendent la réussite des contrôles GitHub (`autoDeployTrigger: checksPass`). Si nécessaire, après correction d'un réglage, utiliser **Manual Deploy → Deploy latest commit**. Les valeurs `sync: false` ne sont demandées qu'à la création ; une clé modifiée ensuite se renseigne dans **Environment**, puis nécessite un redémarrage/redéploiement.

## Alternative — service Web déjà créé manuellement

Si un service existe déjà, adapter ses réglages sans en créer un second :

| Réglage | Valeur |
| --- | --- |
| Repository | `KELLAM-Safeyeddine/ProjetGenAI-TXT` |
| Branch | `main` |
| Language / Runtime | **Python** |
| Root directory | Vide : racine du dépôt |
| Build command | `python -m pip install --no-cache-dir -r requirements.txt` |
| Start command | `python scripts/start_render.py` |
| Health check path | `/health` |
| Instance type | **Free** |

Ajouter les variables du blueprint dans **Environment**. Pour `SECRET_KEY`, utiliser un générateur privé de valeur aléatoire d'au moins trente-deux caractères. Le fichier `.python-version` choisit la version ; si `PYTHON_VERSION` existe déjà, la supprimer ou renseigner une version 3.12 complète supportée par Render. Ne pas choisir le runtime Docker pour cette procédure, car son image exclut les PDF.

## Étape 4 — importer les manuels depuis le PC vers Neon

Le plan gratuit Render ne fournit pas de Shell ni de tâches ponctuelles. L'opération s'exécute donc sur le PC de l'opérateur, avec le même code et le même PostgreSQL Neon. Aucun changement de `.env` local n'est nécessaire.

Depuis PowerShell, dans le projet source :

```powershell
cd C:\Users\SafeyeddineK\Desktop\Projet\Projet-GenAIText
Copy-Item .env.example .env.render
notepad .env.render
```

**Créer cette copie une seule fois**, sans écraser un `.env.render` déjà renseigné. Dans ce fichier privé ignoré par Git, renseigner seulement :

```dotenv
APP_ENV=production
SECRET_KEY=LA_MEME_CLE_PRIVEE_QUE_DANS_RENDER
DATABASE_URL=LA_CONNEXION_POSTGRESQL_NEON
RATELIMIT_STORAGE_URI=LA_CONNEXION_REDIS_TLS_UPSTASH
```

Ces valeurs sont des exemples à remplacer. Laisser les autres variables vides. Copier la `SECRET_KEY` depuis **Render → Environment**, en privé. Ne jamais envoyer ce fichier, les URL avec mot de passe ni les clés dans GitHub, une capture ou un message.

Sur le poste actuel, l'environnement Python utilisable est `.work/venv`. Lancer :

```powershell
.\.work\venv\Scripts\python.exe scripts/render_manage.py initialiser
.\.work\venv\Scripts\python.exe scripts/render_manage.py verifier
.\.work\venv\Scripts\python.exe scripts/render_manage.py creer-admin
```

Sur un autre PC, créer un virtualenv Python 3.12 et installer `requirements.txt`, puis utiliser son interpréteur à la place de `.work/venv/Scripts/python.exe`.

L'outil n'accepte que `initialiser`, `verifier` et `creer-admin`. Il charge la cible depuis `.env.render`, refuse une cible SQLite ou Redis sans TLS et empêche la reprise des clés/base du `.env` local. Aucun appel de modèle n'est effectué par ces commandes. Les mots de passe administrateur sont saisis sans affichage. L'import conserve les PDF et le manifeste ; les passages sont écrits dans Neon. L'extraction complète peut durer : laisser le PC travailler jusqu'à la fin.

Après l'import, redémarrer le service Render si des utilisateurs avaient déjà chargé le catalogue avant l'import, puis se connecter au site HTTPS. Ne pas importer une copie de la base personnelle ; créer les comptes de démonstration sur le site.

## Étape 5 — recette réelle sur le site

1. Vérifier accueil et `/health` en 200, puis `/ready` en 200 après index et configuration du fournisseur. `/ready` ne constitue pas un appel réel au modèle.
2. Inscrire un compte de démonstration, ajouter un Dacia et un entretien.
3. Sans véhicule : tester les essuie-glaces, réponse FAQ détaillée.
4. Avec Bigster 2026 : demander comment contrôler le niveau d'huile, attendre une réponse avec pages et chapitre vérifiés.
5. Se déconnecter/reconnecter, vérifier l'historique, puis effectuer un redéploiement et contrôler la persistance des données Neon.
6. Tester les droits avec un second compte et la protection CSRF. Contrôler les quotas et les journaux sans publier de secret.

## Limites et diagnostic

Render Free peut se mettre en veille après inactivité et son disque n'est pas persistant. Les écritures locales ne sont donc jamais une sauvegarde. Le service PostgreSQL gratuit de Render expire après trente jours ; ce guide utilise Neon à sa place. Les offres Neon, Upstash, Render et Groq ont leurs propres quotas et conditions ; rester sur les plans gratuits choisis. La faible RAM de l'instance Render peut imposer de réduire la charge ou de changer d'offre : un worker limite les duplications, sans garantir une mémoire suffisante pour tous les usages. Aucun dispositif de faux trafic n'est prévu pour empêcher la veille.

| Symptôme | Vérification |
| --- | --- |
| Build en Python 3.14 ou dépendance incompatible | Runtime Python, `.python-version` et éventuelle variable `PYTHON_VERSION` prioritaire |
| Aucun port détecté | Start command `python scripts/start_render.py`, journaux de migration et `PORT` fourni par Render |
| Erreur de connexion à PostgreSQL | URI de la bonne branche Neon, rôle, mot de passe et paramètres TLS |
| Connexion/inscription en 503 | URI Redis `rediss://`, pas l'URL REST ; quotas et disponibilité Upstash |
| Aucun manuel | Résultat de l'import dans la même base Neon que `DATABASE_URL` du web |
| Assistant indisponible | Clé, modèle, URL, quotas et accès réseau du fournisseur |
| Instance arrêtée pour mémoire | Examiner les métriques ; limiter la charge avant de promettre une disponibilité |

Le service de sauvegarde Docker ne tourne pas sur cette architecture. Prévoir des exports PostgreSQL privés et tester une restauration avant d'utiliser de vraies données. Les informations de confidentialité et la relecture automobile restent à valider par le responsable.

## Sources officielles consultées le 20 novembre 2026

- [Flask sur Render](https://render.com/docs/deploy-flask).
- [Blueprint et variables privées](https://render.com/docs/blueprint-spec).
- [Python sur Render](https://render.com/docs/python-version).
- [Limites du plan gratuit, dont absence de Shell](https://render.com/docs/free).
- [Connexion PostgreSQL Neon](https://neon.com/docs/connect/connect-from-any-app).
- [Connexion Redis Upstash depuis Render](https://upstash.com/docs/redis/quickstarts/render).

La recette sur les comptes et l'URL publics reste à effectuer ; aucune réussite sur Render/Neon/Upstash n'est déduite des tests locaux.

Contrôles de préparation exécutés : 420 tests pytest réussis en 77,53 s, Ruff conforme sur 142 fichiers. La construction Docker Linux locale n'a pas pu être répétée car Docker Desktop était arrêté ; le déploiement Render utilise le runtime Python natif. Les tests de démarrage et d'administration simulent les processus externes et n'utilisent ni vos secrets ni vos services cloud.
