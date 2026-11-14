# AutoHELP — Carnet automobile et assistant conversationnel

### Reprise des améliorations — 14 novembre 2026

Avant toute modification, une sauvegarde privée complète du projet source et de la livraison a été créée dans le dossier frère `sauvegardes/` : archive ZIP, 24 654 fichiers relus et vérifiés par SHA-256, instantané SQLite cohérent contrôlé. Elle contient la configuration privée et des données locales : ne pas la publier ni la joindre à une livraison.

Le versionnement initial conserve le code, les tests et les métadonnées des manuels ; les PDF, `.env`, clés, bases, environnements, journaux et médias de démonstration sont exclus. Avant chaque commit, indexer les changements puis vérifier le contenu exact de l'index :

```bash
git add --all
python scripts/audit_git.py
git diff --cached --stat
```

L'audit refuse notamment un PDF ajouté de force, une configuration d'exemple renseignée ou une clé reconnue dans un blob indexé. Il ne remplace pas une revue des fichiers ni un audit spécialisé des secrets. Les données privées restent sur le poste ; aucun dépôt distant n'est publié automatiquement.

**Livraison existante :** la copie voisine a été personnalisée après la documentation historique ci-dessous : SQLite persistant, port 5000, huit notices dans `manuels/`, import `flask import-manuels --lecture-seule`. La décision du 14 novembre conserve ces huit notices dans cette copie, sans les versionner ni les incorporer à l'image. Ne pas lancer l'ancien générateur sur cette livraison avant son adaptation et sa validation à l'étape Docker. Les instructions actuelles de cette copie sont dans son `README-livraison.md`.

La feuille de route de reprise et le plan de la prochaine étape sont dans [docs/AMELIORATIONS.md](docs/AMELIORATIONS.md).

Application Flask en français : comptes privés, véhicules limités aux versions Dacia dont un manuel local est identifié, entretiens, échéances et conversations persistantes. Sans véhicule sélectionné, le chatbot consulte les quarante fiches de `data/faq_generale.json` avec des réponses détaillées sans libellé de mode, terminées par une seule phrase vers un mécanicien. Avec un véhicule, il répond uniquement depuis son PDF Dacia local identifié et indexé : le LLM reformule les passages retrouvés, sans relais FAQ ni web. L’ancienne FAQ `data/faq.json` et son administration restent archivées ; elles ne fournissent pas les réponses de la nouvelle FAQ générale. Les évolutions expressément demandées priment sur les anciennes règles du cahier des charges ; voir [docs/CHANGEMENTS.md](docs/CHANGEMENTS.md).

## Lancer la livraison avec Docker

Docker Desktop/Engine et Compose v2 doivent être démarrés. Aucun Python à installer sur l’hôte.

```bat
cd C:\Users\SafeyeddineK\Desktop\Projet\livraison
copy .env.example .env
docker compose up --build
```

Ouvrir http://localhost:8000. Sous PowerShell, `Copy-Item .env.example .env` convient ; sous Linux/macOS, `cp .env.example .env`.

Le démarrage applique les migrations, importe le catalogue historique archivé et conserve l’archive FAQ. Gunicorn sert l’application. `/health` contrôle la connexion et le schéma. Le conteneur démarre sans clé de modèle : la FAQ générale sans véhicule fonctionne ; le dialogue sur un manuel affiche **« L’assistant est indisponible pour le moment. »** tant que le fournisseur n’est pas configuré. L’interface ne demande jamais une clé aux utilisateurs.

```bash
docker compose exec web flask create-admin
```

La commande demande des identifiants privés et un mot de passe masqué ; aucun compte administrateur public n’est fourni. `docker compose down` arrête cette instance ; `docker compose up -d` la reprend. Les volumes `postgres_data`, `db_secrets`, `app_secrets` conservent données et secrets générés. Éviter `down -v` si ces données doivent rester.

Si 8000 est occupé, définir un port libre dans `PORT`, puis utiliser ce port dans le navigateur. Le projet Compose est `autohelp`, avec services `web` et `db` ; ne pas lancer deux copies sous ce même nom. `docker compose -p autre-groupe ...` permet une instance indépendante. PostgreSQL n’expose pas de port hôte ; le web écoute sur l’interface locale.

## Préparer les données et le modèle

1. Placer les PDF Dacia identifiables dans `data/manuels/`, selon la procédure ci-dessous. Les huit fichiers Dacia présents dans le projet source sont maintenant validés ; la livraison ne contient aucun PDF.
2. Importer les PDF et vérifier les versions disponibles (aucun index web n’est utilisé) :

```bash
docker compose run --rm --volume ./data/manuels:/app/data/manuels:rw web flask import-manuels
docker compose exec web flask lister-manuels-dacia
```

3. Renseigner la configuration privée du modèle dans `.env`, puis recréer le service :

```bash
docker compose up -d --force-recreate web
```

Toutes les variables de `.env.example` sont **vides**. Ne jamais y placer une vraie clé ni partager le `.env` privé.

| Variable | Rôle |
| --- | --- |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` | Premier fournisseur si sa clé est présente ; modèle compatible Chat Completions et appels de fonctions |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL` | Sinon, fournisseur Groq compatible avec les appels de fonctions |
| `SEARCH_PROVIDER`, `SEARCH_API_KEY`, `SEARCH_BASE_URL` | Variables historiques, inutilisées par le dialogue actuel (PDF uniquement) |
| `SECRET_KEY` | Sessions/CSRF ; au moins 32 caractères aléatoires en production |
| `DATABASE_URL` | SQLite en local, PostgreSQL en production ; défaut Compose vers `db` |
| `PORT` | 8000 par défaut dans Compose |
| `AI_API_KEY` | Ancienne variable conservée, inutilisée |

Il n’existe aucun nom de modèle ou URL de fournisseur implicite dans le service. Une clé exige également un modèle et une URL de base HTTPS valides. OpenAI a priorité sur Groq ; une erreur OpenAI ne bascule pas silencieusement sur Groq. Sans clé ou en erreur distante, seul le message neutre est public, avec un avertissement de sécurité si nécessaire.

Documentation officielle consultée le **18/10/2026** : [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling), [Groq tool use](https://console.groq.com/docs/tool-use/overview), [modèles Groq](https://console.groq.com/docs/models). Exemple documentaire vérifié : modèle Groq `openai/gpt-oss-20b`, base `https://api.groq.com/openai/v1`. Pour OpenAI : base `https://api.openai.com/v1` et modèle compatible disponible sur votre compte. Ces exemples ne sont pas des valeurs distribuées dans le template.

## Installation locale SQLite

Python 3.13 recommandé ; Windows utilise le serveur Flask de développement. Gunicorn s’exécute sous Linux/Docker.

```bash
python -m venv .venv
# PowerShell : .\.venv\Scripts\Activate.ps1
# Linux/macOS : source .venv/bin/activate
python -m pip install -r requirements.txt
flask --app run db upgrade
flask --app run import-vehicules
flask --app run import-faq
flask --app run run --port 5001
```

Le `.env` privé est lu sans exécuter son contenu ; les variables du processus ont priorité. En développement, la clé de session persistante est générée dans `instance/`. Cette base et ces secrets ne sont jamais livrés. Commande Linux : `gunicorn run:app`, ou `gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 40 run:app`.

## Véhicules et carnet d’entretien

La création et le réenregistrement acceptent uniquement les combinaisons marque/modèle/année dont un **PDF Dacia local est identifié**. `app/services/manual_inventory.py` scanne récursivement le dossier configuré ; le formulaire et la validation serveur utilisent ce même inventaire, sans liste de modèles figée ni suggestions du catalogue marocain. Actuellement, huit combinaisons correspondent aux PDF vérifiés ci-dessous. Le retrait d’un fichier le retire du catalogue ; ajouter un modèle Dacia identifié ne demande aucun changement du code.

Dacia est fixe, modèle et année sont des listes en cascade. Comparaison exacte insensible à la casse, aux accents et aux espaces ; Sandero, Sandero Stepway et les millésimes restent distincts. Un POST forgé hors inventaire reçoit HTTP 422 avec erreur française, sans écriture. Motorisation libre facultative, kilométrage facultatif entier positif ou nul sur 64 bits. Le catalogue marocain reste archivé, sans effet sur les choix.

Les anciens véhicules sont conservés et consultables ; leur formulaire s’ouvre sans changer la base, mais le réenregistrement exige un PDF admissible. Le chat ne sélectionne que les véhicules du compte présents dans l’inventaire. Un ancien identifiant envoyé à l’API ne reçoit jamais le manuel d’un autre modèle/année ; l’absence d’index exact est annoncée. Pour lister les véhicules hors inventaire sans modification :

```bash
flask --app run lister-vehicules-hors-liste
```

Les entretiens enregistrent une opération réalisée, date, compteur, coût en MAD et notes. Une échéance est saisie depuis le carnet constructeur, jamais inventée. États : dépassée si un terme est dépassé ; atteinte si un terme est égal et aucun dépassé ; future si les termes comparables sont futurs ; absente si aucun renseigné. Sans compteur actuel, une échéance kilométrique ne peut être comparée. Le compteur d’une opération respecte la chronologie des opérations et le compteur actuel lorsqu’il est connu. Les coûts ont deux décimales. Aucun VIN, plaque, notification email/SMS ou diagnostic à distance.

L’accueil connecté propose le tableau de bord et la déconnexion ; `/login` et `/register` redirigent alors vers le tableau de bord. Les suppressions demandent confirmation et CSRF, jamais un GET. La suppression du compte exige le mot de passe et retire ses données liées.

## Chatbot : FAQ générale sans véhicule, PDF Dacia avec véhicule

Le périmètre est dérivé des PDF Dacia réellement présents et identifiés par `manual_inventory.py`. `manual_policy.py` définit l’égalité exacte, sans liste figée. Inventaire vérifié le 24/10/2026 :

| Marque | Modèle | Année | État documentaire courant |
| --- | --- | --- | --- |
| Dacia | Bigster | 2026 | PDF validé et indexé |
| Dacia | Duster | 2026 | PDF identifié et indexé |
| Dacia | Jogger | 2026 | PDF identifié et indexé |
| Dacia | Logan | 2026 | PDF identifié et indexé |
| Dacia | Sandero | 2021 | PDF identifié et indexé |
| Dacia | Sandero | 2026 | PDF identifié et indexé |
| Dacia | Sandero Stepway | 2026 | PDF identifié et indexé |
| Dacia | Spring | 2026 | PDF identifié et indexé |

L’égalité de marque/modèle/année ignore casse, accents et espaces, sans rapprochement approximatif. Sandero 2021, Sandero 2026 et Sandero Stepway restent distincts. Les créations et réenregistrements sont limités à l’inventaire local validé, qui peut évoluer après ajout ou retrait d’un PDF. Les anciens véhicules hors liste restent conservés, mais ne sont pas sélectionnables dans le chat.

Le serveur vérifie d’abord les droits sur le véhicule et la conversation. Le modèle n’a que `rechercher_manuel(requete)`, en lecture seule, lié au véhicule choisi. Aucun argument de véhicule, de version, de page ou de table n’est accepté. La version mécanique demandée est extraite côté serveur du message original et de la motorisation enregistrée. Les passages incompatibles sont écartés ; les passages applicables sont privilégiés, sans confondre les valeurs des versions. Les références proviennent uniquement des résultats du tour courant.

Une réponse sourcée se termine par une seule ligne : `Source : manuel Dacia Bigster 2026, page imprimée 196, page PDF 198, chapitre La conduite, section ...`. Le serveur inclut cette ligne dans `reply` et le navigateur évite une seconde copie. Aucun libellé de mode ni formule finale générique vers un mécanicien n’est ajouté. Si la pagination imprimée n’est pas identifiée, le serveur le précise au lieu de l’inventer. Les valeurs et unités sans support et les références inventées restent rejetées. Les autres versions sont signalées lorsque le passage n’est pas universel.

Sans manuel, le chat répond explicitement, par exemple : **« Je n’ai pas le manuel du Dacia Duster 2026. »** Sans sélection, il cherche dans la nouvelle FAQ générale ; celle-ci ne remplace jamais un manuel quand un véhicule est sélectionné. Une question vague peut demander une précision ; hors sujet, refus poli. Si le PDF disponible ne contient pas d’information suffisamment pertinente ou vérifiable, message honnête sur l’information manquante, sans réponse web, FAQ, source inventée ou diagnostic deviné. Les avertissements freins, pneus, direction, airbags, voyants rouges et fuites de carburant sont conservés.

Les conversations et leurs sources restent privées et persistantes. La présentation des anciens messages masque les libellés et les anciennes sources FAQ, sans réécriture en base ni invention de référence. Les avertissements historiques restent des phrases de sécurité dans le contenu. Dix messages récents/5 500 caractères et un résumé extractif de 900 caractères sont sélectionnés parmi 80 messages. Un changement de véhicule/motorisation coupe le segment précédent. Les anciennes réponses documentaires, notamment web/FAQ, restent visibles dans l’historique mais ne servent pas de sources au modèle ; seules les nouvelles recherches du tour courant font autorité.

Les appels restent isolés dans `llm_service.py`, avec configuration OpenAI prioritaire puis Groq, timeout de 5 secondes, tentatives limitées, budget de 20 secondes, contexte 28 000 caractères et sortie 1 200 jetons. Sans configuration utilisable, indisponibilité neutre du dialogue sur les manuels ; la FAQ générale locale reste accessible ; les métadonnées connues de manuel absent peuvent être annoncées sans appel distant. Aucun fournisseur ni clé n’est affiché dans les réponses.

## FAQ générale sans véhicule

La règle précédente « FAQ désactivée » est annulée **uniquement sans véhicule sélectionné**. Le sélecteur est placé au-dessus du champ de question : « Aucun véhicule » active les conseils généraux ; choisir un véhicule active uniquement son manuel. Les références et l’historique sont conservés dans le compte.

`data/faq_generale.json` contient quarante fiches originales, sans marques, chiffres ni normes techniques. Les champs obligatoires sont `identifiant`, `categorie`, `question`, `reponse`, `mots_cles`, `niveau_risque` ; `variantes` complète les formulations ; `ancrages` et `exclusions` facultatifs évitent les rapprochements de sujets non couverts. Un identifiant est unique et le risque vaut `faible`, `moyen` ou `élevé`. Les quarante réponses contiennent de 150 à 300 mots et se terminent par une seule phrase invitant à consulter un mécanicien pour plus d’informations. Les fiches à risque élevé intègrent les actions de sécurité dans leur contenu, sans bandeau. Le fichier est lu directement : **aucun import ni clé API nécessaire** ; `flask import-faq` concerne seulement l’archive historique.

La recherche réutilise `chatbot_service.search_response` : normalisation, synonymes, mots-clés et TF-IDF, seuil existant **0,45**. Le score n’est pas une probabilité. En dessous du seuil ou en cas d’ambiguïté, aucune fiche n’est inventée : l’assistant propose de reformuler ou de choisir un véhicule. Une question vague reçoit une demande de précision ; une question hors sujet est refusée poliment.

Pression exacte, huile, couple, capacité et fusible : explication générale sans valeur technique, puis invitation à sélectionner le véhicule. Aucune page, marque ou notice particulière n’est citée sans sélection. Les actions de sécurité restent obligatoires dans le contenu, sans avertissement générique ajouté autour. Aucun libellé de mode ni source de fiche FAQ n’est affiché. Le sélecteur conserve son emplacement ; son déplacement antérieur et la proposition sont documentés dans [docs/FORMAT_REPONSES.md](docs/FORMAT_REPONSES.md). Détail du contenu, répartition, sources de vérification et limites : [docs/FAQ_GENERALE.md](docs/FAQ_GENERALE.md).

## Import et méthode d’extraction des manuels

Placer uniquement les PDF dont l’équipe dispose du droit d’usage dans `data/manuels/` (ou le dossier Flask `MANUALS_DIR`). Arborescence recommandée : `dacia/<modele>/<annee>/manuel.pdf`. Un nom explicite comme `Dacia_Lodgy_2020.pdf` est aussi accepté si la couverture confirme le modèle et la marque. Le scan est récursif, insensible à la casse de l’extension, sans réseau ni OCR.

L’année doit apparaître dans le nom du fichier ou la couverture ; **un dossier nommé 2026 ne suffit pas**. Lorsque le PDF ne porte aucune année, renseigner une preuve vérifiée `preuve_identite` : URL officielle exacte, URL PDF effectivement proposée, modèle/année, date de consultation, début/fin de validité et SHA-256 du fichier. L’équipe doit vérifier ces informations sur la page officielle ; le scan ne les invente pas et ne navigue pas automatiquement. Les huit preuves actuelles ont été revérifiées le 24/10/2026. Une période partielle ne garantit pas toutes les éditions ni tous les équipements d’une année.

Un PDF sans modèle/année identifiables, chiffré, corrompu, sans texte, en conflit avec la couverture ou en double pour le même triplet est rejeté avec une raison. Aucun manuel d’une autre marque n’est activé. Les modèles multiples d’une couverture ne créent pas automatiquement de nouveaux triplets : l’identité déclarée ou nommée doit être confirmée. Les copies Sandero et Stepway 2026 contiennent le même document commun, qui cite explicitement les deux modèles.

```bash
flask --app run lister-manuels-dacia
flask --app run import-manuels
flask --app run lister-manuels-dacia
```

`import-manuels` scanne tous les PDF, importe les Dacia identifiés et actualise atomiquement `data/manuels/index.json`. Les anciens indicateurs `pret_import` ne constituent plus une liste figée ; l’identification du fichier fait autorité. Les entrées rejetées/absentes restent désactivées et les anciens passages archivés, sans suppression. Le catalogue et les validations serveur sont recalculés depuis les fichiers identifiés ; sans PDF admissible, aucun véhicule ne peut être ajouté. Sans index actif correspondant au modèle ET à l’année, le chat annonce le manuel absent. Après remplacement d’un PDF, relancer l’import avant utilisation.

Sous Docker, le service web conserve son montage des PDF **en lecture seule**. L’import doit pouvoir mettre à jour le manifeste : utiliser un conteneur ponctuel avec le montage autorisé en écriture pour cette commande, puis consulter depuis le service web :

```bash
docker compose run --rm --volume ./data/manuels:/app/data/manuels:rw web flask import-manuels
docker compose exec web flask lister-manuels-dacia
```

Le compte du conteneur (UID 10001 sous Linux) doit pouvoir écrire le manifeste dans le dossier hôte. Aucun PDF n’est incorporé à Git, à l’image ou à la livraison ; les membres doivent placer leurs PDF sur leur poste. Le scan et le modèle ne téléchargent aucun manuel. Référence de la commande ponctuelle : [documentation Docker Compose](https://docs.docker.com/reference/cli/docker/compose/run/). Cette commande Docker n’a pas été exécutée lors de cette recette, le moteur étant arrêté.



### Analyse et extraction du Bigster

Document analysé : **NU 1626-3 R1310**, 430 pages, couche texte exploitable, non chiffré. `pdfinfo` a confirmé les propriétés ; `pdffonts` n’est pas installé dans cet environnement, les polices ont été contrôlées par les ressources PDF et les caractères extraits. La page PDF 198 a été rendue et inspectée : deux colonnes de texte et des encadrés latéraux, page imprimée 196.

La nouvelle extraction utilise **pdfplumber** : mots et coordonnées, découpe géométrique des colonnes, détection des encadrés et extraction des tableaux avec leurs en-têtes et cellules fusionnées. `pdftotext -layout` n’est pas utilisé comme source principale. Chaque passage conserve page PDF, page imprimée, chapitre, section, marqueurs 4x2/4x4/GPL/Hybrid/Diesel/essence, renvois et type de bloc.

Les en-têtes/pieds répétés et numéros isolés sont retirés du corps. Les mots coupés sont recollés, U+2011 devient `-`, et les flèches de renvoi sortent du texte tout en conservant leurs cibles en métadonnées. Les pages de moins de 40 caractères utiles sont ignorées. Les textes sont découpés vers 700 caractères avec chevauchement d’environ 80 ; tableaux, listes et avertissements restent entiers, même plus longs. Les outils ne tronquent pas ces blocs pour les transmettre au modèle.

**Import courant : 8 fichiers Dacia, 11 892 passages actifs, dont 671 bloqués pour contrôle visuel ; 11 221 utilisables.** Les copies Sandero/Stepway 2026 contiennent un manuel commun explicitement identifié pour les deux modèles : huit fichiers, sept contenus PDF distincts. Les 179 851 anciens passages restent archivés. Détail par version et liste des rejets : [docs/DIAGNOSTIC_ASSISTANT.md](docs/DIAGNOSTIC_ASSISTANT.md).

La pagination imprimée vient du pied de page. Le décalage 2 du Bigster est détecté ; Sandero 2021 conserve les références chapitre.page, par exemple PDF 198 → 2.56, sans faux décalage. Trois passages de cette notice n’ont pas de page imprimée détectable : le serveur le précise. Les paragraphes douteux restent bloqués, sauf validation visuelle explicite du bloc exact, liée aux empreintes du fichier et du texte. Deux blocs Bigster des PDF 355/356 ont ainsi été vérifiés ; cela ne valide pas les autres tableaux ou schémas.

La recherche exclut les sommaires et privilégie une consigne d’entretien plutôt que les chapitres d’alerte quand la question ne parle pas d’alerte. Une localisation ou méthode de vérification réellement sourcée est donnée même si une valeur précise manque. Aucun seuil de pertinence ni contrôle des références/valeurs techniques n’est contourné.


## Sources web conservées, hors du chemin de réponse

`config/sources_fiables.json` n’a pas été élargi. Ses pages officielles et la déclaration ManualsLib sont conservées pour traçabilité, mais **aucune recherche web n’est proposée au modèle ni appelée par `/api/chat`**. La commande historique `flask indexer-sources-web` reste un outil d’administration de données, sans effet sur les réponses actuelles. Les variables SEARCH_* restent inutilisées dans le dialogue.

ManualsLib demeure une provenance complémentaire pour des PDF obtenus avec les droits nécessaires et vérifiés par l’équipe, jamais une source aspirée automatiquement. Son import reste soumis au même périmètre Dacia et à la page exacte du document. Les métadonnées et archives existantes sont conservées ; aucun nouveau PDF n’a été téléchargé pour cette évolution. L’ancienne FAQ reste une archive administrable ; seule la nouvelle FAQ générale est utilisée sans véhicule.

## API et sécurité

`POST /api/chat` exige session, JSON et en-tête `X-CSRFToken` de la page connectée :

```json
{"message":"Comment vérifier le niveau d’huile ?","vehicle_id":3,"conversation_id":12}
```

Omettre `conversation_id` commence un échange ; omettre `vehicle_id` sélectionne les conseils généraux. Les identifiants sont des entiers positifs et chaque ressource doit appartenir au compte. Champs supplémentaires refusés. La réponse contient `reply`, `conversation_id`, `source`, `source_line`, `references`, `vehicle`, `status`. `source` vaut `faq`, `manuel`, `aucune` ou `indisponible`. Sans véhicule : `status=generale` et `is_general=true` pour une fiche pertinente, ou `sans_reponse_generale`, `clarification`, `hors_sujet`, `politesse`. Une réponse FAQ ajoute `faq_id` et le `score` de pertinence ; ses références contiennent seulement `source`, `faq_id`, `categorie`, sans modèle, année, manuel ou page. `source_line` est vide pour la FAQ ; les métadonnées de fiche restent internes à l’API et ne sont pas ajoutées au texte. Avec véhicule : `hors_perimetre`, `manuel_absent` ou statuts du dialogue documentaire ; les références conservent page PDF, page imprimée, chapitre, section et version, sans score de recherche. Aucun contenu de passage ou fournisseur n’est exposé. Avec une réponse documentaire, `reply` se termine par la référence vérifiée et `source_line` la conserve aussi pour compatibilité ; le navigateur ne la duplique pas. Les messages restent affichés avec `textContent`. `manual_status` reste retiré.

`GET /api/conversations` et `/api/conversations/<id>/messages` sont privés ; l’historique conserve les sources sans réécrire les anciens messages. `GET /api/vehicle-catalog` fournit les suggestions aux comptes connectés. Un identifiant d’un autre compte renvoie 404. Erreurs : 400 validation/CSRF, 401 session, 413 taille, 415 format ; une erreur distante donne HTTP 200 avec indisponibilité neutre, une erreur d’enregistrement interne annule la transaction et donne 500. Mots de passe hachés, ORM, CSRF, sorties Jinja échappées et messages JavaScript textuels. Le navigateur attend au plus 30 secondes ; après une erreur réseau incertaine, vérifier l’historique avant de renvoyer.

## Tests et évaluation

```bash
python -m pytest -q
flask --app run evaluer-chatbot
# Ou dans Docker :
docker compose exec web python -m pytest -q
docker compose exec web flask evaluer-chatbot
```

L’évaluation garde les **78 formulations, identifiants, catégories et contextes d’origine**. Les attentes sans véhicule ont été adaptées à la FAQ générale ; les anciennes attentes restent archivées dans le JSON. Une fiche attendue est vérifiée pour les sujets couverts et un repli honnête est attendu pour les sujets précis absents. Elle utilise la FAQ générale réelle, un **modèle factice simulant les outils** sur quatre pages de manuel fictif et aucune page web. Les scores FAQ sont enregistrés dans le rapport. Le taux mesure ces comportements, pas la qualité d’un vrai modèle ni la couverture des manuels réels. Aucun crédit API n’est consommé. Les tests documentaires et les contrôles de sécurité restent exécutés ; un test géométrique lit trois pages du PDF local quand il est disponible, sinon il est ignoré.

Le rapport `data/rapport_evaluation.md`, ou l’emplacement choisi par `--rapport chemin.md`, liste chaque comportement, les échecs et les questions orientées vers un mécanicien. Il est exclu de la livraison. Le bilan validé et ses limites sont dans [docs/recette.md](docs/recette.md). Les 20 questions de démonstration sont dans [data/questions_a_poser.md](data/questions_a_poser.md), jamais ajoutées aux réponses des utilisateurs.

Recette HTTP avec CSRF, reconnexion et suppression de son propre compte temporaire :

```bash
python tests/smoke_http.py http://localhost:8000
# --restart vérifie aussi la persistance en recréant cette instance Compose
```

Les tests couvrent fournisseurs, appels natifs factices, refus des arguments/ressources étrangères, absence de clé, sources exactes, compteurs facultatifs, listes Dacia en cascade, POST forgés, archives hors liste, XSS, CRUD, échéances, sessions, deux utilisateurs et conversations, import PDF, erreurs réseau et secrets masqués. Aucune vraie clé n’est utilisée pendant pytest. Le test de cascade exécute le JavaScript sous Node lorsque celui-ci est installé ; il est ignoré sinon, tandis que les choix et validations serveur restent testés. Les tests de régression géométrique utilisent le petit extrait réel fourni ; les autres PDF de recette sont fictifs.

## Déploiement et sauvegarde

Aucun hébergeur ni domaine n’a été fourni. Pour publier : hôte Linux, PostgreSQL persistant, `SECRET_KEY` privée explicite, reverse proxy HTTPS avec certificat et redirection HTTPS, puis `docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build`. Le mode production impose PostgreSQL et active les cookies Secure. Configurer les clés dans l’environnement privé, conserver les volumes, protéger le dossier des manuels et valider les réponses avant exposition publique. Bootstrap est fourni localement, sans CDN.

Sauvegarde PostgreSQL dans un fichier privé et restauration dans une nouvelle base séparée :

```bash
python docker/backup.py backup backups/auto.dump
python docker/backup.py restore backups/auto.dump auto_recette_restore
```

Ne jamais distribuer bases, volumes de secrets ou sauvegardes. Sous SQLite, arrêter l’application et utiliser l’API de sauvegarde SQLite vers un fichier distinct.

## Organisation et livraison

`app/routes/` : contrôles de droits et pages ; `app/services/answer_service.py` : orchestration ; `llm_service.py` : transport ; `document_tools.py` : outils documentaires ; `manual_access.py` : correspondance ; `conversation_context.py` : mémoire bornée ; `general_faq_service.py` : chargement validé de la FAQ générale et adaptation au moteur existant ; autres services : imports et ancienne FAQ archivée. `app/models.py` et `migrations/` décrivent le schéma. `config/` : sources web ; `data/` : FAQ générale active sans véhicule, ancienne FAQ archivée, métadonnées et questions de démonstration ; `tests/` : code, jeu et PDF fictifs générés. Architecture : [docs/conception.md](docs/conception.md).

Depuis le projet source, `python scripts/build_delivery.py` régénère le dossier frère `../livraison/`. La livraison ne contient ni `.env` privé, clé, PDF, base, index web, cache, Git, environnement virtuel, rapport généré ou fichier de recherche non validé. Les membres importent leurs sources et configurent leur propre clé après installation.

### Environnement de recette du 24/10/2026

L’ancien `.venv` pointe vers un Python supprimé. La recette courante a utilisé Python 3.12 dans `.work/venv` (ignoré par Git et Docker). Pour la reproduire sur cette machine : `.work/venv/Scripts/python.exe -m pytest -q`. Pour une nouvelle installation, créer un environnement virtuel avec un Python installé ou utiliser Docker. Les résultats et limites exacts figurent dans `docs/recette.md`.
