# Livraison actuelle — 14 novembre 2026

Paquet régénéré depuis le source : 159 fichiers, huit notices Dacia conservées. Aucun secret réel, .env, base, environnement, cache ou compte. PDFs montés en lecture seule et exclus de Git/image. SQLite persistant et Redis partagé ; port 5000 par défaut, 5012 pour la recette isolée.

État final vérifié : 370 tests sur SQLite (68,18 s) et PostgreSQL (57,63 s), zéro ignoré ; image runtime 361 réussis/9 facultatifs ignorés (61,37 s). Accueil, health et ready 200 ; UID 10001 ; image sans PDF/env/base. Audits runtime/dev sans avis connu, Ruff et Actionlint réussis. Workflow GitHub à déclencher après publication par le groupe.

Évaluateur réel fourni avec 400 questions ; 50 annotations Bigster assistées, 350 à établir et aucune revue humaine signée. Rappel partiel : 25/49 (51,0 %) ; absence de passage pour le tarif non documenté : 1/1, séparée du rappel. Corpus non validé, pas de score de qualité LLM. Le CLI sans --partiel refuse le corpus incomplet (code 1 attendu), y compris les annotations assistées sans revue humaine. Le groupe demande d'attendre les annotations avant les tâches suivantes. Guide EVALUATION_MANUELS.md et détails recette.md. Les rapports temporaires, rendus PDF et bases de recette sont exclus du paquet.

La suite conserve les recettes historiques ; leurs anciens nombres de fichiers/tests et blocages Docker ne décrivent pas cet état final.

---

# Validation du 14 novembre 2026

Le blocage moteur d'octobre est levé. Livraison régénérée depuis le source et testée réellement : Docker/Gunicorn non-root, SQLite persistant, port 5000 (5012 pour la recette isolée), huit PDF montés en lecture seule hors image. Image inspectée sans PDF, .env ni base ; accueil, health et ready 200, santé healthy. Import Bigster complet 1721 passages ; création administrateur CLI, réponse sourcée avec modèle factice et parcours HTTP/persistance après recréation réussis. Source : 326 tests réussis en 115,92 s ; conteneur sans puis avec fournisseur factice : 317 réussis/9 facultatifs ignorés en 77,75 s et 70,14 s. Détails et commandes : recette.md.

La suite du fichier conserve le rapport historique d'octobre ; ses mentions de moteur indisponible et de générateur à ne pas utiliser sont remplacées par cette validation.

---

# Rapport de préparation — livraison AutoHELP

**Date : 25 octobre 2026. Dossier travaillé : `C:\Users\SafeyeddineK\Desktop\Projet\livraison`.**

Cette demande remplace la livraison sans PDF et le fonctionnement PostgreSQL par défaut de l’ancienne copie. Le nom reste `livraison` ; aucun autre paquet de livraison n’a été créé. Le projet source voisin n’est pas modifié et son générateur ne doit pas écraser cette copie.

## Fichiers inclus et exclus

Inclus : `app/` (templates et static), `migrations/`, `config/`, `data/` (FAQ générale et archives factuelles), `tests/`, `docs/`, `docker/`, `scripts/`, `manuels/`, `config.py`, `run.py`, `requirements.txt`, `pytest.ini`, `Dockerfile`, fichiers Compose, `.dockerignore`, `.gitignore`, `.gitattributes`, `.env.example`, `README.md`, `README-livraison.md` et `CHANGEMENTS.md`. Liste exhaustive : [CONTENU_LIVRAISON.txt](CONTENU_LIVRAISON.txt).

Exclus : `.venv`, caches Python/pytest, `.git`, bases locales, journaux, uploads personnels, fichier `.env`, clés réelles, données utilisateur et PDF hors des huit références. Les PDF fournis restent ignorés par Git et hors de l’image. Les rapports temporaires, bases de recette, captures de couvertures et secrets de test sont restés dans un répertoire temporaire extérieur au paquet.

La copie utilise un utilisateur non-root dans une image Python 3.12 slim et Gunicorn. La configuration Compose valide définit un service web, le port local 5000, le volume nommé `autohelp_data` pour SQLite et la clé de session générée, et le montage `./manuels:/app/data/manuels:ro`. Les valeurs du modèle `.env.example` sont vides ; `.env` est facultatif au démarrage de la FAQ. L’option `env_file.required: false` demande Compose 2.24 ou plus récent, conformément à la [documentation Docker](https://docs.docker.com/reference/compose-file/services/#env_file).

## Notices copiées

Le dossier `manuels/` à la racine du projet source indiqué n’existait pas. La source réelle était `C:\Users\SafeyeddineK\Desktop\Projet\Projet-GenAIText\data\manuels`. Seules les huit entrées Dacia validées et actives ont été retenues ; aucun des PDF étrangers n’est copié.

| Fichier dans livraison | Modèle | Année | Pages |
| --- | --- | ---: | ---: |
| `manuels/dacia/bigster/2026/manuel.pdf` | Dacia Bigster | 2026 | 430 |
| `manuels/dacia/duster/2026/manuel.pdf` | Dacia Duster | 2026 | 440 |
| `manuels/dacia/jogger/2026/manuel.pdf` | Dacia Jogger | 2026 | 422 |
| `manuels/dacia/logan/2026/manuel.pdf` | Dacia Logan | 2026 | 374 |
| `manuels/dacia/sandero/2021/manuel.pdf` | Dacia Sandero | 2021 | 402 |
| `manuels/dacia/sandero/2026/manuel.pdf` | Dacia Sandero | 2026 | 384 |
| `manuels/dacia/sandero-stepway/2026/manuel.pdf` | Dacia Sandero Stepway | 2026 | 384 |
| `manuels/dacia/spring/2026/manuel.pdf` | Dacia Spring | 2026 | 286 |

**Huit fichiers pour huit combinaisons, aucun manquant**, environ 144,5 Mio. Sandero et Sandero Stepway 2026 partagent la même notice commune explicitement identifiée : sept contenus distincts par SHA-256, huit fichiers associés à leurs identités séparées.

Vérifications effectuées : présence, signature PDF, absence de chiffrement, ouverture par pypdf, modèle confirmé avec l’inventaire existant, empreinte SHA-256 conforme à la preuve validée, texte extractible sur la couverture et des pages échantillonnées, rendu et inspection visuelle des huit couvertures. Cela ne constitue pas une relecture visuelle de toutes les pages. Les droits du constructeur restent applicables ; aucune redistribution hors du cadre autorisé.

`manuels/index.json` et sa copie de métadonnées indiquent les notices **à importer**. Aucune base ni aucun index prérempli n’est distribué. Après initialisation, `flask list-manuels` donne l’état réel de la base ; le manifeste monté en lecture seule n’est pas réécrit.

## Corrections indispensables à l’exécution

- **Montage lecture seule** : l’ancien import réécrivait `index.json` après l’extraction. L’option `flask import-manuels --lecture-seule` conserve cette extraction, les contrôles et l’indexation en base, mais ne réécrit pas le manifeste. Sans cette adaptation d’infrastructure, l’import échouerait sur le montage demandé. L’import sans option conserve son comportement antérieur.
- **Vivacité** : `/health` répond sans requête base, comme demandé. L’ancien contrôle connexion/schéma reste dans `/ready`.
- **Stockage et port** : configuration Compose SQLite/volume persistant et port 5000, démarrage Gunicorn non-root ; migrations automatiques conservées.
- **Recette** : tests des fonctions d’infrastructure et adaptation de l’emplacement des PDF pour les deux intégrations géométriques.

Aucune modification des réponses, du moteur de recherche, du formulaire ou de la FAQ. Sept fichiers métier ont été comparés octet par octet au projet source : orchestration des réponses, moteurs FAQ, outils documentaires, route du chat, formulaires et FAQ générale. CSRF, isolation des comptes, ORM, échappement et références vérifiées restent conservés.

## Résultats réels des vérifications

| Vérification | Résultat réel |
| --- | --- |
| Configuration Compose | **Valide**, `docker compose --env-file .env.example config --quiet` réussit |
| Huit PDF | **Validés et copiés**, aucun manquant ni PDF supplémentaire |
| Règles Git | **Validées pour les huit chemins** dans un dépôt temporaire externe ; aucun `.git` livré |
| Nettoyage et secrets | Contrôle par `scripts/verifier_livraison.py`, sans clé réelle ni fichier privé détecté |
| Pytest depuis livraison | **314 réussis en 227,38 s**, aucun échec ni ignoré |
| Essai assistant natif isolé | **HTTP 200, source manuel, deux références, ligne Source finale**, Bigster 2026, CSRF actif |
| Docker Desktop | Client installé ; démarrage en échec : `Docker Desktop is still starting: context deadline exceeded`, moteur injoignable |
| `docker build -t autohelp .` | Tenté ; **délai de 45 secondes dépassé sans construction validée** |
| `docker compose up --build -d` | Tenté ; **délai de 45 secondes dépassé sans démarrage validé** |
| Accueil et `/health` sur localhost:5000 | **Non validés** : connexions HTTP refusées/injoignables au contrôle |
| Inspection effective de l’image par `docker run … find` | **Non exécutée**, aucune image construite avec succès ; la copie explicite et les exclusions ont seulement été contrôlées statiquement |
| Non-root, healthcheck et persistance du volume dans Docker | Configurés, mais **non vérifiés en conteneur** faute de moteur opérationnel |
| Assistant dans Docker et indexation complète des huit notices | **Non vérifiés en conteneur** ; à effectuer après démarrage et import |

Pytest a été exécuté avec Python 3.12 et l’environnement existant du poste, extérieur au dossier livraison, en plaçant bases et journaux de recette dans un répertoire temporaire. Commande :

```powershell
C:\Users\SafeyeddineK\Desktop\Projet\Projet-GenAIText\.work\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp <répertoire-temporaire-externe>
```

Le répertoire courant était bien celui de la livraison. Les clés de tests sont factices. Les tests supplémentaires couvrent la vivacité sans base, le contrôle `/ready`, l’import sans écriture du manifeste et l’absence de valeurs privées dans la configuration.

L’essai natif de l’assistant a importé seulement les pages PDF 355 et 356 de la notice Bigster dans une base temporaire neuve, puis créé un compte et son véhicule éphémères et appelé `/api/chat` avec CSRF actif. Il a utilisé la configuration privée déjà autorisée sur le poste, uniquement en mémoire : aucune clé n’est copiée dans ce dossier ou l’image. Les références retournées portaient sur ces pages. Cet essai réel ne valide ni Docker ni l’indexation complète des huit notices ; aucune donnée de ce compte n’est dans le paquet.

## Commandes exactes

Depuis la livraison :

```bat
cd C:\Users\SafeyeddineK\Desktop\Projet\livraison
copy .env.example .env
docker build -t autohelp .
docker compose up --build
```

Dans un second terminal, après que le service répond :

```bash
docker compose exec web flask import-manuels --lecture-seule
docker compose exec web flask list-manuels
docker compose exec web flask create-admin
```

Le premier import prend plusieurs minutes ; le relancer après remplacement d’un PDF. Les migrations sont appliquées automatiquement au démarrage, sans compte public prédéfini. Pour arrêter sans perdre SQLite et la clé de session :

```bash
docker compose down
```

Contrôles restant à lancer lorsque Docker est opérationnel :

```bash
docker run --rm autohelp find /app -name "*.pdf" -o -name "*.env" -o -name "*.db"
docker compose exec web python -m pytest -q -p no:cacheprovider
docker compose exec web flask evaluer-chatbot
```

La commande find inspecte l’image sans initialisation ni volumes et ne doit rien renvoyer. Vérifier ensuite l’accueil, `/health`, `/ready`, une réponse documentaire sourcée, et la persistance après `docker compose restart web`.

## À faire côté groupe

1. Rendre le moteur Docker opérationnel, puis refaire build, lancement et contrôles en conteneur ci-dessus. Ne pas considérer la présence du client comme un démarrage réussi.
2. Importer les huit notices dans le volume neuf, puis contrôler les éditions, langues et motorisations utilisées. Les passages nécessitant une relecture visuelle restent bloqués.
3. Configurer sa propre clé de fournisseur, son modèle et son URL dans un `.env` privé, puis recréer web. La FAQ fonctionne sans clé ; le dialogue documentaire nécessite cette configuration.
4. Relire un échantillon de réponses, notamment de sécurité, et respecter les droits des notices avant partage. Supprimer `.env`, bases ou journaux locaux avant redistribution.
5. Fournir hébergement, domaine, HTTPS, PostgreSQL de production et sauvegardes si une publication publique est souhaitée ; SQLite ici est destiné au partage local.
