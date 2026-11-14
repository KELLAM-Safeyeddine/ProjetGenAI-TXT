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
