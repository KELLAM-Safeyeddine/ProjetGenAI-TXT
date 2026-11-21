# 21 novembre 2026 — diagnostic de démarrage Vercel

Recette réelle après e7d5674 : **accueil et /health 200** ; /ready 503, CSS 404. Les dépendances sont maintenant disponibles. Le paquet conservait app/static dans ses exclusions alors que la promotion CDN n’a pas eu lieu : retrait de cette exclusion et test vérifiant les assets réellement référencés par l’accueil. **31 tests ciblés réussis en 5,47 s**, lint/format conformes. Le fichier opérateur privé n’a pas encore ses connexions Neon/Upstash : initialisation à effectuer après saisie privée par l’utilisateur. Aucune clé lue ou publiée.

Validation locale du correctif : **430 tests réussis en 108,12 s**, dont 30 ciblés hébergement/livraison en 5,43 s. Ruff lint et format conformes sur 145 fichiers. Build exécuté : 48 dépendances déclarées et imports essentiels vérifiés, huit PDF (151 524 804 octets), six ressources statiques. Audit de 216 fichiers Git sans élément interdit ni secret reconnu. Correctif publié sous e7d5674 ; recette distante encore en cours.

Le tableau de bord annonce le build a61c9cc prêt, mais cinq requêtes HTTP (accueil, health, ready et deux CSS) renvoient 500 FUNCTION_INVOCATION_FAILED. Runtime Logs réellement consultés : Flask introuvable lors de l'import de run.py. Correctif du manifeste de dépendances et contrôle d'imports au build ; aucune réussite distante déduite des seuls tests locaux. Résultats du correctif ci-dessous à compléter après exécution.

# 21 novembre 2026 — premier build Vercel et correction de configuration

Journal réel fourni pour e45a4b1 : dépendances installées, huit notices vérifiées, six ressources statiques générées, puis erreur 463,32 Mo contre une limite de 225 Mo. Le message identifie une Install Command personnalisée désactivant l'optimisation. La taille estimée et les tests locaux ne valent donc pas une réussite de déploiement. Correction : installation native via `installCommand: null`, override du tableau de bord à désactiver, dernier commit à reconstruire sans cache. Nouveau résultat distant en attente ; aucun manuel ou composant métier retiré.

# 21 novembre 2026 — préparation Vercel

427 tests locaux réussis en 124,75 s ; Ruff sans erreur et 145 fichiers conformes au format. Les nouveaux tests vérifient les chemins temporaires, le refus d'une configuration locale/SQLite/clé éphémère sur Vercel, le démarrage sans écriture dans le source, et la reprise d'une session et de son historique entre fabriques distinctes avec HTTPS/CSRF. La base utilisée pour ce test est une SQLite temporaire, substituée explicitement par la fixture ; la configuration publique exige toujours PostgreSQL et Redis.

Le build des assets a réellement vérifié les SHA-256 des huit notices (151 524 804 octets) et copié six ressources publiques, sans publier de PDF dans public/. Estimation des archives de dépendances ciblant Linux CPython 3.12 : 327 605 738 octets décompressés, avant adaptateur et bytecode ; la taille finale de fonction doit être vérifiée au build Vercel. Les services Neon/Upstash et l'URL publique ne sont pas encore reliés/testés. Docker Desktop est arrêté : pas de nouvelle recette Linux locale. Le dossier livraison n'a pas été régénéré par cette préparation.

Les campagnes datées ci-dessous décrivent leurs propres états historiques.

# 14 novembre 2026 — recette intégrée après « continue tous »

Cette section décrit l'état actuel. Les campagnes conservées plus bas sont historiques : leurs chiffres, ready=200 sans fournisseur et attente stricte ne décrivent plus le fonctionnement courant.

- **SQLite : 402 réussis en 221,64 s ; PostgreSQL : 402 réussis en 79,66 s**, aucun échec/ignoré. Les PDF réels sont disponibles localement ; les tests de protocole utilisent un transport factice. Migrations PostgreSQL sur une base dédiée : upgrade/check/downgrade base/upgrade/check, codes 0, aucune opération supplémentaire détectée.
- **Livraison : 207 fichiers, huit PDF validés**. Construction et démarrage depuis le dossier frère avec PORT=5012 et projet isolé autohelp-recette-p0. Sans fournisseur : **393 réussis/9 ignorés en 87,93 s** ; avec configuration factice : **393 réussis/9 ignorés en 84,02 s**, aucun appel externe. Les huit tests Git et le contrôle Node passent dans l'environnement de test complet ; ces outils ne sont pas dans le runtime.
- Accueil et /health : **200** ; santé Docker healthy, UID **10001**. Aucun PDF, fichier .env réel ou base sous /app dans l'image. Les huit notices restent sur montage en lecture seule. **/ready=503** sans configuration fournisseur ; **200** avec configuration factice complète et index utilisable. Il s'agit d'un contrôle de configuration, pas d'un appel payant au fournisseur.
- `scripts/smoke_container.py` : import Bigster complet **1 721 passages**, administrateur CLI éphémère, CSRF actif, réponse neutre sans clé, réponse avec **Source** vérifiée via modèle factice ; compte et données liés supprimés. `tests/smoke_http.py --restart` : inscription, véhicule, entretien, question, déconnexion/reconnexion et historique, puis recréation et persistance de la session/des données réussis ; fixture supprimée.
- Navigateur à **390 px** : chat, réponse du manuel fictif, FAQ, retour utile/commentaire, renommage et nouvelle conversation, formulaire modèle/année/version et confidentialité ; clavier fonctionnel, aucune erreur/warning de console ni débordement horizontal mesuré. L'emplacement du sélecteur véhicule n'est pas modifié. La suppression et les droits sont couverts par tests serveur, sans suppression de données privées dans le navigateur.
- **Ruff lint/format : conforme, 137 fichiers Python**. Pip check sans conflit ; audits résolus relancés : **48 runtime et 73 dev, zéro avis connu**. Une réponse PyPI incorrecte a fait échouer un premier audit dev ; relance complète réussie sans exclusion. Git index et paquet audités sans fichier interdit/secret reconnu. La CI est préparée et validée localement, non exécutée sur GitHub faute de publication.
- Protocole : **78/78** sur les questions conservées, FAQ réelle locale et modèle documentaire simulé. Ce résultat ne mesure pas l'exactitude d'un vrai fournisseur.
- Corpus réel : **400 questions, 50 annotations Bigster assistées, 350 attendus à établir, zéro revue humaine signée**. Empreinte inchangée b132b4d0d7dcb412420651e02129a25ee547e5c89f9b8fb049a870e12cdf040f. Comparaison relancée : moteur actif **25/49**, prototype **32/49** pages attendues dans les trois premiers passages, huit gains/une régression ; absence de tarif local **1/1** mesurée séparément. **Prototype non activé, pas de score global de qualité**, génération complète non mesurée. Compléter/revoir les attendus avant adoption.
- Mesure distante unique Groq : **7,344 s**, deux appels de 375/578 ms, **1 740 jetons déclarés**, trois références contrôlées et Source finale. Aucun contenu privé/clé dans le rapport distribué. **OpenAI non configuré, non mesuré**. Les budgets restent configurables ; cet échantillon n'est pas une garantie de latence.
- Cache/charge : **11 892 passages réels**, huit index construits/huit réutilisés, pic processus environ **251 Mio** dans le conteneur ; charge séparée avec modèle/PDF fictifs : **335/335 réponses vérifiées**, 355 requêtes HTTP, zéro erreur, p95 HTTP **39,97 ms**. Détails et limites : PERFORMANCES.md.
- PostgreSQL/Redis/Caddy/sauvegarde : projet de production isolé, HTTPS **local** avec autorité explicitement fournie au client ; accueil, santé, confidentialité/conditions 200 et HSTS présent. Parcours HTTP HTTPS complet conservant CSRF/historique réussi. Sauvegarde/restauration réelle : **onze tables ORM intégralement identiques par empreintes**, schéma, connexion au compte fictif avec CSRF, historique et séquence vérifiés. Aucune donnée réelle copiée, aucune bascule de production. Détails DEPLOIEMENT.md et SAUVEGARDE_POSTGRESQL.md.

Les fonctions indépendantes 10–22 sont implémentées. Restent les attendus/revues du benchmark et la décision sur le prototype, l'essai OpenAI si souhaité/configuré, la publication GitHub, la validation juridique/responsable/conservation, la décision du groupe sur les archives, puis hébergement/domaine et recette publique. Les archives et l'ancien .venv n'ont pas été supprimés. Les secrets, données et rapports de recette restent hors livraison ; les sauvegardes privées initiales sont conservées.

---

# Reprise du 14 novembre 2026 — P1-8, premier lot documentaire

- **370 tests SQLite réussis en 68,18 s** et **370 tests PostgreSQL réussis en 57,63 s**, aucun échec/ignoré. Dix nouveaux cas vérifient unités composées, décimales, bornes de plages, absence séparée du rappel, empreinte du jeu et revue humaine traçable.
- Livraison régénérée (**159 fichiers, huit PDF**) et auditée sans secret, base ni fichier temporaire. Construction et démarrage Docker depuis cette copie réussis, projet isolé autohelp-recette-p0, PORT=5012 ; accueil, /health et /ready **200**. UID **10001**, aucun PDF/.env/base dans l’image. Dans le runtime : **361 réussis, 9 ignorés en 61,37 s** ; les contrôles Git/Node facultatifs passent dans l’environnement complet.
- CLI dans le conteneur : **400 cas, 50 évalués, 350 à annoter**, même empreinte et résultat Bigster que le source. Sans --partiel : **code 1 attendu**, refus explicite du corpus incomplet/non relu par un humain. Aucun fournisseur distant configuré dans la recette et aucun appel distant effectué. Conteneurs de recette arrêtés après vérification, volumes conservés.
- Ruff lint/format et audit Git/livraison réussis ; aucun changement de dépendance depuis l’audit précédent.
- **50 annotations Bigster assistées**, après lecture indépendante des pages complètes et inspection de rendus ciblés ; **350 attendus encore absents**, **aucune revue humaine signée**. Questions, identités et SHA-256 des PDF inchangés ; aucune validation professionnelle revendiquée.
- Mesure sans modèle : **25/49 pages attendues dans le top trois (51,0 %)**. Cas sans information (tarif local) : **1/1 sans passage**, séparé du rappel. **24 échecs** conservés : 16 sans passage, 8 avec d’autres pages. Ces observations ne prouvent pas encore leurs causes ; aucun seuil, réserve visuelle ou classement n’est modifié pour améliorer le score.
- Rapport local `.work/rapport_manuels.md`, jeu SHA-256 **b132b4d0d7dcb412420651e02129a25ee547e5c89f9b8fb049a870e12cdf040f**. Génération, qualité sémantique, citations produites et exactitude numérique d’un vrai fournisseur : **non mesurées**.
- Le CLI distingue relecture assistée et revue humaine : sans --partiel, il refuse un corpus incomplet/non relu par un humain. Aucun nom de relecteur humain inventé. Exemple de trace dans EVALUATION_MANUELS.md.
- Conformément à l’ordre strict demandé, **P1-8 reste non validée et P1-9 à P2-22 restent en attente**. Les réponses applicatives, formulaires, protections et sources autorisées ne changent pas dans cette reprise.

La campagne précédente ci-dessous reste historique ; ses 360 tests et son unique annotation ne décrivent plus le source courant.

---

# Recette finale du 14 novembre 2026 — P0, CI et préparation du benchmark

- **360 tests SQLite réussis en 69,56 s**, **360 PostgreSQL réussis en 55,38 s**, aucun échec/ignoré. Onze tests d'évaluation plus un cas de cohérence des versions s'ajoutent aux 348 précédents ; total réel ci-dessus.
- Livraison/image runtime finale : **351 réussis, 9 facultatifs ignorés en 67,81 s**. Les huit tests Git et le contrôle Node sont réservés à l'image de test/CI ; les deux intégrations PDF locales passent dans le runtime grâce au montage.
- Construction/démarrage depuis livraison refaits sur l'état courant, projet isolé autohelp-recette-p0, PORT=5012. Accueil, /health et /ready : **200**. Image inspectée : UID **10001**, aucun PDF, .env, base .db/.sqlite/.sqlite3 sous /app. Huit notices montées en lecture seule.
- Audit des dépendances résolues : 48 runtime et 73 dev sans avis connu, aucun avis ignoré ; voir AUDIT_DEPENDANCES.md. Ruff lint/format et Actionlint passent. Workflow GitHub non encore exécuté à distance.
- Évaluation historique relancée : **78/78 comportements conformes**, mêmes questions, FAQ réelle et modèle manuel factice ; aucun taux de qualité d'un fournisseur réel revendiqué.
- Nouveau jeu réel : **400 cas, 50 par notice**. Une annotation Bigster relue sur la page PDF rendue 336/imprimée 334 ; recherche retrouvant cette page (**1/1**). **399 cas à annoter**, exclus des scores. Résultat identique via le CLI du source et du conteneur ; génération réelle non mesurée. Aucun score global de couverture/qualité.
- Le CLI refuse la validation du corpus complet sans cinquante annotations vérifiées par manuel ; le mode --partiel explicite ce manque. Contrôles de l'édition SHA-256, absence de substitution, page manquée, refus, valeurs, budget et normalisation testés. La liaison des versions depuis la question originale est partagée avec l'API, sans modification de la règle existante.
- Rapports temporaires et image de revue restent dans .work/ ou /tmp du conteneur, jamais dans la livraison. Guide permanent : EVALUATION_MANUELS.md.
- **Décision de l'équipe : garder l'ordre strict et attendre les annotations.** Recherche hybride et tâches suivantes non entamées. Aucun nettoyage d'archives ni publication distante effectués. La livraison conserve les huit notices autorisées, sans donnée de compte ou configuration privée.

---

# 14 novembre 2026 — P1-7 : CI préparée et équivalents locaux validés

- Workflow GitHub Actions : lint/format Ruff, audit des blobs Git, audit des dépendances dev, construction runtime ; matrice SQLite/PostgreSQL avec comptes et documents factices. Actions checkout/setup-python épinglées à leurs SHA officiels vérifiés. Permissions contents:read, aucun secret nécessaire, délais bornés.
- Actionlint **1.7.12** sur le workflow : code **0**, aucune erreur. Exécution dans un conteneur sans réseau, avec seul le dossier workflows monté en lecture seule.
- `ruff check .` : réussi ; `ruff format --check .` : **93 fichiers conformes**. Imports nettoyés et réexports de fixtures explicités ; aucune modification intentionnelle du comportement métier.
- Après formatage : **348 tests SQLite réussis en 81,12 s**, **348 PostgreSQL en 57,63 s**, zéro ignoré avec les notices locales. Les audits résolus runtime/dev de P0-6 restent sans avis connu ; dépendances inchangées à cette étape.
- Livraison régénérée/auditée : huit notices vérifiées, aucun fichier privé/temporaire. Le workflow sera exécuté à un push/PR après publication par le groupe. Aucun dépôt distant n'est configuré/publié et aucun succès GitHub Actions distant n'est revendiqué.

---

# 14 novembre 2026 — P0-6 : dépendances corrigées

- Audit initial : 14 signalements (12 identifiants uniques) sur Flask, pytest et pypdf. Correctifs épinglés : Flask 3.1.3, pytest 9.0.3, pypdf 6.21.4.
- `pip check` : aucun conflit. Audit résolu `python -m pip_audit -r requirements.txt` : **48 dépendances, aucune vulnérabilité connue**. Audit `requirements-dev.txt` : **73 dépendances, aucune vulnérabilité connue**. Aucun avis ignoré ; JSON temporaires dans .work, non livrés.
- **348 tests réussis en 102,89 s sur SQLite**, puis **348 réussis en 60,99 s sur PostgreSQL**, zéro ignoré. Les extraits réels et PDF fictifs passent avec le parseur corrigé.
- Versions des correctifs vérifiées sur les fiches PyPI officielles le 14 novembre. Un audit sans avis connu à cette date ne garantit pas l'absence de défaut inconnu ni la sécurité future ; le répéter en CI. Aucun audit global des paquets système n'est revendiqué.

---

# 14 novembre 2026 — P0-5 : cookies, sessions, CSP et proxy

- **348 tests réussis en 124,98 s**, aucun échec/ignoré. Dix nouveaux cas couvrent les en-têtes des routes publiques/privées, cookie avec expiration, HttpOnly/SameSite, Secure/HSTS sous HTTPS, configuration remember et confiance proxy activée/désactivée ; chaîne invalide refusée.
- Session permanente bornée à huit heures, sans renouvellement à chaque requête. Cookies remember HttpOnly/SameSite=Lax, Secure en production et durée définie. HSTS uniquement en configuration HTTPS sécurisée. CSP sans unsafe-inline/unsafe-eval, object-src none ajouté.
- ProxyFix désactivé par défaut ; PROXY_HOPS explicite entre zéro et deux. Seuls adresse et protocole sont transférés, jamais l'hôte ou un préfixe fourni par le client. Le réseau doit empêcher tout accès direct contournant les proxys déclarés.
- Navigateur Edge headless réel sur l'instance Docker : accueil, connexion, inscription, tableau de bord, formulaire véhicule et chat, puis question FAQ et viewport mobile 390 px. **Aucune violation CSP**, réponse FAQ reçue, aucun débordement horizontal. Compte temporaire et conversation supprimés par le formulaire CSRF.

---

# 14 novembre 2026 — P0-4 : protections contre les abus

- **338 tests réussis en 102,12 s sur SQLite local**, puis **338 réussis en 73,10 s sur PostgreSQL**, aucun ignoré. Une première campagne PostgreSQL interrompue par le contrôle Redis a été écartée et relancée seule.
- Neuf nouveaux cas : verrouillage/déverrouillage sans attente réelle, compte inconnu, remise à zéro après succès, limite IP connexion, limite inscription, 429 JSON du chat et reprise, séparation de deux comptes, stockage indisponible (503), refus du stockage mémoire en production. Les cas paramétrés et regroupements correspondent au total réel ci-dessus.
- Contrôle Redis réel dans un conteneur isolé : échecs enregistrés par une première application, verrou vu par une seconde, effacement partagé après succès. Compteurs de recette supprimés.
- Flask-Limiter 4.1.1, Redis en Compose sans port hôte, mémoire uniquement pour le développement local. Production : Redis obligatoire, pas de secours mémoire silencieux. Clés de compte/IP pseudonymisées par HMAC ; aucune adresse en clair dans ces clés.
- Limites par défaut : connexion 20/minute/IP, inscription 5/heure/IP, chat 20/minute/compte ; verrou après cinq échecs, quinze minutes. Les tests généraux désactivent les quotas et les tests dédiés les activent explicitement.

---

# 14 novembre 2026 — P0-3 : SQLite et PostgreSQL validés

- Image de test séparée avec Git et Node ; ces outils restent absents de l'image runtime.
- `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from tests` : **329 tests réussis en 67,81 s sur PostgreSQL 17.6**, zéro échec/ignoré.
- `docker compose -f docker-compose.test.yml run --rm --no-deps -e AUTOHELP_TEST_DATABASE_URL= tests` : **329 tests réussis en 74,04 s sur SQLite**, zéro échec/ignoré.
- Migrations PostgreSQL : upgrade, check (aucune différence de schéma), downgrade base réussis, codes 0. La suite vérifie les deux bases sans modification de logique métier.
- PostgreSQL de test : base autohelp_test, réseau isolé, aucun port publié, stockage tmpfs. Authentification trust strictement réservée à ce Compose de recette ; ne jamais l'utiliser en production. La variable AUTOHELP_TEST_DATABASE_URL refuse un nom de base ne finissant pas par _test.
- Les trois nouveaux tests vérifient la sélection et la protection de la base de recette. Les deux intégrations de vrais extraits PDF passent avec le montage local ; en CI sans PDF elles peuvent être ignorées.

---

# 14 novembre 2026 — P0-2 : recette Docker validée

- Source : **326 tests réussis en 115,92 s**, aucun ignoré ; sept contrôles infrastructure/générateur ajoutés.
- Livraison régénérée depuis le source : 146 fichiers, dont huit PDF Dacia validés. Générateur réconcilié avec SQLite/5000, import lecture seule, contrôle des changements locaux contre la sauvegarde ZIP. Aucun fichier inconnu supprimé.
- Construction et démarrage réels : `PORT=5012 docker compose --env-file .env.example -p autohelp-recette-p0 up --build -d`, depuis livraison. Migrations et imports historiques automatiques réussis. Projet et volume de recette distincts.
- Accueil, `/health`, `/ready` : **HTTP 200**, sans clé puis avec configuration Groq factice ; santé Docker `healthy`. Après recréation, attendre le démarrage effectif de Gunicorn avant le contrôle HTTP.
- Image inspectée avec `docker run --rm --entrypoint python autohelp:latest ...` : UID **10001**, aucun PDF, `.env`, `.db`, `.sqlite` ou `.sqlite3` sous /app. Huit PDF présents sur le montage runtime en lecture seule.
- Pytest conteneur sans fournisseur : **317 réussis, 9 ignorés en 77,75 s**. Avec configuration factice : **317 réussis, 9 ignorés en 70,14 s**. Huit tests Git nécessitent Git ; le test JavaScript facultatif nécessite Node. Les deux intégrations PDF locales passent grâce au montage des notices.
- `docker compose exec web python scripts/smoke_container.py` : notice Bigster complète importée (**1721 passages**), création CLI administrateur, CSRF actif, indisponibilité attendue sans clé, réponse manuel avec transport factice et référence serveur vérifiée. Aucun appel distant ; compte et données liés supprimés.
- Parcours HTTP réel `tests/smoke_http.py http://127.0.0.1:5012 --restart`, avec COMPOSE_PROJECT_NAME=autohelp-recette-p0 : inscription, véhicule, entretien, chat, reconnexion et historique réussis ; données et session conservées après recréation. Compte éphémère supprimé.
- Audit du paquet : huit empreintes et signatures PDF vérifiées, texte extractible, aucun fichier privé ou temporaire. Le modèle factice ne mesure pas la qualité d'une réponse réelle ; celle-ci reste à relire humainement.

---

# Recette courante — 14 novembre 2026 : sauvegarde et P0-1

- Sauvegarde complète avant modification : archive privée vérifiée de 24 654 fichiers, y compris un instantané SQLite cohérent (`quick_check : ok`). 3 351 024 963 octets non compressés, archive de 1 645 347 689 octets. Manifeste SHA-256 dans le ZIP et résultat dans `verification.json`, hors du dépôt. Le nettoyage des copies intermédiaires a été refusé par le contrôle automatique ; les originaux et l'archive vérifiée sont conservés.
- **319 tests réussis en 88,33 secondes**, aucun échec ni ignoré. Commande : `.work/venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp <dossier-temporaire-externe>`, Python 3.12, SQLite, `PYTHONDONTWRITEBYTECODE=1`. Les 311 tests métier existants et huit nouveaux cas d'hygiène Git passent.
- Audit du contenu réellement indexé : `python scripts/audit_git.py`, **127 fichiers vérifiés, aucun chemin interdit ni secret reconnu**. Vérification des ajouts forcés de PDF/configuration/base et des secrets restés dans l'index après nettoyage du disque. Ce contrôle par signatures n'est pas une certification d'absence de tout secret imaginable.
- Dépôt local conservé, branche `codex/fiabilisation-autohelp`, premier commit du socle actuel ; pas de publication distante ni de faux historique des anciennes évolutions. `git ls-files` exclut PDF, `.env`, bases, journaux, environnements et vidéo. La configuration d'exemple ne contient aucune valeur.
- Aucune modification du chatbot, du formulaire ou des règles de sécurité. La livraison SQLite/5000 et ses huit PDF restent inchangés à cette étape, selon la décision explicite de l'équipe. Ne pas utiliser l'ancien générateur avant adaptation.
- P0-2 n'est pas déclaré validé : plan d'exécution dans `AMELIORATIONS.md`, contrôles Docker à consigner séparément après exécution réelle. Les résultats d'octobre ci-dessous restent historiques.

---

# Recette précédente — réponses détaillées sans bandeaux, 25 octobre 2026

Cette recette remplace les anciens formats de réponse. Rapport demandé, raison documentée du sélecteur, répartition et limites : [FORMAT_REPONSES.md](FORMAT_REPONSES.md).

- **311 tests réussis en 209,41 s**, zéro échec ou ignoré, commande `.work/venv/Scripts/python.exe -m pytest -q`.
- **106 contrôles ciblés réussis en 13,22 s** après renforcement de la consigne d’arrêt pour une alerte rouge/huile, commande `python -m pytest tests/test_response_format.py tests/test_answer_policy.py -q`.
- **64 nouveaux cas** : chaque fiche de FAQ répond avec le bon contenu détaillé et sa clôture unique ; source documentaire en dernière ligne ; absence de doublon, de libellé et de clôture informative sur le manuel ; risques, hors sujet, présentation de l’historique sans écriture et sélecteur conservé.
- **78/78 comportements conformes** dans `flask evaluer-chatbot --rapport .work/evaluation-format.md`, avec FAQ réelle et modèle manuel factice. Questions et identifiants conservés ; aucun taux de qualité d’un vrai LLM n’est revendiqué.
- Quarante fiches réécrites, zéro nouvelle entrée, de 187 à 209 mots dans `reponse`. Douze catégories, seize risques élevés ; aucun chiffre ou norme technique universels. Aucun doute transformé en prescription ; relecture professionnelle restant à organiser.
- Réponse réelle Bigster avec le fournisseur configuré : 135 mots, trois références vérifiées, source finale, aucun libellé interdit ni phrase informative finale vers un mécanicien. Le contenu reste limité aux extraits disponibles.
- Deux parcours HTTP réels : véhicule/entretien/chat et FAQ/hors sujet, CSRF actif et historique après reconnexion. Comptes de recette supprimés, données préexistantes conservées.
- Sélecteur non déplacé. Raison précédente : demande de le proposer à côté de la question, déplacement consigné le 24 octobre ; aucun commentaire supplémentaire, aucun commit Git (`HEAD` absent, zéro commit). Proposition de conserver cet emplacement ; retour latéral non effectué sans validation.
- Aucun contrôle CSRF, propriété, ORM, échappement, référence ou valeur assoupli. Les actions de sécurité sont dans le contenu, y compris lors d’une indisponibilité ; seuls les bandeaux et formulations génériques sont retirés.
- Livraison régénérée depuis le projet, sans manuel PDF, base, clé ou rapport temporaire. Le fonctionnement Docker n’est pas revérifié ; configuration Compose validée sans moteur. Application source actualisée sur le port 5001 et `/health` en HTTP 200.

---

## Recettes précédentes

# Recette courante — FAQ générale sans véhicule, 24 octobre 2026

Cette évolution annule la désactivation totale de la FAQ : sans véhicule, FAQ générale ; avec véhicule, manuel exact uniquement. Rapport de contenu, répartition et sources : [FAQ_GENERALE.md](FAQ_GENERALE.md). Les recettes précédentes sont conservées plus bas et ne définissent plus le comportement sans véhicule.

- **247 tests réussis en 62,96 s**, aucun échec ni test ignoré : `.work/venv/Scripts/python.exe -m pytest -q`. Sortie locale : `.work/pytest-faq-validation.txt`.
- **26 nouveaux tests de FAQ générale** : essuie-glaces, cinq demandes propres au modèle sans valeur chiffrée, refus hors sujet, cinq dangers avec avertissement, absence de FAQ avec véhicule, seuil et repli, validation des quarante fiches, persistance après reconnexion, sélecteur près de la saisie, refus de références voisines non pertinentes et absence de contamination par un ancien véhicule/historique. Les tests existants d’authentification, de propriété, CSRF, XSS, documents et fournisseurs restent exécutés.
- **78/78 = 100 %** sur `flask --app run evaluer-chatbot --rapport .work/evaluation-faq-generale.md`. Questions, identifiants, catégories et contextes conservés ; attentes sans véhicule actualisées et anciennes valeurs archivées. Identifiant de fiche vérifié pour les sujets couverts. Aucun échec restant sur ce jeu. Les scores de recherche sont détaillés dans le rapport local.
- Limite : le taux inclut des refus/replis corrects ; il ne signifie pas que toutes les questions reçoivent une réponse de fond. La FAQ locale est réelle, mais le parcours manuel utilise quatre pages fictives et un modèle simulé, sans réseau ni crédit API. Aucune nouvelle validation de qualité d’un vrai LLM n’est revendiquée.
- Questions avec véhicule volontairement orientées vers un mécanicien sur le corpus fictif : T072 « La climatisation ne produit plus de froid. » et T073 « Que préparer pour ma visite technique ? ». La FAQ n’est pas utilisée à leur place.
- Quarante fiches, douze catégories ; sept risques faibles, dix-sept moyens, seize élevés. Pas de marques, chiffres, normes techniques, pressions/couples/capacités universels. Les valeurs propres au modèle nécessitent une sélection. Aucune affirmation jugée incertaine ajoutée ; relecture professionnelle des fiches de sécurité à organiser.
- Aucune modification des manuels, de leurs liaisons ou du registre web ; aucun appel web, clé ou manuel injecté dans la FAQ. Les réponses et références restent du texte ; les messages et sources sont conservés après déconnexion/reconnexion.
- Livraison régénérée depuis le projet source, sans PDF, base, clé, index web ou rapport généré. Docker Engine indisponible : aucun `docker compose up --build` ni `/health` Docker n’est présenté comme revérifié pour cette évolution. `docker compose --env-file .env.example config --quiet` a réussi depuis la livraison.
- Le processus local déjà lancé doit être redémarré pour charger le nouveau code. Le redémarrage automatique avait été refusé par le contrôle d’approbation lors de la tentative précédente, sans motif détaillé ; aucune nouvelle tentative de contournement n’a été faite.

---

## Recettes antérieures

# Recette courante — inventaire dynamique Dacia, 24 octobre 2026

Cette recette remplace les périmètres fixes décrits plus bas. Rapport complet : [DIAGNOSTIC_ASSISTANT.md](DIAGNOSTIC_ASSISTANT.md).

- **221 tests réussis en 95,08 s** : `.work/venv/Scripts/python.exe -m pytest -q`.
- **47 PDF trouvés, 8 Dacia identifiés/importés, 39 autres marques rejetées du périmètre et conservées.** 11 892 passages actifs, 671 bloqués, 11 221 utilisables ; 179 851 anciens passages archivés.
- Modèle fictif Lodgy 2020 découvert sans inscription préalable, apparaissant dans le formulaire et accepté côté serveur ; année absente et Renault refusés. PDF non identifiable et dossier portant seulement une année rejetés avec raison. Suppression d’un PDF immédiatement prise en compte ; aucun emprunt à une autre version.
- Pagination imprimée 196/PDF 198 conservée, format chapitre.page Sandero 2021 ajouté (PDF 198 → 2.56). Trois passages de cette notice restent sans pagination imprimée détectée et sont annoncés ainsi.
- Problème réel reproduit avant modification : orientation sans référence pour une question pneus Bigster, malgré une clé valide et des appels fournisseur réussis. Recherche corrigée, blocs de prose des PDF 355/356 vérifiés par rendu et empreintes, contrat de synthèse précisé, faux rejet de l’année du véhicule corrigé sans autoriser des valeurs techniques inventées.
- Même question via HTTP après redémarrage : réponse concrète sourcée, pages imprimées 353/354, avertissement conservé. Navigateur : cascade Sandero 2021/2026 puis Duster 2026 vérifiée ; historique relu, sélection et références visibles ; aucune erreur/alerte JavaScript. Compte temporaire supprimé.
- Deux autres questions réelles : huile Duster 2026 et Sandero 2021 répondue avec leurs propres références ; pagination imprimée Sandero 4.4 / PDF 288 confirmée.
- Évaluation : **78/78 comportements conformes avec modèle factice**, questions inchangées ; ce score ne mesure pas la pertinence d’un vrai modèle.
- Aucun PDF ni secret à livrer, aucun changement de liste web, aucun relais FAQ/web. Docker non relancé (moteur arrêté) ; montage web des PDF toujours en lecture seule et import ponctuel documenté.

---

## Recettes antérieures conservées pour traçabilité

# Complément de recette — formulaire Dacia limité, 24 octobre 2026

- Liste unique `manual_policy.VEHICLES` : Dacia Bigster, Duster, Jogger, Logan, Sandero, Sandero Stepway et Spring 2026, plus Sandero 2021 : **7 modèles / 8 combinaisons**.
- Dacia fixe et listes modèle/année en cascade ; plus de saisie libre ni suggestions du catalogue marocain. Sandero 2021 accepté ; Sandero 2022, Stepway 2021 et Renault Clio 2026 refusés côté serveur en 422, sans écriture.
- Toutes les huit combinaisons sont testées ; correspondance normalisée, liaison documentaire et motorisation/compteur facultatifs conservés. Les véhicules autorisés sans PDF restent enregistrables.
- Anciens véhicules conservés sans correction automatique ; GET de modification accessible, POST soumis à la liste. Commande `flask lister-vehicules-hors-liste` en lecture seule. Chat limité aux véhicules autorisés du compte, anciens signalés séparément sans manuel ; API directe sans remplacement documentaire.
- CSRF, contrôle de propriété et échappement toujours actifs. Test d’injection HTML refusée à la création et affichage échappé d’un ancien nom malveillant.
- **Suite complète : 207 tests réussis en 49,23 secondes**, commande `.work/venv/Scripts/python.exe -m pytest -q`.
- Recette HTTP sur le serveur source relancé : inscription, ajout Bigster, entretien, chat, déconnexion/reconnexion et historique avec CSRF actif réussis ; compte temporaire supprimé. `/health` répond `ok`.
- Le test JavaScript exécute le vrai script sous Node avec des listes DOM simulées : Sandero → 2021/2026, Bigster et Stepway → 2026, ancienne année invalide retirée. Ce test facultatif est ignoré sur un poste sans Node ; les choix et validations serveur restent couverts.

La recette documentaire ci-dessous reste applicable ; ses anciennes mentions de formulaire libre sont remplacées par ce complément.

---

# Recette courante — 24 octobre 2026 : PDF Dacia uniquement

## Périmètre et état réel

Le chatbot et l’import sont limités à huit triplets : Dacia Bigster/Duster/Jogger/Logan/Sandero/Sandero Stepway/Spring 2026, plus Sandero 2021. Les créations et réenregistrements sont désormais limités aux mêmes huit triplets Dacia ; les anciens véhicules hors liste sont conservés. Le manifeste conserve les anciennes entrées désactivées et huit entrées autorisées ; seul Bigster 2026 est prêt à importer. Les autres PDF historiques sont conservés sans activation. Aucun autre modèle ni millésime ne peut servir de remplacement.

**Import réel : 1721 passages actifs, 403 pages PDF représentées, 84 passages bloqués pour contrôle visuel, soit 1637 passages utilisables par la recherche. 189882 anciens passages sont conservés inactifs.**

Seul le triplet **Dacia / Bigster / 2026** possède des passages actifs. Les sept autres renvoient un message nominatif de manuel absent. La migration `f82b650ca410` et l’import conservent les archives sans suppression ; une sauvegarde SQLite préalable est conservée localement dans `.work/backups`.

## Méthode validée

Notice **NU 1626-3 R1310**, 430 pages, PDF non chiffré avec texte extractible. `pdfinfo` a confirmé ces propriétés. `pdffonts` n’est pas disponible sur cet hôte ; les ressources de polices PDF ont été inspectées avec pypdf et les caractères/coordonnées avec pdfplumber. La page PDF 198 a été rendue et examinée : deux colonnes principales, encadrés latéraux séparés, pied de page « 196 - La conduite ».

L’extraction utilise pdfplumber et des bandes géométriques avec gouttières blanches ; elle ne repose pas sur `pdftotext -layout`. En-têtes/pieds et numéros isolés sont retirés du corps ; mots coupés recollés, U+2011 normalisé, renvois retirés du texte et conservés en métadonnées. Découpage des textes vers 700 caractères/80 de chevauchement ; tableaux, listes et avertissements atomiques, sans troncature dans les outils. Les tableaux conservent les en-têtes ; une cellule commune n’est répétée que si sa géométrie confirme la fusion. Aucun OCR.

Chaque passage conserve page PDF, page imprimée (pied de page prioritaire, décalage 2 détecté automatiquement), chapitre/section, type, boîte géométrique, renvois et marqueurs de version. Les variantes incompatibles sont filtrées ; les variantes applicables sont privilégiées selon le message original et la motorisation, fixés côté serveur. Les sources/valeurs inventées restent rejetées. Les avertissements de sécurité sont conservés, y compris en cas de fournisseur indisponible.

## Contrôle visuel restant

Les pages PDF suivantes nécessitent une revue de tableau, d’étiquette ou de schéma :

119, 200, 201, 204, 353, 354, 355, 356, 357, 358, 359, 360, 362, 363, 366, 386, 388, 389.

Le tableau incomplet de la page PDF 119 n’est pas utilisé. Les 84 passages des pages signalées portent `controle_visuel_requis` et sont exclus des réponses, même si leur texte reste consultable dans le lecteur. Les valeurs des schémas/fusibles ou étiquettes non reconnus ne sont pas devinées. Cette version ne fournit pas d’écran de validation : il faut corriger/vérifier l’extraction avant de réintroduire ces informations.

Pages PDF ignorées pour texte utile insuffisant : 1, 2, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 110, 112, 114, 224, 293, 294, 387, 400, 403, 428, 429. Une autre page ne produit aucun bloc utile après retrait du formulaire. Aucune exception d’extraction de page n’a été enregistrée. Ces contrôles automatiques et la vérification de quelques pages ne prouvent pas la fidélité intégrale des 430 pages : relecture humaine nécessaire.

Journal complet local : `instance/manual-import.log`.

## Tests exécutés

- **193 tests passent en 42,07 secondes**, Windows / Python 3.12, commande `.work/venv/Scripts/python.exe -m pytest -q`.
- L’environnement isolé `.work/venv` a été créé car l’ancien `.venv` référence un Python supprimé. Dépendances installées avec les versions épinglées et pdfplumber ; `pip check` sans conflit.
- `flask db check` : aucune différence de schéma après migration sur la base SQLite source.
- Tests réels de géométrie sur deux pages : colonnes non mélangées en page imprimée 196 (PDF 198), pagination, renvoi 353, bloc 4x2 entier, tableau des masses (PDF 405) avec en-têtes 4x2/4x4. Petit extrait JSON de mots/coordonnées/tableau inclus dans `tests/data/bigster_extrait.json` ; aucun PDF complet distribué.
- Test d’intégration supplémentaire sur les pages PDF locales 198/404/405 ; la table numérique des dimensions reste conservée. Ce test est ignoré si le PDF constructeur est absent, comme dans la livraison.
- Tests de séparation Sandero 2021/2026/Stepway, manque de PDF, archivage non destructif, données en attente, mauvais véhicule, arguments de version/page interdits et blocage des pages nécessitant contrôle visuel.
- Tests API avec modèle factice : références serveur « page imprimée 196 (PDF 198), chapitre La conduite » ; propriété, comptes, conversations et historique conservés.
- Parcours HTTP réel avec CSRF : inscription, Bigster, entretien, chat, déconnexion/reconnexion, historique ; compte temporaire supprimé.
- Essai réel avec le fournisseur privé : question sur l’usage tout-terrain du 4x2, réponse issue du manuel et citation page imprimée 196 / PDF 198 / chapitre La conduite / section Versions 4x2.
- Évaluation des 78 formulations inchangées : **78/78 comportements conformes**, modèle factice et corpus réduit. Attentes adaptées à la sélection d’un véhicule et à l’absence de manuel, sans modifier les questions. Ce taux ne mesure pas la pertinence d’un modèle réel.
- Aucun outil web n’est fourni au modèle ni appelé par `/api/chat`. Le registre `config/sources_fiables.json` est identique à la livraison précédente ; aucune source ajoutée.
- Docker non relancé lors de cette recette : moteur Docker Desktop arrêté. Les résultats Docker historiques ci-dessous ne valident pas ce nouvel état.

## Limites et suite

Fournir et valider les sept autres PDF avant de mettre `pret_import: true`, puis relancer `flask import-manuels`. Ne pas se fier à la seule présence des anciens fichiers sur disque. Revoir les 18 pages signalées et un échantillon plus large avant diffusion. Aucun modèle n’accède directement à la base ou au système de fichiers ; la FAQ et le web ne participent plus aux réponses.

---

## Recettes antérieures — conservées pour traçabilité, remplacées par le périmètre ci-dessus

# Recette AutoHELP — 18 octobre 2026

Ce bilan remplace les recettes des anciennes priorités manuel/Groq/FAQ et du formulaire limité au catalogue.

## Résultats et portée

- **178 tests passent sous Windows/Python 3.14 en 123,07 s ; 178 passent dans Docker/Python 3.13 en 39,38 s.**
- `flask evaluer-chatbot` : 78/78 comportements conformes avec modèle factice simulant les appels natifs et quatre pages de manuel fictif, sans page web et sans FAQ.
- Ce taux de 100 % mesure le protocole, les références et l’honnêteté sur un corpus réduit ; il ne mesure pas la pertinence d’un vrai modèle. Les 78 questions et contextes d’origine sont inchangés ; les attentes sont adaptées au contrat sans FAQ.
- Tests réels de génération effectués avec le fournisseur privé configuré : réponse NARSA avec URL/date et réponse du manuel Dacia Bigster 2026, pages 336/339, sur le niveau d’huile.
- Les essais réels ont révélé des sorties non conformes : appels natifs mal suivis et procédures complétées de mémoire. Les phases de recherche et synthèse ont été séparées, les consignes réduites et les valeurs sans support rejetées. Une sortie rejetée conduit à une orientation, jamais à son affichage brut. Une relecture humaine reste nécessaire.
- Migration `e41ac907d256` appliquée sur SQLite et PostgreSQL ; `flask db check` sans différence sur les deux moteurs. `pip check` sans conflit. Aucun PDF constructeur ni vraie clé dans les tests.

## Recettes HTTP et Docker

Le parcours HTTP source avec CSRF actif passe : inscription, véhicule, entretien, chat, déconnexion/reconnexion et historique, puis suppression du compte temporaire. Une seconde recette réelle vérifie la saisie Lexus facultative, la liaison normalisée `DÁ CIA / BIG STER / 2026` vers Dacia Bigster, une réponse sourcée du manuel puis un changement vers Lexus sans reprise du manuel précédent. Les comptes et données de recette sont supprimés.

Depuis la livraison seule, `docker compose up --build` démarre PostgreSQL et Gunicorn ; `/health` répond sans clé, puis avec clé factice et URL factice, sans appel externe. Le port 8002 est utilisé pour la recette car 8000 sert à un autre projet. Le script HTTP déduit le port à conserver lors de `--restart` depuis l’adresse testée. Le template `.env` est copié pour la recette, puis retiré de la livraison finale. La livraison ne conserve que `.env.example` vide. Le redémarrage réel web + db conserve les données, la session et l’historique ; le compte temporaire est ensuite supprimé. L’évaluation dans le conteneur confirme 78/78 comportements conformes. Le serveur source reste disponible sur le port 5001.

## État des sources locales

47 versions de manuels indexées, 191 558 passages ; 43 PDF distincts par empreinte, conservés uniquement dans le projet source. Les 66 versions du catalogue ont leur état documenté dans `data/manual_sources.json` et `docs/acquisition_manuels.md`. Les PDF anglais restent signalés. La livraison part sans PDF et sans passages.

10 pages autorisées vérifiées le 17/10/2026 ; 9 pages/78 passages importés sur la source. ADEME non indexée : autorisation robots non validée. Liste exacte : [SOURCES_WEB.md](SOURCES_WEB.md). Aucune date d’indexation n’est remplacée par une fausse date récente.

Véhicules personnels enregistrés sans manuel correspondant, audit du 18/10/2026 (aucune identité de compte exposée) : Renault Clio 2020 et Volkswagen Golf 8 2026. Les nouveaux véhicules libres restent enregistrables sans manuel.

## Questions orientées vers un mécanicien dans le jeu réduit

51 questions attendent cette orientation, parce que leurs informations ne sont pas dans les quatre pages fictives et qu’aucun index web n’est injecté. Cela ne constitue pas une mesure de couverture des manuels réels.

- T001 : Je ne roule presque pas, faut-il quand même remplacer le lubrifiant ?
- T002 : Le garage me propose une autre homologation huile, est-ce équivalent ?
- T003 : Je souhaite contrôler la jauge sans faire de bêtise.
- T004 : Rajouter du lubrifiant suffit pour éviter une révision ?
- T005 : Après ma vidange une flaque grasse apparaît sous le moteur.
- T006 : Bghit ndir vidanj dyal tomobil, imta ?
- T007 : Comment déterminer le gonflage adapté aux bagages ?
- T008 : Un flanc de ma roue présente une bosse.
- T009 : Le dessin des roues est usé uniquement sur un bord.
- T010 : Que faire quand une roue se dégonfle à répétition ?
- T011 : Peut-on mesurer les pneumatiques juste après autoroute ?
- T012 : Ça siffle dès que j’appuie sur le frin.
- T013 : La pédale s’enfonce beaucoup et reste spongieuse.
- T014 : Ma tomobil tire à droite lorsque je freine.
- T015 : Comment reconnaître des garnitures de frein fatiguées ?
- T016 : Le moteur tourne péniblement au lancement.
- T017 : Mon accu se retrouve vide après chaque nuit.
- T018 : J’ai laissé les phares toute la nuit et elle ne démarre plus.
- T019 : Les bornes de mon accumulateur sont blanchâtres.
- T020 : Comment faire tester le circuit qui recharge la batterie ?
- T021 : La burette rouge s’allume en roulant, je continue ?
- T022 : Un dessin moteur orange clignote et ça broute.
- T023 : Le pictogramme de coussin gonflable ne s’éteint pas.
- T024 : Le voyant de charge reste allumé après démarrage.
- T025 : Le témoin antipatinage clignote sur route glissante.
- T026 : Un clac apparaît à chaque passage sur un dos d’âne.
- T027 : Une vibration se produit seulement quand je freine.
- T028 : Un ronronnement augmente quand la vitesse monte.
- T029 : J’entends un couinement au lancement du moteur.
- T030 : L’air souffle mais reste tiède quand j’active la clim.
- T031 : Une odeur de moisi sort des aérateurs.
- T032 : Une petite flaque d’eau claire se forme après la clim.
- T033 : Est-ce utile de recharger le gaz tous les étés ?
- T034 : Un des feux de croisement ne s’allume plus.
- T035 : Puis-je mettre une ampoule LED dans mon vieux phare ?
- T036 : Mes optiques deviennent jaunes et éclairent mal.
- T037 : Quels papiers préparer pour la visite technique au Maroc ?
- T038 : La responsabilité civile couvre-t-elle ma propre voiture ?
- T039 : Je vends ma voiture, quelle démarche officielle pour changer le propriétaire ?
- T040 : J’ai perdu mon certificat d’immatriculation marocain.
- T041 : Je roule souvent sur des pistes poussiéreuses, que surveiller sur le filtre moteur ?
- T042 : Un filtre de ventilation sale peut-il réduire le débit d’air ?
- T043 : Peut-on dévisser le vase d’expansion quand le moteur est brûlant ?
- T044 : Le niveau de liquide baisse régulièrement sans explication.
- T045 : Comment comparer deux devis d’entretien en dirhams sans tarif arbitraire ?
- T046 : Je consomme plus depuis que mes trajets sont très courts.
- T072 : La climatisation ne produit plus de froid.
- T073 : Que préparer pour ma visite technique ?
- T076 : À quelle fréquence faire la vidange ?
- T077 : Que faire si les pneus perdent de l’air ?
- T078 : Mes freins grincent en roulant.

## Limites restantes

Le seuil documentaire conservateur peut manquer une formulation. Les tableaux PDF, variantes de motorisation et éditions de marché exigent une vérification humaine. L’index web est limité aux pages exactes, sans recherche libre ni moteur externe configuré. Pas de déploiement HTTPS public faute d’hébergement. Valider la liste des pages et relire un échantillon de réponses avant diffusion.

## Recette de l’ajout ManualsLib

178 tests passent sur les deux plateformes après cet ajout ; évaluation inchangée à 78/78 comportements simulés. Les nouveaux tests vérifient l’import d’un PDF fictif avec provenance ManualsLib et citation de page/section/URL, le refus d’une provenance de portail, l’absence complète de requête réseau vers la source manuelle et la purge/exclusion des pages HTML en cache. La livraison a été reconstruite et `/health` vérifié. Aucun nouveau PDF réel téléchargé ; 47 versions de manuels restent indexées sur la source. ManualsLib figure dans le registre avec accès automatisé désactivé conformément aux conditions consultées le 18/10/2026.
